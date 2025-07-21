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
    # Ambil data dari Google Sheets
    import pandas as pd
    from sheets import load_sheet_data

    df_user = load_sheet_data("user")
    df_kamar = load_sheet_data("kamar")
    df_pembayaran = load_sheet_data("pembayaran")

    # Cek username login
    username = st.session_state.username
    data_user = df_user[df_user["username"] == username].iloc[0]

    # Ambil data kamar terkait
    kamar = data_user["kamar"]
    data_kamar = df_kamar[df_kamar["Nama"] == kamar].iloc[0]

    # Cari pembayaran terakhir user
    df_pembayaran_user = df_pembayaran[df_pembayaran["username"] == username]
    if not df_pembayaran_user.empty:
        last_row = df_pembayaran_user.sort_values(by="waktu", ascending=False).iloc[0]
        pembayaran_terakhir = {
            "bulan": f"{last_row['bulan']} {last_row['tahun']}",
            "jumlah": last_row["nominal"],
            "tanggal": last_row["waktu"],
            "bukti": last_row["bukti"]
        }
    else:
        pembayaran_terakhir = None

    # Tampilkan UI
    st.markdown("# 👋 Selamat datang, **{}**".format(data_user["nama_lengkap"]))

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📌 Informasi Kamar Anda")
        st.markdown(
            f"""
            <div style="background-color:#222;padding:1.5rem;border-radius:1rem">
                <h3>Kamar {data_kamar['Nama']}</h3>
                <p><strong>Status:</strong> {data_kamar['Status']}</p>
                <p><strong>Harga:</strong> Rp {int(data_kamar['Harga']):,}/bulan</p>
                <p><strong>Deskripsi:</strong> {data_kamar['Deskripsi']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown("### 💳 Riwayat Pembayaran Terakhir")
        if pembayaran_terakhir:
            st.markdown(
                f"""
                <div style="background-color:#222;padding:1.5rem;border-radius:1rem">
                    <h4>{pembayaran_terakhir["bulan"]}</h4>
                    <p><strong>Rp {int(pembayaran_terakhir["jumlah"]):,}</strong></p>
                    <div style="display:flex;justify-content:space-between;margin-top:0.5rem">
                        <small>{pembayaran_terakhir["tanggal"]}</small>
                        <a href="{pembayaran_terakhir["bukti"]}" target="_blank">Lihat Bukti</a>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Belum ada data pembayaran.")

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
