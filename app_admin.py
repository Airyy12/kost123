import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
import calendar
import re

# ---------- Fungsi Utilitas ----------
def get_current_month():
    return datetime.now().strftime('%B')

def get_current_year():
    return datetime.now().year

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
            user_ws.append_row([username, hashed, "admin", "", "", "", "Belum Lunas"])
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

    # ---------- Daftar Kamar ----------
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
            user_ws.append_row([b['nama'], hashed, "penyewa", b['kamar_dipilih'], b['no_hp_email'], password, "Belum Lunas"])

            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")

            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.rerun()

def manajemen_penyewa():
    st.subheader("👥 Manajemen Penyewa")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    for idx, u in enumerate(users):
        if u['role'] == 'penyewa':
            label = f"{u['username']} ({u['kamar']})"
            with st.expander(label):
                st.write(f"**Kontak:** {u['kontak']}")
                st.write(f"**Password:** {u['password_default']}")
                st.write(f"**Status Pembayaran Bulan Ini:** {u['Status Pembayaran']}")

                new_status = st.selectbox("Update Status Pembayaran", ["Lunas", "Belum Lunas"], index=0 if u['Status Pembayaran'] == "Lunas" else 1, key=f"status_{idx}")
                new_kontak = st.text_input("Update Kontak", value=u['kontak'], key=f"kontak_{idx}")

                if st.button(f"Simpan Perubahan {u['username']}", key=f"simpan_{idx}"):
                    user_ws.update(f"E{idx+2}", [[new_kontak]])
                    user_ws.update(f"G{idx+2}", [[new_status]])
                    st.success("Data berhasil diperbarui.")

# ---------- Fitur Penyewa ----------
def fitur_penyewa(username):
    st.header(f"Selamat Datang, {username}")

    menu = st.sidebar.selectbox("Menu Penyewa", ["Upload Pembayaran", "Komplain", "Cek Status Pembayaran"])

    if menu == "Upload Pembayaran":
        bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
        bulan = st.text_input("Bulan & Tahun Pembayaran (Contoh: Juli 2025)")
        if st.button("Kirim Bukti"):
            if not bulan:
                st.warning("Mohon isi keterangan bulan/tahun pembayaran.")
            else:
                link = upload_to_cloudinary(bukti, f"Bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
                bayar_ws = connect_gsheet().worksheet("Pembayaran")
                bayar_ws.append_row([username, link, bulan, str(datetime.now())])
                st.success("Bukti pembayaran berhasil dikirim.")

    if menu == "Komplain":
        isi = st.text_area("Tulis Komplain Anda")
        if st.button("Kirim Komplain"):
            komplain_ws = connect_gsheet().worksheet("Komplain")
            komplain_ws.append_row([username, isi, str(datetime.now())])
            st.success("Komplain berhasil dikirim.")

    if menu == "Cek Status Pembayaran":
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        for u in users:
            if u['username'] == username:
                st.write(f"**Kamar:** {u['kamar']}")
                st.write(f"**Status Pembayaran Bulan Ini:** {u['Status Pembayaran']}")

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
            menu = st.sidebar.selectbox("Menu Admin", ["Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa"])
            if menu == "Kelola Kamar":
                kelola_kamar()
            elif menu == "Verifikasi Booking":
                verifikasi_booking()
            elif menu == "Manajemen Penyewa":
                manajemen_penyewa()

        elif st.session_state.role == "penyewa":
            fitur_penyewa(st.session_state.username)

        if st.sidebar.button("Logout"):
            st.session_state.login_status = False
            st.session_state.role = None
            st.session_state.username = ""
            st.rerun()
