import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
import calendar
import re

# ---------- CSS Custom ----------
st.markdown("""
<style>
    .css-1d391kg {padding-top: 2rem;}
    .css-18e3th9 {background-color: #1f1f1f;}
    .stButton button {
        background-color: #4CAF50; 
        color: white; 
        border-radius: 8px;
        padding: 10px 24px;
    }
    .badge {
        padding: 5px 10px;
        border-radius: 12px;
        color: white;
        font-weight: bold;
    }
    .lunas {background-color: #4CAF50;}
    .belum {background-color: #E53935;}
</style>
""", unsafe_allow_html=True)

# ---------- Fungsi Login ----------
def login(username, password):
    sheet = connect_gsheet().worksheet("User")
    users = sheet.get_all_records()
    for u in users:
        if u['username'] == username:
            if bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
                return u['role']
    return None

# ---------- Dashboard Penyewa ----------
def penyewa_dashboard(username):
    user_ws = connect_gsheet().worksheet("User")
    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
    users = user_ws.get_all_records()
    pembayarans = pembayaran_ws.get_all_records()

    u = next((i for i in users if i['username'] == username), None)
    if not u:
        st.error("User tidak ditemukan.")
        return

    st.title("🏠 Dashboard Penyewa")
    st.write(f"**Nama:** {u['username']}")
    st.write(f"**Kamar:** {u.get('kamar', '-')}")

    # Cek status pembayaran bulan ini
    now = datetime.now()
    bulan_ini = calendar.month_name[now.month]
    tahun_ini = str(now.year)
    status = "Belum Lunas"
    for p in pembayarans:
        if p['username'] == username and p['bulan'] == bulan_ini and p['tahun'] == tahun_ini:
            status = "Lunas"
            break

    badge_color = 'lunas' if status == 'Lunas' else 'belum'
    st.markdown(f"<span class='badge {badge_color}'>Status Pembayaran Bulan Ini: {status}</span>", unsafe_allow_html=True)

# ---------- Menu Pembayaran ----------
def pembayaran(username):
    st.header("💳 Upload Pembayaran")
    bulan = st.selectbox("Pilih Bulan", list(calendar.month_name)[1:])
    tahun = st.text_input("Tahun", str(datetime.now().year))

    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
    if st.button("Kirim Bukti"):
        if not bukti:
            st.warning("Bukti transfer wajib diupload.")
            return
        link = upload_to_cloudinary(bukti, f"Bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')} ")
        bayar_ws = connect_gsheet().worksheet("Pembayaran")
        bayar_ws.append_row([username, link, bulan, tahun, str(datetime.now())])
        st.success("Bukti pembayaran berhasil dikirim.")

# ---------- Menu Komplain ----------
def komplain(username):
    st.header("📢 Komplain")
    isi = st.text_area("Tulis Komplain Anda")
    foto = st.file_uploader("Upload Bukti Foto (Opsional)", type=["jpg", "jpeg", "png"])
    if st.button("Kirim Komplain"):
        link_foto = ""
        if foto:
            link_foto = upload_to_cloudinary(foto, f"Komplain_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_ws.append_row([username, isi, link_foto, str(datetime.now())])
        st.success("Komplain berhasil dikirim.")

# ---------- Profil Saya ----------
def profil_saya(username):
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = None
    for i, u in enumerate(users):
        if u['username'] == username:
            idx = i
            break

    if idx is None:
        st.error("User tidak ditemukan.")
        return

    u = users[idx]

    st.header("👤 Profil Saya")
    nama = st.text_input("Nama Lengkap", u.get('nama', u['username']))
    kontak = st.text_input("No HP / Email", u.get('kontak', ''))
    foto = st.file_uploader("Foto Profil (Opsional)", type=["jpg", "jpeg", "png"])

    # Cek batas waktu edit
    if u.get('last_edit'):
        try:
            last_edit = datetime.strptime(u['last_edit'], "%Y-%m-%d %H:%M:%S")
            delta = datetime.now() - last_edit
            if delta.days < 7 and u['role'] == 'penyewa':
                st.info(f"Edit profil hanya bisa seminggu sekali. Coba lagi dalam {7 - delta.days} hari.")
                return
        except:
            pass

    if st.button("Simpan Perubahan"):
        link_foto = u.get('foto_profil', '')
        if foto:
            link_foto = upload_to_cloudinary(foto, f"Profil_{username}.jpg")

        user_ws.update(f"B{idx+2}", nama)
        user_ws.update(f"C{idx+2}", kontak)
        user_ws.update(f"D{idx+2}", link_foto)
        user_ws.update(f"E{idx+2}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        st.success("Profil berhasil diupdate.")

# ---------- Main App ----------
st.set_page_config(page_title="Dashboard Kost123", layout="wide")

if 'login_status' not in st.session_state:
    st.session_state.login_status = False
    st.session_state.username = ""
    st.session_state.role = ""

if not st.session_state.login_status:
    st.title("🔑 Login Kost123")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = login(username, password)
        if role:
            st.session_state.login_status = True
            st.session_state.username = username
            st.session_state.role = role
            st.rerun()
        else:
            st.error("Username atau password salah.")
else:
    if st.session_state.role == 'penyewa':
        menu = st.sidebar.radio("Menu Penyewa", ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"])
        if menu == "Dashboard":
            penyewa_dashboard(st.session_state.username)
        elif menu == "Pembayaran":
            pembayaran(st.session_state.username)
        elif menu == "Komplain":
            komplain(st.session_state.username)
        elif menu == "Profil Saya":
            profil_saya(st.session_state.username)
        elif menu == "Logout":
            st.session_state.login_status = False
            st.rerun()

    elif st.session_state.role == 'admin':
        st.sidebar.header("Menu Admin")
        menu = st.sidebar.radio("", ["Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa", "Logout"])

        if menu == "Kelola Kamar":
            st.write("Fitur Kelola Kamar di sini (lanjutan)")
        elif menu == "Verifikasi Booking":
            st.write("Fitur Verifikasi Booking di sini (lanjutan)")
        elif menu == "Manajemen Penyewa":
            st.write("Fitur Manajemen Penyewa di sini (lanjutan)")
        elif menu == "Logout":
            st.session_state.login_status = False
            st.rerun()
