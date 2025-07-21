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
    st.markdown("<h1 style='text-align: center;'>👋 Selamat datang, {}</h1>".format(
        st.session_state.get("nama", "Penyewa")), unsafe_allow_html=True)
    st.write("---")

    # Ambil data dari Google Sheets
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    # Ambil username saat ini
    username = st.session_state.get("username", "")
    user_data = user_df[user_df["username"] == username].iloc[0]

    # --- PROFIL
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 👤 Profil Penyewa")
            st.image(user_data["foto_profil"], width=100)
            st.write(f"**Nama:** {user_data['nama_lengkap']}")
            st.write(f"**No HP:** {user_data['no_hp']}")
            st.write(f"**Username:** {user_data['username']}")
            st.write(f"**Kamar:** {user_data['kamar']}")
            st.write(f"**Deskripsi:** {user_data['deskripsi']}")
            st.write(f"**Terakhir Edit:** {user_data['last_edit']}")

        # --- INFO KAMAR
        with col2:
            st.markdown("### 🛏️ Info Kamar")
            kamar_data = kamar_df[kamar_df["Nama"] == user_data["kamar"]].iloc[0]
            st.image(kamar_data["link_foto"], use_column_width=True)
            st.write(f"**Nama Kamar:** {kamar_data['Nama']}")
            st.write(f"**Status:** {kamar_data['Status']}")
            st.write(f"**Harga:** Rp{int(kamar_data['Harga']):,}")
            st.write(f"**Deskripsi:** {kamar_data['Deskripsi']}")

    st.write("---")

    with st.container():
        col3, col4 = st.columns(2)

        # --- RIWAYAT KOMPLAIN
        with col3:
            st.markdown("### 💬 Riwayat Komplain")
            komplain_user = komplain_df[komplain_df["username"] == username]
            if not komplain_user.empty:
                st.dataframe(komplain_user[["isi_komplain", "waktu", "status"]].sort_values("waktu", ascending=False))
            else:
                st.info("Belum ada komplain.")

        # --- PEMBAYARAN TERAKHIR
        with col4:
            st.markdown("### 💳 Pembayaran Terakhir")
            pembayaran_user = pembayaran_df[pembayaran_df["username"] == username]
            if not pembayaran_user.empty:
                last_payment = pembayaran_user.sort_values("waktu", ascending=False).iloc[0]
                st.write(f"**Bulan:** {last_payment['bulan']}")
                st.write(f"**Tahun:** {last_payment['tahun']}")
                st.write(f"**Nominal:** Rp{int(last_payment['nominal']):,}")
                st.write(f"**Status:** {last_payment['status']}")
                st.image(last_payment["bukti"], caption="Bukti Pembayaran", width=200)
            else:
                st.warning("Belum ada pembayaran.")

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
