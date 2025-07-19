import streamlit as st
import bcrypt
from sheets import connect_gsheet
from drive import upload_to_drive
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
            st.experimental_rerun()

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
    st.subheader("🏠 Kelola Data Kamar")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()
    for idx, k in enumerate(data):
        col1, col2 = st.columns([3,1])
        with col1:
            st.write(f"**{k['Nama']}** - {k['Status']} - Rp{k['Harga']}")
            st.text(k['Deskripsi'])
        with col2:
            if st.button(f"Hapus {k['Nama']}", key=idx):
                kamar_ws.delete_rows(idx+2)
                st.success(f"Kamar {k['Nama']} dihapus.")
                st.experimental_rerun()

    st.markdown("---")
    st.subheader("➕ Tambah Kamar Baru")
    nama = st.text_input("Nama Kamar Baru")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg","jpeg","png"])
    if st.button("Tambah Kamar"):
        link_foto = upload_to_drive(foto, f"{re.sub(r'[^a-zA-Z0-9_\-]', '_', nama)}.jpg") if foto else ""
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link_foto])
        st.success("Kamar berhasil ditambahkan.")
        st.experimental_rerun()

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
        st.image(b['link_ktp'], width=200)

        if st.button(f"Setujui {b['nama']}", key=f"setuju{idx}"):
            password = "12345678"  # Default password
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_ws.append_row([b['nama'], hashed, "penyewa"])

            # Update status kamar
            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")  # Kolom Status

            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.experimental_rerun()

# ---------- Fitur Penyewa ----------

def fitur_penyewa(username):
    st.header(f"Selamat Datang, {username}")

    menu = st.sidebar.selectbox("Menu Penyewa", ["Upload Pembayaran", "Komplain"])

    if menu == "Upload Pembayaran":
        bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
        if st.button("Kirim Bukti"):
            link = upload_to_drive(bukti, f"Bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')}.jpg")
            bayar_ws = connect_gsheet().worksheet("Pembayaran")
            bayar_ws.append_row([username, link, str(datetime.now())])
            st.success("Bukti pembayaran berhasil dikirim.")

    if menu == "Komplain":
        isi = st.text_area("Tulis Komplain Anda")
        if st.button("Kirim Komplain"):
            komplain_ws = connect_gsheet().worksheet("Komplain")
            komplain_ws.append_row([username, isi, str(datetime.now())])
            st.success("Komplain berhasil dikirim.")

# ---------- Main App ----------

st.set_page_config(page_title="Dashboard Kost123", layout="wide")
st.title("📊 Dashboard Kost123")

if not cek_admin():
    registrasi_admin()
else:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = login(username, password)
        if role == "admin":
            st.sidebar.success("Login sebagai Admin")
            menu = st.sidebar.selectbox("Menu Admin", ["Kelola Kamar", "Verifikasi Booking"])
            if menu == "Kelola Kamar":
                kelola_kamar()
            elif menu == "Verifikasi Booking":
                verifikasi_booking()
        elif role == "penyewa":
            fitur_penyewa(username)
        else:
            st.error("Username atau Password salah.")
