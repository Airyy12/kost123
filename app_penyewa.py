import streamlit as st
from datetime import datetime, timedelta
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
import bcrypt

def run_penyewa():
    st.sidebar.title("Penyewa Panel")
    menu = st.sidebar.radio("Menu", ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"])

    if menu == "Dashboard":
        penyewa_dashboard()
    elif menu == "Pembayaran":
        pembayaran()
    elif menu == "Komplain":
        komplain()
    elif menu == "Profil Saya":
        profil_saya()
    elif menu == "Logout":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

def penyewa_dashboard():
    st.title("Dashboard Penyewa")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    user_data = next(u for u in users if u['username']==st.session_state.username)

    col1, col2 = st.columns([1,3])

    with col1:
        if user_data.get('foto_profil'):
            st.image(user_data['foto_profil'], width=100, caption="Foto Profil")

    with col2:
        st.markdown(f"""
        ### Selamat Datang, {user_data.get('nama_lengkap', user_data['username'])}
        {user_data.get('deskripsi', 'Belum ada deskripsi.')}
        """)

    st.info(f"Nomor Kamar: {user_data.get('kamar','Belum Terdaftar')}")
    st.info(f"Status Pembayaran: {user_data.get('Status Pembayaran','Belum Ada Data')}")

def pembayaran():
    st.title("💸 Pembayaran Kost")

    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    tahun = st.text_input("Tahun", str(datetime.now().year))
    nominal = st.number_input("Nominal Pembayaran", min_value=0)
    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","jpeg","png"])

    if st.button("Kirim Bukti"):
        if bukti is not None:
            link = upload_to_cloudinary(bukti, f"Bayar_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}")
            bayar_ws = connect_gsheet().worksheet("Pembayaran")
            bayar_ws.append_row([st.session_state.username, bulan, tahun, nominal, link, str(datetime.now())])
            st.success("Bukti pembayaran berhasil dikirim.")
        else:
            st.warning("Silakan upload bukti transfer terlebih dahulu.")

def komplain():
    st.title("📢 Komplain")

    isi = st.text_area("Tulis Komplain Anda")
    bukti = st.file_uploader("Upload Foto (Opsional)", type=["jpg","jpeg","png"])

    if st.button("Kirim Komplain"):
        link = upload_to_cloudinary(bukti, f"Komplain_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}") if bukti else ""
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_ws.append_row([st.session_state.username, isi, link, str(datetime.now())])
        st.success("Komplain berhasil dikirim.")

def profil_saya():
    st.title("👤 Profil Saya")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = next(i for i,u in enumerate(users) if u['username']==st.session_state.username)
    user_data = users[idx]

    st.write(f"Nama Lengkap : {user_data.get('nama_lengkap','')}")
    st.write(f"Nomor HP / Email : {user_data.get('no_hp','')}")
    st.write(f"Kamar : {user_data.get('kamar','-')}")
    st.write(f"Deskripsi : {user_data.get('deskripsi','')}")

    if user_data.get('foto_profil'):
        st.image(user_data['foto_profil'], width=150)

    if st.button("Edit Profil"):
        st.session_state['submenu'] = 'edit_profil'

    if st.session_state.get('submenu') == 'edit_profil':
        st.subheader("Edit Profil")
        last_edit_str = user_data.get('last_edit', '')
        can_edit = True

        if last_edit_str:
            last_edit = datetime.strptime(last_edit_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() - last_edit < timedelta(days=7):
                can_edit = False

        if can_edit:
            nama = st.text_input("Nama Lengkap", value=user_data.get('nama_lengkap',''))
            kontak = st.text_input("Nomor HP / Email", value=user_data.get('no_hp',''))
            deskripsi = st.text_area("Deskripsi Diri", value=user_data.get('deskripsi',''))
            foto = st.file_uploader("Foto Profil", type=["jpg","jpeg","png"])
            new_password = st.text_input("Ganti Password (Opsional)", type="password")

            if st.button("Simpan Perubahan"):
                link = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}") if foto else user_data.get('foto_profil','')
                user_ws.update_cell(idx+2, 4, nama)
                user_ws.update_cell(idx+2, 5, f"'{kontak}")
                user_ws.update_cell(idx+2, 6, deskripsi)
                user_ws.update_cell(idx+2, 7, link)
                user_ws.update_cell(idx+2, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if new_password:
                    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    user_ws.update_cell(idx+2, 2, hashed)
                st.success("Profil berhasil diperbarui.")
                st.session_state['submenu'] = None
        else:
            st.warning("Edit profil hanya bisa dilakukan 1x dalam seminggu.")
