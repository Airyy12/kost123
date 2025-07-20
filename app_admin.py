import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
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
import streamlit as st
import pandas as pd
from datetime import datetime

def admin_dashboard():
    st.title("📊 Dashboard Admin")

    # Load semua data
    df_komplain = load_sheet_data('komplain')
    df_booking = load_sheet_data('booking')
    df_pembayaran = load_sheet_data('pembayaran')

    # Pastikan tidak ada kolom yang salah format
    for df in [df_komplain, df_booking, df_pembayaran]:
        df.columns = df.columns.str.strip()

    st.markdown("### 🛠️ Komplain Terbaru")
    if df_komplain.empty:
        st.info("Belum ada komplain.")
    else:
        komplain_terbaru = df_komplain.sort_values("waktu", ascending=False).head(5)
        for _, row in komplain_terbaru.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color:#fef3c7; padding:10px; border-radius:10px; margin-bottom:10px;">
                    <strong>📅 {row['waktu']}</strong><br>
                    🧑 <strong>{row['nama']}</strong><br>
                    📝 {row['isi_komplain']}
                </div>
                """, unsafe_allow_html=True)

    st.markdown("### 📝 Booking Terbaru")
    if df_booking.empty:
        st.info("Belum ada data booking.")
    else:
        booking_terbaru = df_booking.sort_values("waktu_booking", ascending=False).head(5)
        for _, b in booking_terbaru.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color:#dbeafe; padding:10px; border-radius:10px; margin-bottom:10px;">
                    <strong>📅 {b['waktu_booking']}</strong><br>
                    🧑 <strong>{b['nama']}</strong> memesan kamar <strong>{b['kamar_dipilih']}</strong>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("### 💵 Pembayaran Terbaru")
    if df_pembayaran.empty:
        st.info("Belum ada data pembayaran.")
    else:
        pembayaran_terbaru = df_pembayaran.sort_values("waktu", ascending=False).head(5)
        for _, p in pembayaran_terbaru.iterrows():
            with st.container():
                st.markdown(f"""
                <div style="background-color:#dcfce7; padding:10px; border-radius:10px; margin-bottom:10px;">
                    <strong>📅 {p['waktu']}</strong><br>
                    🧑 <strong>{p['username']}</strong> 
                    💸 Total: Rp {p['jumlah_bayar']}
                </div>
                """, unsafe_allow_html=True)

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

    submenu = st.selectbox("Pilih Submenu", ["Manajemen Penyewa", "Manajemen Pembayaran", "Manajemen Komplain"])

    if submenu == "Manajemen Penyewa":
        manajemen_penyewa()
    elif submenu == "Manajemen Pembayaran":
        manajemen_pembayaran()
    elif submenu == "Manajemen Komplain":
        manajemen_komplain()

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

def manajemen_komplain():
    st.title("📢 Manajemen Komplain")

    komplain_ws = connect_gsheet().worksheet("Komplain")
    komplain_data = komplain_ws.get_all_records()

    if not komplain_data:
        st.info("Belum ada data komplain.")
        return

    for idx, k in enumerate(komplain_data):
        username = k.get('username', '-')
        isi_komplain = k.get('isi_komplain', '-')
        waktu = k.get('waktu', '-')
        link_foto = k.get('link_foto', '')

        with st.expander(f"{username} - {waktu}"):
            st.write(f"**Isi Komplain:** {isi_komplain}")
            if link_foto:
                st.image(link_foto, caption="Bukti Foto", use_container_width=True)

            if st.button("Hapus Komplain Ini", key=f"hapus_{idx}"):
                komplain_ws.delete_rows(idx + 2)
                st.warning("Komplain telah dihapus.")
                st.rerun()

import requests

def manajemen_pembayaran():
    st.title("💸 Manajemen Pembayaran")

    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
    pembayaran_data = pembayaran_ws.get_all_records()

    if not pembayaran_data:
        st.info("Belum ada data pembayaran.")
        return

    for idx, p in enumerate(pembayaran_data):
        username = p.get('username', '-')
        bulan = p.get('bulan', '-')
        tahun = p.get('tahun', '-')
        nominal = p.get('nominal', '0')
        waktu = p.get('waktu', '-')
        bukti_link = p.get('bukti', '')

        with st.expander(f"{username} - {bulan} {tahun} - Rp{nominal}"):
            st.write(f"**Nama:** {username}")
            st.write(f"**Bulan/Tahun:** {bulan}/{tahun}")
            st.write(f"**Nominal:** Rp {int(nominal):,}")
            st.write(f"**Waktu Upload:** {waktu}")

            if bukti_link:
                try:
                    response = requests.get(bukti_link, timeout=5)
                    if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                        st.image(bukti_link, caption="Bukti Pembayaran", use_container_width=True)
                    else:
                        st.warning("❗ Gagal menampilkan gambar: URL tidak valid atau bukan file gambar.")
                except Exception as e:
                    st.warning(f"❗ Gagal memuat gambar bukti: {e}")
            else:
                st.info("Tidak ada bukti pembayaran yang diunggah.")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("✅ Verifikasi", key=f"verif_{idx}"):
                    user_ws = connect_gsheet().worksheet("User")
                    users = user_ws.get_all_records()
                    user_idx = next((i for i, u in enumerate(users) if u['username'] == username), None)

                    if user_idx is not None:
                        user_ws.update_cell(user_idx + 2, 9, "Lunas")
                        st.success(f"Pembayaran dari {username} berhasil diverifikasi.")

                    pembayaran_ws.delete_rows(idx + 2)
                    st.rerun()

            with col2:
                if st.button("❌ Tolak", key=f"tolak_{idx}"):
                    pembayaran_ws.delete_rows(idx + 2)
                    st.warning(f"Pembayaran dari {username} ditolak.")
                    st.rerun()

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
    if 'profil_submenu' not in st.session_state:
        st.session_state.profil_submenu = None

    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    idx = next(i for i, u in enumerate(users) if u['username'] == st.session_state.username)
    user_data = users[idx]

    st.header("👤 Profil Saya")

    col1, col2 = st.columns([1,3])

    with col1:
        if user_data.get('foto_profil'):
            st.image(user_data['foto_profil'], width=100, caption="Foto Profil")

    with col2:
        st.markdown(f"""
        <p><strong>Username:</strong> {user_data['username']}</p>
        <p><strong>Nama Lengkap:</strong> {user_data.get('nama_lengkap','')}</p>
        <p><strong>Nomor HP/Email:</strong> {user_data.get('no_hp','')}</p>
        <p><strong>Kamar:</strong> {user_data.get('kamar','-')}</p>
        <p><strong>Deskripsi:</strong> {user_data.get('deskripsi','')}</p>
        """, unsafe_allow_html=True)

    if st.button("Edit Profil"):
        st.session_state.profil_submenu = "edit_profil"

    if st.session_state.profil_submenu == "edit_profil":
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
                st.session_state.profil_submenu = None
        else:
            st.warning("Edit profil hanya bisa dilakukan 1x dalam seminggu.")
