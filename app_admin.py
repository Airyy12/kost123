import streamlit as st
import bcrypt
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
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
            user_ws.append_row([username, hashed, "admin", "", "", "", "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
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
            user_ws.append_row([b['nama'], hashed, "penyewa", b['nama'], b['no_hp_email'], "", b['kamar_dipilih'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            for i, k in enumerate(kamar_data):
                if k['Nama'] == b['kamar_dipilih']:
                    kamar_ws.update_cell(i+2, 2, "Terisi")
            booking_ws.delete_rows(idx+2)
            st.success(f"{b['nama']} disetujui. Password default: {password}")
            st.rerun()

def manajemen_penyewa():
    st.subheader("👥 Manajemen Penyewa")
    user_ws = connect_gsheet().worksheet("User")
    bayar_ws = connect_gsheet().worksheet("Pembayaran")
    users = user_ws.get_all_records()
    pembayaran = bayar_ws.get_all_records()
    bulan_ini = datetime.now().strftime("%B %Y")

    for idx, u in enumerate(users):
        if u['role'] == 'penyewa':
            label = f"{u['username']} ({u['kamar']})"
            with st.expander(label):
                st.write(f"Nama Lengkap: {u.get('nama_lengkap','')}")
                st.write(f"No HP: {u.get('no_hp','')}")

                status_bayar = "Belum Bayar"
                for p in pembayaran:
                    if p['username'] == u['username'] and bulan_ini in p['bulan']:
                        status_bayar = "Lunas"
                        break
                st.write(f"Status Pembayaran: {status_bayar}")

                new_nama = st.text_input(f"Edit Nama {u['username']}", value=u.get('nama_lengkap',''))
                new_nohp = st.text_input(f"Edit No HP {u['username']}", value=u.get('no_hp',''))
                if st.button(f"Simpan {u['username']}"):
                    user_ws.update_cell(idx+2, 4, new_nama)
                    user_ws.update_cell(idx+2, 5, new_nohp)
                    user_ws.update_cell(idx+2, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    st.success("Data diperbarui.")
                    st.rerun()

# ---------- Fitur Penyewa ----------

def fitur_penyewa(username):
    st.header(f"Selamat Datang, {username}")
    user_ws = connect_gsheet().worksheet("User")
    bayar_ws = connect_gsheet().worksheet("Pembayaran")
    users = user_ws.get_all_records()
    u = next(i for i in users if i['username'] == username)

    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
    tahun = st.text_input("Tahun", value=str(datetime.now().year))

    bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
    if st.button("Kirim Bukti"):
        link = upload_to_cloudinary(bukti, f"Bayar_{username}_{datetime.now().strftime('%Y%m%d%H%M')}")
        bayar_ws.append_row([username, link, f"{bulan} {tahun}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        st.success("Bukti pembayaran berhasil dikirim.")

    st.markdown("---")
    st.subheader("🔧 Edit Profil")
    now = datetime.now()
    try:
        last_edit = datetime.strptime(u.get('last_edit', '2000-01-01 00:00:00'), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        last_edit = datetime(2000,1,1)

    if now - last_edit > timedelta(days=7):
        nama_lengkap = st.text_input("Nama Lengkap", value=u.get('nama_lengkap',''))
        no_hp = st.text_input("No HP", value=u.get('no_hp',''))
        foto = st.file_uploader("Upload Foto Profil", type=["jpg", "jpeg", "png"])
        new_pass = st.text_input("Ganti Password", type="password")
        if st.button("Simpan Perubahan"):
            idx = users.index(u)
            user_ws.update_cell(idx+2, 4, nama_lengkap)
            user_ws.update_cell(idx+2, 5, no_hp)
            if foto:
                link_foto = upload_to_cloudinary(foto, f"Foto_{username}")
                user_ws.update_cell(idx+2, 6, link_foto)
            if new_pass:
                hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                user_ws.update_cell(idx+2, 2, hashed)
            user_ws.update_cell(idx+2, 8, now.strftime("%Y-%m-%d %H:%M:%S"))
            st.success("Profil berhasil diperbarui.")
            st.rerun()
    else:
        sisa = (last_edit + timedelta(days=7) - now).days
        st.info(f"Anda bisa edit profil lagi dalam {sisa} hari.")

    st.markdown("---")
    st.subheader("📩 Komplain")
    isi = st.text_area("Tulis Komplain Anda")
    bukti_foto = st.file_uploader("Upload Bukti Foto (Opsional)", type=["jpg", "jpeg", "png"], key="komplain")
    if st.button("Kirim Komplain"):
        link_foto = ""
        if bukti_foto:
            link_foto = upload_to_cloudinary(bukti_foto, f"Komplain_{username}_{datetime.now().strftime('%Y%m%d%H%M')}" )
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_ws.append_row([username, isi, link_foto, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        st.success("Komplain berhasil dikirim.")

# ---------- Session State ----------

st.set_page_config(page_title="Dashboard Kost123", layout="wide")
st.title("📊 Dashboard Kost123")

if "login_status" not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""

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
