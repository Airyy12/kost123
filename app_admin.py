import streamlit as st
import bcrypt
from datetime import datetime, timedelta
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary

st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Custom CSS ----------
st.markdown("""
<style>
body {
    background-color: #1e1e1e;
    color: #f0f0f0;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(145deg, #2c2c2c, #3a3a3a);
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
.info-card {
    background: rgba(60,60,60,0.5);
    padding: 20px;
    border-radius: 12px;
    margin-bottom: 20px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}
.stButton>button {
    background-color: #3d3d3d;
    color: white;
    padding: 10px 24px;
    border: none;
    border-radius: 8px;
    transition: 0.3s;
    font-size: 16px;
}
.stButton>button:hover {
    background-color: #505050;
}
</style>
""", unsafe_allow_html=True)

# ---------- Session Init ----------
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu = None
    st.session_state.submenu = None

# ---------- Sidebar ----------
def sidebar_menu():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)

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
            style = "menu-item"
            if st.session_state.menu == key:
                style += " menu-selected"
            if st.button(label, key=key):
                st.session_state.menu = key
                st.session_state.submenu = None

# ---------- Login ----------
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
                st.session_state.menu = "Dashboard Admin" if u['role']=="admin" else "Dashboard"
                return
        st.error("Username atau Password salah.")

# ---------- Penyewa Dashboard ----------
def penyewa_dashboard():
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    user_data = next(u for u in users if u['username']==st.session_state.username)

    st.title(f"Selamat Datang, {user_data.get('nama_lengkap', user_data['username'])}")

    if user_data.get('foto_profil'):
        st.image(user_data['foto_profil'], width=100, caption="Foto Profil", output_format="JPEG", use_column_width=False, clamp=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div class="info-card">
            <b>Nomor Kamar:</b><br>{user_data.get('kamar','Belum Terdaftar')}
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="info-card">
            <b>Status Pembayaran:</b><br>{user_data.get('Status Pembayaran','Belum Ada Data')}
        </div>
        """, unsafe_allow_html=True)

# ---------- Profil Saya ----------
def profil_saya():
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = next(i for i,u in enumerate(users) if u['username']==st.session_state.username)
    user_data = users[idx]

    st.header("👤 Profil Saya")

    st.write(f"**Username:** {user_data['username']}")
    st.write(f"**Nama Lengkap:** {user_data.get('nama_lengkap','')}")
    st.write(f"**Nomor HP/Email:** {user_data.get('no_hp','')}")
    st.write(f"**Kamar:** {user_data.get('kamar','-')}")

    if st.button("Edit Profil"):
        st.session_state.submenu = "edit_profil"

    if st.session_state.submenu == "edit_profil":
        st.subheader("Edit Profil")
        last_edit_str = user_data.get('last_edit', '')
        can_edit = True

        if st.session_state.role != 'admin':
            if last_edit_str:
                last_edit = datetime.strptime(last_edit_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_edit < timedelta(days=7):
                    can_edit = False

        if can_edit:
            nama = st.text_input("Nama Lengkap", value=user_data.get('nama_lengkap',''))
            kontak = st.text_input("Nomor HP / Email", value=user_data.get('no_hp',''))
            foto = st.file_uploader("Foto Profil", type=["jpg","jpeg","png"])
            new_password = st.text_input("Ganti Password (Opsional)", type="password")

            if st.button("Simpan Perubahan"):
                link = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}") if foto else user_data.get('foto_profil','')
                user_ws.update_cell(idx+2, 4, nama)
                user_ws.update_cell(idx+2, 5, f"'{kontak}")  # Tambah ' agar 0 tidak hilang
                user_ws.update_cell(idx+2, 7, link)
                user_ws.update_cell(idx+2, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if new_password:
                    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    user_ws.update_cell(idx+2, 2, hashed)
                st.success("Profil berhasil diperbarui.")
                st.session_state.submenu = None
        else:
            st.warning("Edit profil hanya bisa dilakukan 1x dalam seminggu.")

# ---------- Komplain ----------
def komplain():
    st.title("📢 Komplain")
    isi = st.text_area("Tulis Komplain Anda")
    bukti = st.file_uploader("Upload Foto (Opsional)", type=["jpg","jpeg","png"])
    if st.button("Kirim Komplain"):
        link = upload_to_cloudinary(bukti, f"Komplain_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M')}") if bukti else ""
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_ws.append_row([st.session_state.username, isi, link, str(datetime.now())])
        st.success("Komplain berhasil dikirim.")

# ---------- Pembayaran ----------
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

# ---------- Admin Dashboard ----------
def admin_dashboard():
    st.title("📊 Dashboard Admin")
    st.markdown("<div class='info-card'>Selamat datang di Admin Panel Kost123.</div>", unsafe_allow_html=True)

# ---------- Kelola Kamar ----------
def kelola_kamar():
    st.title("🛠️ Kelola Kamar")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()
    for k in data:
        st.markdown(f"<div class='info-card'>{k['Nama']} - {k['Status']} - Rp{k['Harga']}</div>", unsafe_allow_html=True)

    nama = st.text_input("Nama Kamar")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg","jpeg","png"])
    if st.button("Tambah Kamar"):
        link = upload_to_cloudinary(foto, f"Kamar_{nama}") if foto else ""
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link])
        st.success("Kamar berhasil ditambahkan.")

# ---------- Verifikasi Booking ----------
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

# ---------- Manajemen Penyewa ----------
def manajemen_penyewa():
    st.title("👥 Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    for u in users:
        if u['role'] == 'penyewa':
            st.markdown(f"<div class='info-card'>{u['username']} - {u.get('kamar','-')}</div>", unsafe_allow_html=True)

# ---------- Routing ----------
if not st.session_state.login_status:
    login_page()
else:
    sidebar_menu()

    menu = st.session_state.menu

    if menu == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
    elif st.session_state.role == "admin":
        if menu == "Dashboard Admin": admin_dashboard()
        elif menu == "Kelola Kamar": kelola_kamar()
        elif menu == "Verifikasi Booking": verifikasi_booking()
        elif menu == "Manajemen Penyewa": manajemen_penyewa()
    else:
        if menu == "Dashboard": penyewa_dashboard()
        elif menu == "Pembayaran": pembayaran()
        elif menu == "Komplain": komplain()
        elif menu == "Profil Saya": profil_saya()
