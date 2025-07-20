import streamlit as st
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
import bcrypt

def run_admin():
    st.sidebar.title("Admin Panel")
    menu = st.sidebar.radio("Menu", ["Dashboard Admin", "Kelola Kamar", "Manajemen Penyewa", "Verifikasi Booking", "Logout"])

    if menu == "Dashboard Admin":
        dashboard_admin()
    elif menu == "Kelola Kamar":
        kelola_kamar()
    elif menu == "Manajemen Penyewa":
        manajemen_penyewa()
    elif menu == "Verifikasi Booking":
        verifikasi_booking()
    elif menu == "Logout":
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.experimental_rerun()

def dashboard_admin():
    st.title("📊 Dashboard Admin")

    kamar_ws = connect_gsheet().worksheet("Kamar")
    user_ws = connect_gsheet().worksheet("User")
    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
    komplain_ws = connect_gsheet().worksheet("Komplain")

    kamar_data = kamar_ws.get_all_records()
    user_data = user_ws.get_all_records()
    pembayaran_data = pembayaran_ws.get_all_records()
    komplain_data = komplain_ws.get_all_records()

    total_kamar = len(kamar_data)
    kamar_terisi = sum(1 for k in kamar_data if k['Status'].lower() == 'terisi')
    kamar_kosong = total_kamar - kamar_terisi
    penyewa = sum(1 for u in user_data if u['role'] == 'penyewa')
    total_pemasukan = sum(int(p.get('Nominal', 0)) for p in pembayaran_data if p.get('Nominal', '').isdigit())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Kamar", total_kamar)
    col2.metric("Kamar Terisi", kamar_terisi)
    col3.metric("Kamar Kosong", kamar_kosong)
    col4.metric("Penyewa Aktif", penyewa)

    st.markdown("### 💰 Pemasukan Bulan Ini")
    st.write(f"Rp {total_pemasukan:,}")

    st.markdown("### 📢 Komplain Terbaru")
    for k in komplain_data[-5:]:
        st.write(f"{k['username']} : {k['komplain']} ({k['waktu']})")

def kelola_kamar():
    st.title("🛠️ Kelola Kamar")

    kamar_ws = connect_gsheet().worksheet("Kamar")
    data = kamar_ws.get_all_records()

    st.markdown("### Daftar Kamar")
    for k in data:
        st.markdown(f"**{k['Nama']}** - {k['Status']} - Rp{k['Harga']}")

    st.markdown("### Tambah Kamar Baru")
    nama = st.text_input("Nama Kamar")
    harga = st.number_input("Harga", min_value=0)
    deskripsi = st.text_area("Deskripsi")
    foto = st.file_uploader("Upload Foto", type=["jpg","jpeg","png"])
    if st.button("Tambah Kamar"):
        link = upload_to_cloudinary(foto, f"Kamar_{nama}") if foto else ""
        kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link])
        st.success("Kamar berhasil ditambahkan.")

def manajemen_penyewa():
    st.title("👥 Manajemen Penyewa")

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    for idx, u in enumerate(users):
        if u['role'] == 'penyewa':
            with st.expander(f"{u.get('nama_lengkap', u['username'])} - {u.get('kamar','-')}"):
                st.write(f"Nama: {u.get('nama_lengkap', u['username'])}")
                st.write(f"No HP: {u.get('no_hp', '-')}")
                st.write(f"Kamar: {u.get('kamar', '-')}")
                st.write(f"Deskripsi: {u.get('deskripsi', '-')}")

                nama = st.text_input("Nama Lengkap", value=u.get('nama_lengkap',''), key=f"nama_{idx}")
                no_hp = st.text_input("No HP", value=u.get('no_hp',''), key=f"hp_{idx}")
                deskripsi = st.text_area("Deskripsi", value=u.get('deskripsi',''), key=f"desc_{idx}")
                kamar = st.text_input("Kamar", value=u.get('kamar',''), key=f"kamar_{idx}")

                if st.button("Simpan Perubahan", key=f"simpan_{idx}"):
                    user_ws.update(f"D{idx+2}", nama)
                    user_ws.update(f"E{idx+2}", f"'{no_hp}")
                    user_ws.update(f"F{idx+2}", kamar)
                    user_ws.update(f"G{idx+2}", deskripsi)
                    st.success("Data berhasil diupdate.")

                if st.button("Reset Password", key=f"reset_{idx}"):
                    new_pass = "12345678"
                    hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                    user_ws.update(f"B{idx+2}", hashed)
                    st.warning(f"Password direset ke {new_pass}")

                if st.button("Hapus Penyewa", key=f"hapus_{idx}"):
                    user_ws.delete_rows(idx+2)
                    st.warning("Penyewa dihapus. Silakan refresh halaman.")

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
