import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import calendar
import re

# ---------- Fungsi Utilitas ----------
def get_current_month():
    return datetime.now().strftime('%B')

def get_current_year():
    return datetime.now().year

def can_edit_profile(last_edit):
    if not last_edit:
        return True
    last_time = datetime.strptime(last_edit, "%Y-%m-%d %H:%M:%S")
    return datetime.now() - last_time > timedelta(days=7)

# ---------- Fungsi Cek Kolom ----------
def ensure_status_pembayaran_column():
    user_ws = connect_gsheet().worksheet("User")
    header = user_ws.row_values(1)
    if "Status Pembayaran" not in header:
        user_ws.update_cell(1, len(header)+1, "Status Pembayaran")
        users = user_ws.get_all_records()
        for idx, _ in enumerate(users):
            user_ws.update_cell(idx+2, len(header)+1, "Belum Lunas")
    if "Foto Profil" not in header:
        user_ws.update_cell(1, len(header)+1, "Foto Profil")
    if "Last Edit" not in header:
        user_ws.update_cell(1, len(header)+1, "Last Edit")

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
            user_ws.append_row([username, hashed, "admin", "", "", password, "Belum Lunas", "", ""])
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
            user_ws.append_row([b['nama'], hashed, "penyewa", b['kamar_dipilih'], b['no_hp_email'], password, "Belum Lunas", "", ""])

            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")

            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.rerun()

# ---------- Fitur Manajemen Akun ----------
def manajemen_akun(username, role):
    st.subheader("👤 Manajemen Akun Saya")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    for idx, u in enumerate(users):
        if u['username'] == username:
            foto_profil = u.get('Foto Profil', '')
            last_edit = u.get('Last Edit', '')

            if foto_profil:
                st.image(foto_profil, width=150)

            new_name = st.text_input("Nama Lengkap", value=u['username'])
            new_kontak = st.text_input("Nomor Telepon", value=u['kontak'])
            new_password = st.text_input("Password Baru", type="password")
            foto_baru = st.file_uploader("Upload Foto Profil", type=["jpg", "jpeg", "png"])

            can_edit = role == 'admin' or can_edit_profile(last_edit)

            if st.button("Simpan Perubahan"):
                if not can_edit:
                    st.warning("Anda hanya bisa mengedit akun 1x dalam seminggu.")
                    return
                updates = {
                    f"A{idx+2}": new_name,
                    f"E{idx+2}": new_kontak,
                    f"I{idx+2}": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if new_password:
                    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    updates[f"B{idx+2}"] = hashed
                if foto_baru:
                    link_foto = upload_to_cloudinary(foto_baru, f"FotoProfil_{username}_{datetime.now().strftime('%Y%m%d%H%M')}" )
                    updates[f"H{idx+2}"] = link_foto

                for cell, value in updates.items():
                    user_ws.update(cell, value)
                st.success("Data akun berhasil diperbarui.")
                st.rerun()

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
            menu = st.sidebar.selectbox("Menu Admin", ["Kelola Kamar", "Verifikasi Booking", "Manajemen Akun"])
            if menu == "Kelola Kamar":
                kelola_kamar()
            elif menu == "Verifikasi Booking":
                verifikasi_booking()
            elif menu == "Manajemen Akun":
                manajemen_akun(st.session_state.username, st.session_state.role)

        elif st.session_state.role == "penyewa":
            menu = st.sidebar.selectbox("Menu Penyewa", ["Manajemen Akun", "Upload Pembayaran", "Komplain"])
            if menu == "Manajemen Akun":
                manajemen_akun(st.session_state.username, st.session_state.role)
            elif menu == "Upload Pembayaran":
                fitur_penyewa(st.session_state.username)

        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.role = None
            st.session_state.username = ""
            st.rerun()
