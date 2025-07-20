import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import re

# ---------- Fungsi Login & Registrasi ----------

def cek_admin():
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    return len([u for u in users if u['role'] == 'admin']) > 0


def registrasi_admin():
    st.header("🔐 Registrasi Admin Pertama")
    username = st.text_input("Buat Username Admin")
    password = st.text_input("Buat Password", type="password")
    konfirmasi = st.text_input("Konfirmasi Password", type="password")

    if st.button("Daftar Admin"):
        if not username or not password or not konfirmasi:
            st.warning("Semua field wajib diisi.")
        elif password != konfirmasi:
            st.error("Password tidak cocok.")
        else:
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_ws = connect_gsheet().worksheet("User")
            user_ws.append_row([username, hashed, "admin", "", "", "", str(datetime.now()), ""])
            st.success("Admin berhasil dibuat. Silakan login.")
            st.rerun()


def login(username, password):
    sheet = connect_gsheet().worksheet("User")
    users = sheet.get_all_records()
    for u in users:
        if u['username'] == username:
            if bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
                return u['role']
    return None

# ---------- Fitur Admin ----------

def kelola_kamar():
    st.subheader("➕ Tambah Kamar Baru")

    nama = st.text_input("Nama Kamar Baru")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg", "jpeg", "png"])

    if st.button("Tambah Kamar"):
        if not nama:
            st.warning("Nama kamar wajib diisi.")
            return

        safe_nama = re.sub(r'[^a-zA-Z0-9_\-]', '_', nama)
        link_foto = ""

        if foto:
            try:
                link_foto = upload_to_cloudinary(foto, f"{safe_nama}.jpg")
            except Exception as e:
                st.error(f"Gagal upload foto: {e}")
                return

        kamar_ws = connect_gsheet().worksheet("Kamar")
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link_foto])
        st.success("Kamar berhasil ditambahkan.")
        st.rerun()

    st.markdown("---")
    st.subheader("🏠 Kelola Data Kamar")

    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()

    for idx, k in enumerate(data):
        label = f"**{k['Nama']}** - Rp{k['Harga']}"
        with st.expander(label):
            st.write(f"**Status:** {k['Status']}")
            st.text(k['Deskripsi'])
            if k['Link Foto']:
                st.image(k['Link Foto'], width=300)
            if st.button(f"Hapus {k['Nama']}", key=f"hapus_{idx}"):
                kamar_ws.delete_rows(idx + 2)
                st.success(f"Kamar {k['Nama']} dihapus.")
                st.rerun()


def verifikasi_booking():
    st.subheader("📄 Verifikasi Booking")
    sheet = connect_gsheet()
    booking_ws = sheet.worksheet("Booking")
    user_ws = sheet.worksheet("User")
    kamar_ws = sheet.worksheet("Kamar")

    data = booking_ws.get_all_records()
    kamar_data = kamar_ws.get_all_records()

    for idx, b in enumerate(data):
        st.write(f"**{b['nama']}** mengajukan kamar **{b['kamar_dipilih']}**")
        st.write(f"Kontak: {b['no_hp_email']}")

        if st.button(f"Setujui {b['nama']}", key=f"setuju{idx}"):
            password = "12345678"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            user_ws.append_row([b['nama'], hashed, "penyewa", b['kamar_dipilih'], b['no_hp_email'], "", str(datetime.now()), "Belum"])

            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i + 2, 2, "Terisi")

            booking_ws.delete_rows(idx + 2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.rerun()


def manajemen_penyewa():
    st.subheader("👥 Manajemen Penyewa")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    penyewa = [u for u in users if u['role'] == 'penyewa']

    for idx, u in enumerate(penyewa):
        label = f"{u['username']} ({u['kamar']})"
        with st.expander(label):
            st.write(f"**Nomor Kontak:** {u['kontak']}")
            st.write(f"**Status Pembayaran:** {u.get('Status Pembayaran', 'Belum diatur')}")

            new_kamar = st.text_input(f"Edit Kamar {u['username']}", value=u['kamar'], key=f"kamar_{idx}")
            new_kontak = st.text_input(f"Edit Kontak {u['username']}", value=u['kontak'], key=f"kontak_{idx}")
            new_status = st.selectbox(f"Status Pembayaran {u['username']}", ["Lunas", "Belum"], index=0 if u.get('Status Pembayaran', '') == 'Lunas' else 1, key=f"status_{idx}")

            if st.button(f"Simpan Perubahan {u['username']}", key=f"simpan_{idx}"):
                user_ws.update(f"D{idx+2}", [[new_kamar]])
                user_ws.update(f"E{idx+2}", [[new_kontak]])
                user_ws.update(f"H{idx+2}", [[new_status]])
                st.success("Data penyewa berhasil diperbarui.")
                st.rerun()


# ---------- Fitur Penyewa ----------

def fitur_penyewa(username):
    st.header(f"Selamat Datang, {username}")

    menu = st.sidebar.selectbox("Menu Penyewa", ["Upload Pembayaran", "Komplain", "Manajemen Akun"])
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    u = next(u for u in users if u['username'] == username)

    if menu == "Upload Pembayaran":
        bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
        bulan = st.selectbox("Pilih Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        tahun = st.text_input("Tulis Tahun", value=str(datetime.now().year))
        if st.button("Kirim Bukti"):
            link = upload_to_cloudinary(bukti, f"Bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
            bayar_ws = connect_gsheet().worksheet("Pembayaran")
            bayar_ws.append_row([username, link, f"{bulan} {tahun}", str(datetime.now())])
            st.success("Bukti pembayaran berhasil dikirim.")

    if menu == "Komplain":
        isi = st.text_area("Tulis Komplain Anda")
        foto = st.file_uploader("Bukti Foto (Opsional)", type=["jpg", "jpeg", "png"])
        if st.button("Kirim Komplain"):
            link_foto = upload_to_cloudinary(foto, f"Komplain_{username}_{datetime.now().strftime('%Y%m%d%H%M')}") if foto else ""
            komplain_ws = connect_gsheet().worksheet("Komplain")
            komplain_ws.append_row([username, isi, link_foto, str(datetime.now())])
            st.success("Komplain berhasil dikirim.")

    if menu == "Manajemen Akun":
        st.subheader("🔧 Edit Akun Sendiri")
        last_edit = datetime.strptime(u['last_edit'], "%Y-%m-%d %H:%M:%S")
        can_edit = datetime.now() - last_edit > timedelta(days=7)
        if can_edit:
            new_nama = st.text_input("Nama Lengkap", value=u['username'])
            new_kontak = st.text_input("Nomor HP / Email", value=u['kontak'])
            foto = st.file_uploader("Ganti Foto Profil", type=["jpg", "jpeg", "png"])
            new_pw = st.text_input("Password Baru (opsional)", type="password")

            if st.button("Simpan Perubahan"):
                user_ws.update(f"A{users.index(u)+2}", [[new_nama]])
                user_ws.update(f"E{users.index(u)+2}", [[new_kontak]])
                user_ws.update(f"G{users.index(u)+2}", [[datetime.now().strftime('%Y-%m-%d %H:%M:%S')]])
                if foto:
                    link = upload_to_cloudinary(foto, f"Profil_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
                    user_ws.update(f"F{users.index(u)+2}", [[link]])
                if new_pw:
                    hashed = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
                    user_ws.update(f"B{users.index(u)+2}", [[hashed]])
                st.success("Data akun berhasil diperbarui.")
                st.rerun()
        else:
            st.warning("Perubahan akun hanya bisa dilakukan seminggu sekali.")

# ---------- Session State Handling ----------

st.set_page_config(page_title="Dashboard Kost123", layout="wide")
st.title("📊 Dashboard Kost123")

if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""

# ---------- Main App ----------

if not cek_admin():
    registrasi_admin()
else:
    if not st.session_state.login_status:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            role = login(username, password)
            if role:
                st.session_state.login_status = True
                st.session_state.role = role
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Username atau Password salah.")
    else:
        st.sidebar.success(f"Login sebagai {st.session_state.role.capitalize()}")

        if st.session_state.role == "admin":
            menu = st.sidebar.selectbox("Menu Admin", ["Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa", "Manajemen Akun"])
            if menu == "Kelola Kamar":
                kelola_kamar()
            elif menu == "Verifikasi Booking":
                verifikasi_booking()
            elif menu == "Manajemen Penyewa":
                manajemen_penyewa()
            elif menu == "Manajemen Akun":
                fitur_penyewa(st.session_state.username)
        elif st.session_state.role == "penyewa":
            fitur_penyewa(st.session_state.username)

        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.role = None
            st.session_state.username = ""
            st.rerun()
