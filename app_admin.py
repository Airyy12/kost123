import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
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
            user_ws.append_row([username, hashed, "admin"])
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
                try:
                    st.image(k['Link Foto'], width=300)
                except Exception:
                    st.warning("Gagal menampilkan foto.")
            else:
                st.info("Tidak ada foto.")
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
            user_ws.append_row([b['nama'], hashed, "penyewa"])

            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")

            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.rerun()


# ---------- Manajemen Penyewa ----------

def manajemen_penyewa():
    st.subheader("👥 Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    data = user_ws.get_all_records()

    for idx, p in enumerate(data):
        if p['role'] == 'penyewa':
            with st.expander(p['username']):
                st.write(f"**Username:** {p['username']}")
                new_password = st.text_input(f"Password Baru untuk {p['username']}", type="password", key=f"pw_{idx}")
                if st.button(f"Update Password {p['username']}", key=f"update_{idx}"):
                    if new_password:
                        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                        user_ws.update_cell(idx+2, 2, hashed)
                        st.success(f"Password {p['username']} berhasil diubah.")
                        st.rerun()
                    else:
                        st.warning("Password baru tidak boleh kosong.")
                if st.button(f"Hapus Penyewa {p['username']}", key=f"hapus_{idx}"):
                    user_ws.delete_rows(idx+2)
                    st.success(f"Penyewa {p['username']} dihapus.")
                    st.rerun()


# ---------- Session State ----------

st.set_page_config(page_title="Dashboard Kost123", layout="wide")
st.title("📊 Dashboard Kost123")

if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""

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
            menu = st.sidebar.selectbox("Menu Admin", ["Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa"])
            if menu == "Kelola Kamar":
                kelola_kamar()
            elif menu == "Verifikasi Booking":
                verifikasi_booking()
            elif menu == "Manajemen Penyewa":
                manajemen_penyewa()

        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.role = None
            st.session_state.username = ""
            st.rerun()
