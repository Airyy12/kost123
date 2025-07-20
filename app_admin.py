import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
import re

# ---------- Fungsi Login & Registrasi Admin ----------

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

    # List untuk menyimpan booking yang mau dihapus setelah loop
    rows_to_delete = []

    for idx, b in enumerate(data):
        st.write(f"**{b['nama']}** mengajukan kamar **{b['kamar_dipilih']}**")
        st.write(f"Kontak: {b['no_hp_email']}")

        if st.button(f"Setujui {b['nama']}", key=f"setuju{idx}"):
            try:
                password = "12345678"  # Default password
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                user_ws.append_row([b['nama'], hashed, "penyewa"])

                # Update status kamar
                for i, k in enumerate(kamar_data):
                    if k['Nama'] == b['kamar_dipilih']:
                        kamar_ws.update_cell(i+2, 2, "Terisi")  # Kolom Status

                # Tandai baris untuk dihapus nanti
                rows_to_delete.append(idx + 2)

                st.success(f"{b['nama']} disetujui. Password default: {password}")

            except Exception as e:
                st.error(f"Gagal memproses booking: {e}")

    # Setelah semua loop selesai baru hapus
    for row in sorted(rows_to_delete, reverse=True):
        booking_ws.delete_rows(row)

    if rows_to_delete:
        st.rerun()


def manajemen_penyewa():
    st.subheader("👥 Manajemen Penyewa")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    penyewa_list = [u for u in users if u['role'] == 'penyewa']

    if not penyewa_list:
        st.info("Belum ada penyewa yang terdaftar.")
        return

    for idx, p in enumerate(penyewa_list):
        with st.expander(f"{p['username']}"):
            st.write(f"**Username:** {p['username']}")
            if st.button(f"Hapus Penyewa {p['username']}", key=f"hapus_penyewa_{idx}"):
                user_ws.delete_rows(idx + 2)
                st.success(f"Penyewa {p['username']} dihapus.")
                st.rerun()

# ---------- Fitur Penyewa ----------

def fitur_penyewa(username):
    st.header(f"Selamat Datang, {username}")

    menu = st.sidebar.selectbox("Menu Penyewa", ["Upload Pembayaran", "Komplain"])

    if menu == "Upload Pembayaran":
        bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
        bulan = st.text_input("Bulan & Tahun Pembayaran (Contoh: Juli 2025 / Juli-Agustus 2025)")
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
