import streamlit as st
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime
import bcrypt

def run_admin(menu):
    if menu == "Dashboard Admin":
        admin_dashboard()
    elif menu == "Kelola Kamar":
        kelola_kamar()
    elif menu == "Manajemen":
        manajemen()
    elif menu == "Verifikasi Booking":
        verifikasi_booking()
    elif menu == "Profil Saya":
        profil_saya()
    elif menu == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def admin_dashboard():
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
        st.write(f"{k['username']} : {k['isi_komplain']} ({k['waktu']})")

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

def manajemen():
    st.title("🗂️ Manajemen")

    submenu = st.selectbox("Pilih Submenu", ["Manajemen Penyewa", "Manajemen Laporan"])

    if submenu == "Manajemen Penyewa":
        manajemen_penyewa()
    elif submenu == "Manajemen Laporan":
        manajemen_laporan()
import pandas as pd

def manajemen_laporan():
    st.header("📄 Manajemen Laporan")

    sheet_names = ["User", "Pembayaran", "Komplain", "Booking"]

    for sheet in sheet_names:
        st.subheader(f"Laporan {sheet}")

        ws = connect_gsheet().worksheet(sheet)
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        st.dataframe(df)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"Download {sheet}.csv",
            data=csv,
            file_name=f"{sheet.lower()}_laporan.csv",
            mime='text/csv'
        )

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

def profil_saya():
    if 'submenu' not in st.session_state:
        st.session_state.submenu = None
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = next(i for i,u in enumerate(users) if u['username']==st.session_state.username)
    user_data = users[idx]

    st.header("👤 Profil Saya")

    col1, col2 = st.columns([1,3])

    with col1:
        if user_data.get('foto_profil'):
            st.image(user_data['foto_profil'], width=100, caption="Foto Profil")

    with col2:
        st.markdown(f"""
        <p><span class="label-align">Username:</span> {user_data['username']}</p>
        <p><span class="label-align">Nama Lengkap:</span> {user_data.get('nama_lengkap','')}</p>
        <p><span class="label-align">Nomor HP/Email:</span> {user_data.get('no_hp','')}</p>
        <p><span class="label-align">Kamar:</span> {user_data.get('kamar','-')}</p>
        <p><span class="label-align">Deskripsi Diri:</span> {user_data.get('deskripsi','')}</p>
        """, unsafe_allow_html=True)

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
            deskripsi = st.text_area("Deskripsi Diri", value=user_data.get('deskripsi',''))
            foto = st.file_uploader("Foto Profil", type=["jpg","jpeg","png"])
            new_password = st.text_input("Ganti Password (Opsional)", type="password")

            if st.button("Simpan Perubahan"):
                link = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}") if foto else user_data.get('foto_profil','')
                user_ws.update_cell(idx+2, 4, nama)
                user_ws.update_cell(idx+2, 5, f"'{kontak}")
                user_ws.update_cell(idx+2, 6, deskripsi)
                user_ws.update_cell(idx+2, 7, link)
                user_ws.update_cell(idx+2, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                if new_password:
                    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                    user_ws.update_cell(idx+2, 2, hashed)
                st.success("Profil berhasil diperbarui.")
                st.session_state.submenu = None
        else:
            st.warning("Edit profil hanya bisa dilakukan 1x dalam seminggu.")

