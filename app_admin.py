import streamlit as st
import bcrypt
from datetime import datetime
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Styling Profesional Modern ----------
st.markdown("""
<style>
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(145deg, #2c3e50, #34495e);
    padding: 25px;
    border-radius: 15px;
    box-shadow: 0px 0px 15px rgba(0,0,0,0.3);
}
.sidebar-title {
    font-size:26px;
    font-weight:bold;
    color:#ECF0F1;
    margin-bottom:25px;
}
.menu-item {
    color: #ECF0F1;
    padding: 14px 20px;
    margin-bottom: 12px;
    border-radius: 10px;
    transition: background-color 0.3s ease;
    font-size: 17px;
}
.menu-item:hover {
    background-color: #3d566e;
    cursor: pointer;
}
.menu-selected {
    background-color: #1abc9c;
    color: #fff;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
def sidebar_menu():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)

        role = st.session_state.get("role", None)
        menu = st.session_state.get("menu", None)

        if role == "admin":
            options = ["Dashboard Admin", "Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa", "Logout"]
        elif role == "penyewa":
            options = ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"]
        else:
            return

        for opt in options:
            selected = "menu-selected" if menu == opt else "menu-item"
            if st.button(opt, key=opt):
                st.session_state.menu = opt
                st.rerun()

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
                st.session_state.role = u['role']
                st.session_state.username = username
                if u['role'] == "admin":
                    st.session_state.menu = "Dashboard Admin"
                else:
                    st.session_state.menu = "Dashboard"
                st.session_state.login_status = True
                st.rerun()
        else:
            st.error("Username atau Password salah.")

# ---------- Penyewa Features ----------
def penyewa_dashboard():
    st.title("📊 Dashboard Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    user_data = next(u for u in users if u['username']==st.session_state.username)
    st.write(f"**Nama:** {user_data['username']}")
    st.write(f"**Kamar:** {user_data.get('kamar','Belum Terdaftar')}")
    st.write(f"**Status Pembayaran:** {user_data.get('Status Pembayaran','Belum Ada Data')}")

def pembayaran():
    st.title("💸 Pembayaran Kost")
    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
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
        user_ws.update(f"F{idx+2}", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        st.success("Profil berhasil diperbarui.")

# ---------- Admin Features ----------
def admin_dashboard():
    st.title("📊 Dashboard Admin")
    st.write("Selamat datang di Panel Admin Kost123.")

def kelola_kamar():
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

# ---------- Main App Flow ----------
if "login_status" not in st.session_state:
    st.session_state.login_status = False

if not st.session_state.login_status:
    login_page()
else:
    sidebar_menu()
    menu = st.session_state.get("menu", None)

    if st.session_state.role == "penyewa":
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
            st.rerun()

    elif st.session_state.role == "admin":
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
            st.rerun()
