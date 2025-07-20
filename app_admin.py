import streamlit as st
import bcrypt
from datetime import datetime
from cloudinary_upload import upload_to_cloudinary
from sheets import connect_gsheet
import calendar

# ----------------- CONFIG & SESSION ------------------
st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""

# ----------------- AUTH FUNCTION ------------------
def login(username, password):
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    for u in users:
        if u['username'] == username:
            if bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
                return u['role']
    return None

# ----------------- ADMIN FUNCTION ------------------
def admin_dashboard():
    st.sidebar.title("Menu Admin")
    menu = st.sidebar.radio("Pilih Menu", ["Dashboard", "Kelola Kamar", "Verifikasi Booking", "Manajemen Penyewa", "Logout"])

    if menu == "Dashboard":
        st.header("Dashboard Admin")
        st.write("Selamat datang di Dashboard Admin.")

    elif menu == "Kelola Kamar":
        kelola_kamar()

    elif menu == "Verifikasi Booking":
        verifikasi_booking()

    elif menu == "Manajemen Penyewa":
        manajemen_penyewa()

    elif menu == "Logout":
        logout()

# ----------------- PENYEWA FUNCTION ------------------
def penyewa_dashboard(username):
    st.sidebar.title("Menu Penyewa")
    menu = st.sidebar.radio("Pilih Menu", ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"])

    if menu == "Dashboard":
        tampilkan_dashboard_penyewa(username)

    elif menu == "Pembayaran":
        fitur_pembayaran(username)

    elif menu == "Komplain":
        fitur_komplain(username)

    elif menu == "Profil Saya":
        fitur_edit_profil(username)

    elif menu == "Logout":
        logout()

# ----------------- FITUR ADMIN ------------------
def kelola_kamar():
    st.header("Kelola Kamar")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()
    for idx, k in enumerate(data):
        with st.expander(f"{k['Nama']} - Rp{k['Harga']}"):
            st.write(f"Status: {k['Status']}")
            st.write(k['Deskripsi'])
            if k['Link Foto']:
                st.image(k['Link Foto'], width=300)
            if st.button(f"Hapus {k['Nama']}", key=f"hapus{idx}"):
                kamar_ws.delete_rows(idx+2)
                st.success("Kamar dihapus.")
                st.rerun()

    st.markdown("---")
    st.subheader("Tambah Kamar Baru")
    nama = st.text_input("Nama Kamar")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg","png"])
    if st.button("Tambah Kamar"):
        link_foto = upload_to_cloudinary(foto, nama) if foto else ""
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link_foto])
        st.success("Kamar berhasil ditambahkan.")
        st.rerun()


def verifikasi_booking():
    st.header("Verifikasi Booking")
    sheet = connect_gsheet()
    booking_ws = sheet.worksheet("Booking")
    kamar_ws = sheet.worksheet("Kamar")
    user_ws = sheet.worksheet("User")

    data = booking_ws.get_all_records()
    kamar_data = kamar_ws.get_all_records()

    for idx, b in enumerate(data):
        st.write(f"{b['nama']} mengajukan kamar {b['kamar_dipilih']}")
        if st.button(f"Setujui {b['nama']}", key=f"setuju{idx}"):
            password = "12345678"
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            user_ws.append_row([b['nama'], hashed, "penyewa", b['kamar_dipilih'], b['no_hp_email'], "", "", str(datetime.now())])
            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2,2,"Terisi")
            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui.")
            st.rerun()


def manajemen_penyewa():
    st.header("Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    data = user_ws.get_all_records()
    now = datetime.now()
    for idx, u in enumerate(data):
        if u['role']=='penyewa':
            label = f"{u['username']} ({u['kamar']})"
            with st.expander(label):
                st.write(f"Nama: {u['username']}")
                st.write(f"Kontak: {u['kontak']}")
                st.write(f"Last Edit: {u.get('last_edit','-')}")
                if st.button(f"Hapus {u['username']}", key=f"hapus_user{idx}"):
                    user_ws.delete_rows(idx+2)
                    st.success("Penyewa dihapus.")
                    st.rerun()

# ----------------- FITUR PENYEWA ------------------
def tampilkan_dashboard_penyewa(username):
    st.header("Dashboard Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    kamar_ws = connect_gsheet().worksheet("Kamar")
    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")

    users = user_ws.get_all_records()
    u = next(filter(lambda x: x['username']==username, users), None)

    st.write(f"Nama: {u['username']}")
    st.write(f"Kamar: {u['kamar']}")

    bulan_ini = datetime.now().strftime("%B %Y")
    bayar = pembayaran_ws.get_all_records()
    sudah_bayar = any(b['username']==username and bulan_ini in b['bulan_tahun'] for b in bayar)
    status = "Lunas" if sudah_bayar else "Belum Lunas"
    st.write(f"Status Pembayaran Bulan Ini: {status}")


def fitur_pembayaran(username):
    st.header("Upload Pembayaran")
    bulan = st.selectbox("Bulan", list(calendar.month_name)[1:])
    tahun = st.text_input("Tahun", value=str(datetime.now().year))
    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","png"])
    if st.button("Kirim Bukti"):
        link = upload_to_cloudinary(bukti, f"bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
        ws = connect_gsheet().worksheet("Pembayaran")
        ws.append_row([username, link, f"{bulan} {tahun}", str(datetime.now())])
        st.success("Bukti pembayaran terkirim.")


def fitur_komplain(username):
    st.header("Komplain")
    isi = st.text_area("Tulis Komplain")
    foto = st.file_uploader("Bukti Foto (Opsional)", type=["jpg","png"])
    if st.button("Kirim Komplain"):
        link = upload_to_cloudinary(foto, f"komplain_{username}_{datetime.now().strftime('%Y%m%d%H%M')}") if foto else ""
        ws = connect_gsheet().worksheet("Komplain")
        ws.append_row([username, isi, link, str(datetime.now())])
        st.success("Komplain terkirim.")


def fitur_edit_profil(username):
    st.header("Profil Saya")
    user_ws = connect_gsheet().worksheet("User")
    data = user_ws.get_all_records()
    u = next(filter(lambda x: x['username']==username, data), None)

    last_edit = u.get('last_edit','')
    allowed = True
    if last_edit:
        last = datetime.strptime(last_edit, "%Y-%m-%d %H:%M:%S")
        allowed = (datetime.now() - last).days >=7

    nama = st.text_input("Nama Lengkap", value=u['username'])
    kontak = st.text_input("Kontak", value=u['kontak'])
    foto = st.file_uploader("Foto Profil (Opsional)", type=["jpg","png"])
    new_pass = st.text_input("Ganti Password", type="password")

    if st.button("Simpan Perubahan"):
        if allowed:
            idx = data.index(u)
            if new_pass:
                hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                user_ws.update_cell(idx+2,2,hashed)
            user_ws.update_cell(idx+2,1,nama)
            user_ws.update_cell(idx+2,5,kontak)
            if foto:
                link = upload_to_cloudinary(foto,f"profil_{username}")
                user_ws.update_cell(idx+2,6,link)
            user_ws.update_cell(idx+2,8,str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            st.success("Profil diperbarui.")
        else:
            st.warning("Edit profil hanya bisa seminggu sekali.")

# ----------------- LOGOUT ------------------
def logout():
    st.session_state.login_status=False
    st.session_state.username=""
    st.rerun()

# ----------------- MAIN APP ------------------
if not st.session_state.login_status:
    st.title("Login Kost123")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        role = login(username,password)
        if role:
            st.session_state.login_status=True
            st.session_state.username=username
            st.session_state.role=role
            st.rerun()
        else:
            st.error("Login gagal.")
else:
    if st.session_state.role=="admin":
        admin_dashboard()
    elif st.session_state.role=="penyewa":
        penyewa_dashboard(st.session_state.username)
