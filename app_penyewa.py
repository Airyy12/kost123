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

def show_dashboard():
    st.title("📊 Dashboard Penyewa")
    sheet = connect_gsheet()
    user_ws = sheet.worksheet("User")
    kamar_ws = sheet.worksheet("Kamar")
    pembayaran_ws = sheet.worksheet("Pembayaran")
    komplain_ws = sheet.worksheet("Komplain")

    users = pd.DataFrame(user_ws.get_all_records())
    user_data = users[users['username'] == USERNAME].iloc[0]

    kamar_data = pd.DataFrame(kamar_ws.get_all_records())
    kamar = kamar_data[kamar_data['Nama'] == user_data['kamar']].iloc[0] if user_data['kamar'] else {}

    pembayaran_data = pd.DataFrame(pembayaran_ws.get_all_records())
    user_pembayaran = pembayaran_data[pembayaran_data['username'] == USERNAME].sort_values(by='waktu', ascending=False)

    komplain_data = pd.DataFrame(komplain_ws.get_all_records())
    user_komplain = komplain_data[komplain_data['username'] == USERNAME]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 👤 {user_data['nama_lengkap']}")
        st.image(user_data['foto_profil'], width=150)
        st.markdown(f"📱 {user_data['no_hp']}")
        st.markdown(f"📝 {user_data['deskripsi']}")

    with col2:
        st.markdown(f"### 🏠 Kamar: {user_data['kamar']}")
        if kamar:
            st.markdown(f"**Status**: {kamar['Status']}  ")
            st.markdown(f"**Harga**: Rp {kamar['Harga']:,}")
            st.markdown(f"**Deskripsi**: {kamar['Deskripsi']}")
            st.image(kamar['link_foto'], width=200)

    st.markdown("---")
    st.markdown(f"### 💸 Status Pembayaran Terbaru")
    if not user_pembayaran.empty:
        latest = user_pembayaran.iloc[0]
        st.markdown(f"- Bulan: {latest['bulan']} {latest['tahun']}")
        st.markdown(f"- Nominal: Rp {latest['nominal']:,}")
        st.markdown(f"- Status: **{latest['status']}**")
        st.image(latest['bukti'], width=300)
    else:
        st.info("Belum ada pembayaran yang tercatat.")

    st.markdown("---")
    st.markdown(f"### 📢 Komplain Terkirim: {len(user_komplain)} item")


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
