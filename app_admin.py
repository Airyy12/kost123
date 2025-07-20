import streamlit as st
import pandas as pd
from sheets import connect_gsheet
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
    total_pemasukan = sum(int(p.get('nominal', 0)) for p in pembayaran_data if p.get('nominal', '').isdigit())

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
                    st.experimental_rerun()

                if st.button("Reset Password", key=f"reset_{idx}"):
                    new_pass = "12345678"
                    hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                    user_ws.update(f"B{idx+2}", hashed)
                    st.warning(f"Password direset ke {new_pass}")

                if st.button("Hapus Penyewa", key=f"hapus_{idx}"):
                    user_ws.delete_rows(idx+2)
                    st.warning("Penyewa dihapus. Silakan refresh halaman.")
                    st.experimental_rerun()

def manajemen_komplain():
    st.title("📢 Manajemen Komplain Interaktif")

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
                st.experimental_rerun()

def manajemen_pembayaran():
    st.title("💸 Manajemen Pembayaran")

    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
    pembayaran_data = pembayaran_ws.get_all_records()
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()

    if not pembayaran_data:
        st.info("Belum ada data pembayaran.")
        return

    for idx, p in enumerate(pembayaran_data):
        username = p.get('username', '-')
        bulan = p.get('bulan', '-')
        tahun = p.get('tahun', '-')
        nominal = p.get('nominal', '-')
        waktu = p.get('waktu', '-')
        bukti_link = p.get('bukti', '')

        with st.expander(f"{username} - {bulan} {tahun} - Rp{nominal}"):
            st.write(f"**Nama:** {username}")
            st.write(f"**Bulan/Tahun:** {bulan} / {tahun}")
            st.write(f"**Nominal:** Rp {int(nominal):,}")
            st.write(f"**Waktu Upload:** {waktu}")

            if bukti_link:
                st.image(bukti_link, caption="Bukti Pembayaran", use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Verifikasi", key=f"verif_{idx}"):
                    user_idx = next((i for i, u in enumerate(users) if u['username'] == username), None)
                    if user_idx is not None:
                        user_ws.update_cell(user_idx+2, 9, "Lunas")
                        st.success(f"Pembayaran {username} berhasil diverifikasi.")

                    pembayaran_ws.delete_rows(idx+2)
                    st.experimental_rerun()

            with col2:
                if st.button("❌ Tolak", key=f"tolak_{idx}"):
                    pembayaran_ws.delete_rows(idx+2)
                    st.warning(f"Pembayaran dari {username} telah ditolak.")
                    st.experimental_rerun()
