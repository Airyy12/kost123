import streamlit as st
import bcrypt
from datetime import datetime
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Inisialisasi Session State ----------
if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = None
    st.session_state.menu = None

# ---------- Fungsi Login ----------
def login(username, password):
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    for u in users:
        if u['username'] == username and bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
            return u['role'], u['username']
    return None, None

# ---------- Fungsi Sidebar ----------
def sidebar_admin():
    st.sidebar.markdown('<h2 style="color:white;">🏠 Kost123 Admin Panel</h2>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu Admin", ["Dashboard", "Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa", "Logout"])
    return menu

def sidebar_penyewa():
    st.sidebar.markdown('<h2 style="color:white;">🏠 Kost123 Penyewa</h2>', unsafe_allow_html=True)
    menu = st.sidebar.radio("Menu Penyewa", ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"])
    return menu

# ---------- Login Page ----------
def login_page():
    st.title("🔐 Login Kost123")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role, user = login(username, password)
        if role:
            st.session_state.login_status = True
            st.session_state.role = role
            st.session_state.username = user
            st.session_state.menu = "Dashboard"
            st.experimental_rerun()
        else:
            st.error("Username atau Password salah.")

# ---------- Penyewa Menu ----------
def penyewa_dashboard():
    st.title("📊 Dashboard Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    user_data = next(u for u in users if u['username']==st.session_state.username)
    st.write(f"Nama: {user_data['username']}")
    st.write(f"Kamar: {user_data.get('kamar','Belum Terdaftar')}")
    st.write(f"Status Pembayaran: {user_data.get('Status Pembayaran','Belum Ada Data')}")

def penyewa_pembayaran():
    st.title("💸 Pembayaran Kost")
    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    tahun = st.text_input("Tahun", str(datetime.now().year))
    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","jpeg","png"])
    if st.button("Kirim Bukti"):
        link = upload_to_cloudinary(bukti, f"Bayar_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}")
        bayar_ws = connect_gsheet().worksheet("Pembayaran")
        bayar_ws.append_row([st.session_state.username, bulan, tahun, link, str(datetime.now())])
        st.success("Bukti pembayaran berhasil dikirim.")

def penyewa_komplain():
    st.title("📢 Komplain")
    isi = st.text_area("Tulis Komplain Anda")
    bukti = st.file_uploader("Upload Foto (Opsional)", type=["jpg","jpeg","png"])
    if st.button("Kirim Komplain"):
        link = upload_to_cloudinary(bukti, f"Komplain_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}") if bukti else ""
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_ws.append_row([st.session_state.username, isi, link, str(datetime.now())])
        st.success("Komplain berhasil dikirim.")

def penyewa_profil():
    st.title("👤 Profil Saya")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = next(i for i,u in enumerate(users) if u['username']==st.session_state.username)
    nama = st.text_input("Nama Lengkap", value=users[idx].get('nama_lengkap',''))
    kontak = st.text_input("Nomor HP / Email", value=users[idx].get('kontak',''))
    foto = st.file_uploader("Foto Profil", type=["jpg","jpeg","png"])
    if st.button("Update Profil"):
        link = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}") if foto else users[idx].get('foto','')
        user_ws.update(f"C{idx+2}", nama)
        user_ws.update(f"D{idx+2}", kontak)
        user_ws.update(f"E{idx+2}", link)
        st.success("Profil berhasil diperbarui.")

# ---------- Admin Menu ----------
def admin_dashboard():
    st.title("📊 Dashboard Admin")
    st.write("Selamat datang di Admin Panel Kost123.")

def admin_kelola_kamar():
    st.title("🛠️ Kelola Kamar")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()

    st.subheader("Daftar Kamar")
    for idx, k in enumerate(data):
        st.write(f"{k['Nama']} - {k['Status']} - Rp{k['Harga']}")

    st.markdown("---")
    st.subheader("Tambah Kamar Baru")
    nama = st.text_input("Nama Kamar")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg","jpeg","png"])

    if st.button("Tambah Kamar"):
        link = upload_to_cloudinary(foto, f"Kamar_{nama}") if foto else ""
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link])
        st.success("Kamar berhasil ditambahkan.")

def admin_verifikasi_booking():
    st.title("✅ Verifikasi Booking")
    booking_ws = connect_gsheet().worksheet("Booking")
    user_ws = connect_gsheet().worksheet("User")
    kamar_ws = connect_gsheet().worksheet("Kamar")

    bookings = booking_ws.get_all_records()
    kamar_data = kamar_ws.get_all_records()

    for idx, b in enumerate(bookings):
        st.write(f"{b['nama']} mengajukan kamar {b['kamar_dipilih']}")
        if st.button(f"Setujui {b['nama']}", key=f"setuju_{idx}"):
            password = "12345678"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_ws.append_row([b['nama'], hashed, "penyewa", b['kamar_dipilih'], '', '', '', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")
            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui dengan password default 12345678.")

def admin_manajemen_penyewa():
    st.title("👥 Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    for u in users:
        if u['role'] == 'penyewa':
            st.write(f"{u['username']} - {u.get('kamar','-')}")

# ---------- Main App Flow ----------
if not st.session_state.login_status:
    login_page()
else:
    if st.session_state.role == "admin":
        menu = sidebar_admin()
        if menu == "Dashboard":
            admin_dashboard()
        elif menu == "Kelola Kamar":
            admin_kelola_kamar()
        elif menu == "Verifikasi Booking":
            admin_verifikasi_booking()
        elif menu == "Manajemen Penyewa":
            admin_manajemen_penyewa()
        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()
    elif st.session_state.role == "penyewa":
        menu = sidebar_penyewa()
        if menu == "Dashboard":
            penyewa_dashboard()
        elif menu == "Pembayaran":
            penyewa_pembayaran()
        elif menu == "Komplain":
            penyewa_komplain()
        elif menu == "Profil Saya":
            penyewa_profil()
        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()
