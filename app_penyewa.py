import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

USERNAME = st.session_state.username

def run_penyewa(menu):
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Pembayaran":
        show_pembayaran()
    elif menu == "Komplain":
        show_komplain()
    elif menu == "Profil Saya":
        show_profil()
    elif menu == "Logout":
        st.session_state.login_status = False
        st.session_state.username = ""
        st.session_state.role = None
        st.session_state.menu = None
        st.rerun()
        
import streamlit as st
from sheets import connect_gsheet
from datetime import datetime
import pandas as pd

def show_dashboard():
    st.markdown("<h1 style='text-align: center;'>👋 Selamat datang, {}</h1>".format(st.session_state.nama), unsafe_allow_html=True)

    # Load data dari Google Sheets
    gsheet = connect_gsheet()
    penyewa_df = pd.DataFrame(gsheet.worksheet("penyewa").get_all_records())
    kamar_df = pd.DataFrame(gsheet.worksheet("kamar").get_all_records())
    pembayaran_df = pd.DataFrame(gsheet.worksheet("pembayaran").get_all_records())
    komplain_df = pd.DataFrame(gsheet.worksheet("komplain").get_all_records())

    # Data penyewa saat ini
    current_user = penyewa_df[penyewa_df["nama"] == st.session_state.nama].iloc[0]
    kamar_user = kamar_df[kamar_df["nama_penyewa"] == st.session_state.nama].iloc[0]

    pembayaran_user = pembayaran_df[pembayaran_df["nama"] == st.session_state.nama]
    pembayaran_terakhir = pembayaran_user.sort_values(by="timestamp", ascending=False).head(1)

    komplain_user = komplain_df[komplain_df["nama"] == st.session_state.nama]

    # Layout utama 2x2 grid
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("👤 Profil Penyewa")
        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 12px;'>
            <b>Nama:</b> {current_user['nama']}<br>
            <b>No HP:</b> {current_user['no_hp']}<br>
            <b>Deskripsi:</b> {current_user.get('deskripsi', '—')}<br><br>
            <img src="{current_user['foto_profil']}" width="100" style="border-radius: 10px;"/>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.subheader("🛏️ Info Kamar")
        st.markdown(f"""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 12px;'>
            <b>Nama Kamar:</b> {kamar_user['nama_kamar']}<br>
            <b>Status:</b> {kamar_user['status']}<br>
            <b>Harga:</b> Rp {int(kamar_user['harga']):,}/bulan<br>
            <b>Deskripsi:</b> {kamar_user['deskripsi']}
        </div>
        """, unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("💬 Riwayat Komplain")
        if not komplain_user.empty:
            st.dataframe(komplain_user[["tanggal", "isi", "status"]].sort_values(by="tanggal", ascending=False))
        else:
            st.info("Belum ada komplain yang diajukan.")

    with col4:
        st.subheader("💳 Pembayaran Terakhir")
        if not pembayaran_terakhir.empty:
            row = pembayaran_terakhir.iloc[0]
            bukti_link = f"<a href='{row['bukti']}' target='_blank'>Lihat Bukti</a>" if row["bukti"] else "—"
            st.markdown(f"""
            <div style='background-color: #1e1e1e; padding: 20px; border-radius: 12px;'>
                <b>Bulan:</b> {row['bulan']}<br>
                <b>Jumlah:</b> Rp {int(row['jumlah']):,}<br>
                <b>Tanggal Bayar:</b> {row['timestamp']}<br>
                <b>Bukti:</b> {bukti_link}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Belum ada pembayaran tercatat.")

def show_pembayaran():
    st.title("💸 Pembayaran")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.subheader("Upload Bukti Pembayaran")
    with st.form("form_bayar"):
        bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        tahun = st.selectbox("Tahun", [datetime.now().year - 1, datetime.now().year])
        nominal = st.number_input("Nominal (Rp)", min_value=10000)
        bukti = st.file_uploader("Upload Bukti Pembayaran")
        submit = st.form_submit_button("Kirim")

        if submit and bukti:
            url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}_{datetime.now().isoformat()}")
            ws.append_row([USERNAME, url, bulan, tahun, datetime.now().isoformat(), nominal, "Menunggu Verifikasi"])
            st.success("Bukti pembayaran berhasil dikirim!")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Riwayat Pembayaran Saya")
    if not user_data.empty:
        for i, row in user_data.iterrows():
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} [{row['status']}]"):
                st.image(row['bukti'], width=300)
                if st.button(f"Hapus Pembayaran {i}", key=f"hapus_{i}"):
                    ws.delete_rows(i+2)  # header + index
                    st.success("Dihapus.")
                    st.experimental_rerun()
    else:
        st.info("Belum ada pembayaran.")


def show_komplain():
    st.title("📢 Komplain")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.subheader("Kirim Komplain Baru")
    with st.form("form_komplain"):
        isi = st.text_area("Isi Komplain")
        foto = st.file_uploader("Upload Foto (Opsional)")
        submit = st.form_submit_button("Kirim Komplain")

        if submit and isi:
            url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
            ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
            st.success("Komplain berhasil dikirim!")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Riwayat Komplain Saya")
    if not user_data.empty:
        for i, row in user_data.iterrows():
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(row['isi_komplain'])
                if row['link_foto']:
                    st.image(row['link_foto'], width=300)
                if st.button(f"Hapus Komplain {i}", key=f"hapus_komplain_{i}"):
                    ws.delete_rows(i+2)
                    st.success("Komplain dihapus.")
                    st.experimental_rerun()
    else:
        st.info("Belum ada komplain.")


def show_profil():
    st.title("👤 Profil Saya")
    sheet = connect_gsheet()
    ws = sheet.worksheet("User")
    data = pd.DataFrame(ws.get_all_records())
    idx = data.index[data['username'] == USERNAME].tolist()[0]
    row = data.iloc[idx]

    st.image(row['foto_profil'], width=150)
    st.markdown(f"**Terakhir Edit:** {row['last_edit']}")

    edit_allowed = True
    try:
        last = datetime.fromisoformat(row['last_edit'])
        if datetime.now() - last < timedelta(days=7):
            edit_allowed = False
    except:
        pass

    with st.form("edit_profil"):
        nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
        no_hp = st.text_input("No HP", value=row['no_hp'])
        deskripsi = st.text_area("Deskripsi", value=row['deskripsi'])
        foto = st.file_uploader("Ganti Foto Profil")
        submit = st.form_submit_button("Simpan Perubahan")

        if not edit_allowed:
            st.warning("Profil hanya bisa diedit sekali setiap 7 hari.")
            st.stop()

        if submit:
            url = upload_to_cloudinary(foto, f"foto_profil_{USERNAME}_{datetime.now().isoformat()}") if foto else row['foto_profil']
            ws.update(f"D{idx+2}:G{idx+2}", [[nama, no_hp, deskripsi, url]])
            ws.update_acell(f"I{idx+2}", datetime.now().isoformat())
            st.success("Profil berhasil diperbarui!")
            st.experimental_rerun()
