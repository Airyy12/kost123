import streamlit as st
import bcrypt
from datetime import datetime
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

# ---------- Page Config ----------
st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Custom CSS for Professional UI ----------
st.markdown("""
<style>
body {
    background-color: #f5f5f5;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(135deg, #232526, #414345);
    padding: 25px;
    border-radius: 12px;
}
.sidebar-title {
    font-size: 26px;
    font-weight: bold;
    color: #FFFFFF;
    margin-bottom: 30px;
    text-align: center;
}
.menu-item {
    color: #E0E0E0;
    padding: 14px 25px;
    margin-bottom: 12px;
    border-radius: 10px;
    transition: all 0.3s ease;
    font-size: 18px;
}
.menu-item:hover {
    background-color: #5a5a5a;
    cursor: pointer;
}
.menu-selected {
    background-color: #6d6d6d;
    font-weight: bold;
    box-shadow: inset 0 0 5px #00000055;
}
.stButton>button {
    background-color: #4CAF50;
    color: white;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
    transition: 0.3s;
    font-size: 16px;
}
.stButton>button:hover {
    background-color: #45a049;
}
</style>
""", unsafe_allow_html=True)

# ---------- Session State Initialization ----------
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu = None

# ---------- Sidebar Menu ----------
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)

    if st.session_state.role:
        if st.session_state.role == "admin":
            menu_options = [
                ("Dashboard Admin", "📊 Dashboard Admin"),
                ("Kelola Kamar", "🛠️ Kelola Kamar"),
                ("Verifikasi Booking", "✅ Verifikasi Booking"),
                ("Manajemen Penyewa", "👥 Manajemen Penyewa"),
                ("Logout", "🚪 Logout")
            ]
        else:
            menu_options = [
                ("Dashboard", "📊 Dashboard"),
                ("Pembayaran", "💸 Pembayaran"),
                ("Komplain", "📢 Komplain"),
                ("Profil Saya", "👤 Profil Saya"),
                ("Logout", "🚪 Logout")
            ]

        for key, label in menu_options:
            button_style = "menu-item"
            if st.session_state.menu == key:
                button_style += " menu-selected"
            if st.button(label, key=key):
                st.session_state.menu = key
                st.experimental_rerun()

# ---------- Login Page ----------
def login_page():
    st.title("🔐 Login Kost123")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        for u in users:
            if u['username'] == username and bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
                st.session_state.login_status = True
                st.session_state.username = username
                st.session_state.role = u['role']
                if not st.session_state.menu:
                    st.session_state.menu = "Dashboard Admin" if u['role']=="admin" else "Dashboard"
                st.experimental_rerun()
        else:
            st.error("Username atau Password salah.")

# ---------- Penyewa Features ----------
def penyewa_dashboard():
    st.title("📊 Dashboard Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    user_data = next(u for u in users if u['username']==st.session_state.username)
    st.write(f"**Nama:** {user_data.get('nama_lengkap', user_data['username'])}")
    st.write(f"**Kamar:** {user_data.get('kamar','Belum Terdaftar')}")
    st.write(f"**Status Pembayaran:** {user_data.get('Status Pembayaran','Belum Ada Data')}")

def pembayaran():
    st.title("💸 Pembayaran Kost")
    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    tahun = st.text_input("Tahun", str(datetime.now().year))
    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","jpeg","png"])
    if st.button("Kirim Bukti"):
        link = upload_to_cloudinary(bukti, f"Bayar_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}")
        bayar_ws = connect_gsheet().worksheet("Pembayaran")
        bayar_ws.append_row([st.session_state.username, bulan, tahun, link, str(datetime.now())])
        st.success("Bukti pembayaran berhasil dikirim.")

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
    nama = st.text_input("Nama Lengkap", value=users[idx].get('nama_lengkap',''))
    kontak = st.text_input("Nomor HP / Email", value=users[idx].get('kontak',''))
    foto = st.file_uploader("Foto Profil", type=["jpg","jpeg","png"])
    if st.button("Update Profil"):
        link = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}") if foto else users[idx].get('foto','')
        user_ws.update(f"C{idx+2}", nama)
        user_ws.update(f"D{idx+2}", kontak)
        user_ws.update(f"E{idx+2}", link)
        st.success("Profil berhasil diperbarui.")

# ---------- Admin Features ----------
def admin_dashboard():
    st.title("📊 Dashboard Admin")
    st.write("Selamat datang di Admin Panel Kost123.")

def kelola_kamar():
    st.title("🛠️ Kelola Kamar")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()
    st.subheader("Daftar Kamar")
    for k in data:
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

def verifikasi_booking():
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

def manajemen_penyewa():
    st.title("👥 Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    for u in users:
        if u['role'] == 'penyewa':
            st.write(f"{u['username']} - {u.get('kamar','-')}")

# ---------- Routing ----------
if not st.session_state.login_status:
    login_page()
else:
    menu = st.session_state.menu
    if st.session_state.role == "admin":
        if menu == "Dashboard Admin":
            admin_dashboard()
        elif menu == "Kelola Kamar":
            kelola_kamar()
        elif menu == "Verifikasi Booking":
            verifikasi_booking()
        elif menu == "Manajemen Penyewa":
            manajemen_penyewa()
        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()
    else:
        if menu == "Dashboard":
            penyewa_dashboard()
        elif menu == "Pembayaran":
            pembayaran()
        elif menu == "Komplain":
            komplain()
        elif menu == "Profil Saya":
            profil_saya()
        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()
