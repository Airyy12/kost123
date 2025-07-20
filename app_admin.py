import streamlit as st
import bcrypt
from datetime import datetime
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Sidebar Profesional Modern ----------
st.markdown("""
<style>
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(145deg, #1f1f1f, #292929);
    padding: 20px;
    border-radius: 12px;
}
.sidebar-title {
    font-size:24px;
    font-weight:bold;
    color:#FFFFFF;
    margin-bottom:20px;
}
.menu-item {
    color: #E0E0E0;
    padding: 12px 20px;
    margin-bottom: 10px;
    border-radius: 8px;
    transition: background-color 0.3s ease;
    font-size: 17px;
}
.menu-item:hover {
    background-color: #3A3A3A;
    cursor: pointer;
}
.menu-selected {
    background-color: #4C4C4C;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)

    if "role" not in st.session_state:
        st.session_state.role = None

    menu = None

    if st.session_state.role == "admin":
        menu_options = {
            "Dashboard Admin": "📊 Dashboard Admin",
            "Kelola Kamar": "🛠️ Kelola Kamar",
            "Verifikasi Booking": "✅ Verifikasi Booking",
            "Manajemen Penyewa": "👥 Manajemen Penyewa",
            "Logout": "🚪 Logout"
        }
    elif st.session_state.role == "penyewa":
        menu_options = {
            "Dashboard": "📊 Dashboard",
            "Pembayaran": "💸 Pembayaran",
            "Komplain": "📢 Komplain",
            "Profil Saya": "👤 Profil Saya",
            "Logout": "🚪 Logout"
        }

    if st.session_state.role:
        for key, label in menu_options.items():
            if st.button(label, key=key):
                st.session_state.menu = key
                st.experimental_rerun()

# ---------- Main Content ----------
if "login_status" not in st.session_state:
    st.session_state.login_status = False

if not st.session_state.login_status:
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
                st.session_state.menu = list(menu_options.keys())[0]
                st.experimental_rerun()
        else:
            st.error("Username atau Password salah.")
else:
    if st.session_state.role == "penyewa":
        menu = st.session_state.get("menu", "Dashboard")
        if menu == "Dashboard":
            st.title("📊 Dashboard Penyewa")
            user_ws = connect_gsheet().worksheet("User")
            users = user_ws.get_all_records()
            user_data = next(u for u in users if u['username']==st.session_state.username)
            st.write(f"Nama: {user_data['username']}")
            st.write(f"Kamar: {user_data.get('kamar','Belum Terdaftar')}")
            st.write(f"Status Pembayaran: {user_data.get('Status Pembayaran','Belum Ada Data')}")

        elif menu == "Pembayaran":
            st.title("💸 Pembayaran Kost")
            bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            tahun = st.text_input("Tahun", str(datetime.now().year))
            bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","jpeg","png"])
            if st.button("Kirim Bukti"):
                link = upload_to_cloudinary(bukti, f"Bayar_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}")
                bayar_ws = connect_gsheet().worksheet("Pembayaran")
                bayar_ws.append_row([st.session_state.username, bulan, tahun, link, str(datetime.now())])
                st.success("Bukti pembayaran berhasil dikirim.")

        elif menu == "Komplain":
            st.title("📢 Komplain")
            isi = st.text_area("Tulis Komplain Anda")
            bukti = st.file_uploader("Upload Foto (Opsional)", type=["jpg","jpeg","png"])
            if st.button("Kirim Komplain"):
                link = upload_to_cloudinary(bukti, f"Komplain_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}") if bukti else ""
                komplain_ws = connect_gsheet().worksheet("Komplain")
                komplain_ws.append_row([st.session_state.username, isi, link, str(datetime.now())])
                st.success("Komplain berhasil dikirim.")

        elif menu == "Profil Saya":
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

        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()

    elif st.session_state.role == "admin":
        menu = st.session_state.get("menu", "Dashboard Admin")
        if menu == "Dashboard Admin":
            st.title("📊 Dashboard Admin")
            st.write("Selamat datang di Admin Panel Kost123.")

        elif menu == "Kelola Kamar":
            st.title("🛠️ Kelola Kamar")
            st.write("(Fitur kelola kamar di sini - placeholder)")

        elif menu == "Verifikasi Booking":
            st.title("✅ Verifikasi Booking")
            st.write("(Fitur verifikasi booking di sini - placeholder)")

        elif menu == "Manajemen Penyewa":
            st.title("👥 Manajemen Penyewa")
            st.write("(Fitur manajemen penyewa di sini - placeholder)")

        elif menu == "Logout":
            st.session_state.clear()
            st.experimental_rerun()
