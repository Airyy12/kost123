import streamlit as st
import pandas as pd
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import re
import time

# Fungsi utilitas
def validasi_nomor_hp(nomor):
    """Validasi format nomor HP"""
    return re.match(r'^[0-9+\- ]+$', nomor) is not None

def validasi_email(email):
    """Validasi format email"""
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None

def format_rupiah(jumlah):
    """Format angka menjadi mata uang Rupiah"""
    return f"Rp {int(jumlah):,}"

def dapatkan_worksheet(nama):
    """Mendapatkan worksheet dengan penanganan error"""
    try:
        sheet = connect_gsheet()
        return sheet.worksheet(nama)
    except Exception as e:
        st.error(f"Gagal terhubung ke worksheet {nama}: {str(e)}")
        st.stop()

def konfirmasi_aksi(nama_aksi):
    """Dialog konfirmasi untuk aksi penting"""
    return st.checkbox(f"Yakin ingin {nama_aksi}?", key=f"konfirmasi_{nama_aksi}")

def tampilkan_loading(pesan):
    """Menampilkan indikator loading"""
    return st.spinner(pesan)

def handle_image_upload(uploaded_file, prefix):
    """Fungsi untuk menangani upload gambar dengan error handling"""
    if uploaded_file is None:
        return ""
    
    try:
        # Pastikan file adalah gambar
        if uploaded_file.type not in ["image/jpeg", "image/png", "image/jpg"]:
            st.error("Format file tidak didukung. Harap upload gambar JPEG atau PNG")
            return ""
            
        # Upload ke Cloudinary dengan penanganan error
        try:
            result = upload_to_cloudinary(uploaded_file, prefix)
            return result.get("secure_url", "") if result else ""
        except Exception as upload_error:
            st.error(f"Gagal mengupload gambar: {str(upload_error)}")
            return ""
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses gambar: {str(e)}")
        return ""

def safe_display_image(image_url):
    """Menampilkan gambar dengan error handling"""
    if not image_url:
        return
        
    try:
        st.image(image_url, use_column_width=True)
    except:
        st.warning("Gambar tidak dapat dimuat")
        st.text(f"URL: {image_url}")
        
# Fungsi utama admin
def jalankan_admin(menu):
    """Router menu utama admin"""
    if menu == "Dashboard Admin":
        dashboard_admin()
    elif menu == "Kelola Kamar":
        kelola_kamar()
    elif menu == "Manajemen":
        manajemen()
    elif menu == "Verifikasi Booking":
        verifikasi_booking()
    elif menu == "Profil Saya":
        profil_saya()
    elif menu == "Keluar":
        keluar()

def keluar():
    """Proses logout dengan membersihkan session"""
    for key in list(st.session_state.keys()):
        if key not in ['rerun', '_']:  # Menyimpan key internal streamlit
            del st.session_state[key]
    st.rerun()

def dashboard_admin():
    """Halaman dashboard admin"""
    st.title("📊 Dashboard Admin")
    
    try:
        with tampilkan_loading("Memuat data..."):
            # Muat semua data
            data_kamar = dapatkan_worksheet("Kamar").get_all_records()
            data_user = dapatkan_worksheet("User").get_all_records()
            data_pembayaran = dapatkan_worksheet("Pembayaran").get_all_records()
            data_komplain = dapatkan_worksheet("Komplain").get_all_records()
            
            # Hitung metrik
            total_kamar = len(data_kamar)
            kamar_terisi = sum(1 for k in data_kamar if k.get('Status', '').lower() == 'terisi')
            kamar_kosong = total_kamar - kamar_terisi
            penyewa = sum(1 for u in data_user if u.get('role') == 'penyewa')
            
            # Hitung pendapatan bulan ini
            bulan_ini = datetime.now().strftime("%B")
            tahun_ini = datetime.now().year
            pemasukan_bulan_ini = sum(
                int(p.get('nominal', 0)) for p in data_pembayaran 
                if str(p.get('nominal', '')).isdigit() and 
                   p.get('bulan') == bulan_ini and 
                   p.get('tahun') == str(tahun_ini)
        
        # Tampilkan metrik
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kamar", total_kamar)
        col2.metric("Kamar Terisi", kamar_terisi)
        col3.metric("Kamar Kosong", kamar_kosong)
        col4.metric("Penyewa Aktif", penyewa)

        st.markdown("### 💰 Pemasukan Bulan Ini")
        st.write(format_rupiah(pemasukan_bulan_ini))

        st.markdown("### 📢 Komplain Terbaru")
        if not data_komplain:
            st.info("Belum ada komplain")
        else:
            for k in sorted(data_komplain[-5:], key=lambda x: x.get('waktu', ''), reverse=True):
                status = k.get('status', 'Pending')
                warna = "green" if status.lower() == 'selesai' else "orange" if status.lower() == 'ditolak' else "gray"
                st.markdown(f"""
                **{k.get('username', 'N/A')}**  
                📅 {k.get('waktu', '')}  
                🏷️ <span style='color:{warna}'>{status}</span>  
                💬 {k.get('isi_komplain', '')[:100]}...
                """, unsafe_allow_html=True)
                
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def profil_saya():
    """Halaman profil pengguna dengan penanganan error yang lebih baik"""
    st.title("👤 Profil Saya")
    
    # Cek session login
    if 'username' not in st.session_state:
        st.error("Anda belum login. Silakan login terlebih dahulu.")
        return
    
    try:
        # Dapatkan data pengguna
        ws_user = dapatkan_worksheet("User")
        data_user = ws_user.get_all_records()
        
        # Cari index user yang login
        user_idx = next(
            (i for i, u in enumerate(data_user) 
             if u.get('username') == st.session_state.username),
            None
        )
        
        if user_idx is None:
            st.error("Profil tidak ditemukan dalam database")
            return
            
        user_data = data_user[user_idx]
        
        # Tampilkan profil dalam dua kolom
        col_profil, col_aksi = st.columns([3, 1])
        
        with col_profil:
            st.subheader("Informasi Profil")
            
            # Tampilkan foto profil dengan error handling
            if user_data.get('foto_profil'):
                try:
                    st.image(
                        user_data['foto_profil'],
                        width=200,
                        caption="Foto Profil Saat Ini",
                        use_column_width=False
                    )
                except:
                    st.warning("Gambar profil tidak dapat dimuat")
                    st.text(f"URL: {user_data['foto_profil']}")
            else:
                st.info("Belum ada foto profil")
            
            # Tampilkan data profil
            st.markdown(f"""
            **🔹 Username:** `{user_data.get('username', '-')}`  
            **🔹 Nama Lengkap:** {user_data.get('nama_lengkap', '-')}  
            **📞 Kontak:** {user_data.get('no_hp', '-')}  
            **🏠 Kamar:** {user_data.get('kamar', '-')}  
            **📝 Deskripsi:**  
            {user_data.get('deskripsi', 'Belum ada deskripsi')}
            """)
        
        with col_aksi:
            st.subheader("Aksi")
            if st.button("✏️ Edit Profil", use_container_width=True):
                st.session_state.mode_edit = True
                st.rerun()
                
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        # Mode Edit Profil
        if st.session_state.get('mode_edit', False):
            st.markdown("---")
            st.subheader("Edit Profil")
            
            with st.form("form_edit_profil"):
                # Input fields
                nama = st.text_input(
                    "Nama Lengkap*",
                    value=user_data.get('nama_lengkap', ''),
                    help="Wajib diisi"
                )
                
                kontak = st.text_input(
                    "Nomor HP/Email*",
                    value=user_data.get('no_hp', ''),
                    help="Contoh: 081234567890 atau email@contoh.com"
                )
                
                deskripsi = st.text_area(
                    "Deskripsi Diri",
                    value=user_data.get('deskripsi', ''),
                    height=100
                )
                
                foto = st.file_uploader(
                    "Upload Foto Profil Baru",
                    type=["jpg", "jpeg", "png"],
                    accept_multiple_files=False
                )
                
                st.markdown("**Ganti Password** (kosongkan jika tidak ingin mengubah)")
                password_baru = st.text_input(
                    "Password Baru",
                    type="password",
                    help="Minimal 8 karakter"
                )
                
                konfirmasi_password = st.text_input(
                    "Konfirmasi Password Baru",
                    type="password"
                )
                
                # Tombol aksi
                col_simpan, col_batal = st.columns(2)
                with col_simpan:
                    simpan = st.form_submit_button(
                        "💾 Simpan Perubahan",
                        use_container_width=True
                    )
                with col_batal:
                    if st.form_submit_button(
                        "❌ Batal",
                        use_container_width=True,
                        type="secondary"
                    ):
                        st.session_state.mode_edit = False
                        st.rerun()
                
                # Proses penyimpanan
                if simpan:
                    error_messages = []
                    
                    # Validasi input
                    if not nama:
                        error_messages.append("Nama lengkap wajib diisi")
                    
                    if not kontak:
                        error_messages.append("Kontak wajib diisi")
                    elif not (validasi_nomor_hp(kontak) or validasi_email(kontak)):
                        error_messages.append("Format kontak tidak valid (gunakan nomor HP atau email)")
                    
                    if password_baru and len(password_baru) < 8:
                        error_messages.append("Password minimal 8 karakter")
                    
                    if password_baru and (password_baru != konfirmasi_password):
                        error_messages.append("Konfirmasi password tidak cocok")
                    
                    # Tampilkan error jika ada
                    if error_messages:
                        for err in error_messages:
                            st.error(err)
                    else:
                        with st.spinner("Menyimpan perubahan..."):
                            try:
                                # Handle upload foto
                                foto_url = user_data.get('foto_profil', '')
                                if foto:
                                    foto_url = handle_image_upload(
                                        foto, 
                                        f"Profil_{st.session_state.username}"
                                    )
                                
                                # Update password jika diubah
                                if password_baru:
                                    hashed = bcrypt.hashpw(
                                        password_baru.encode(), 
                                        bcrypt.gensalt()
                                    ).decode()
                                    ws_user.update_cell(user_idx+2, 2, hashed)
                                
                                # Update data lainnya
                                updates = [
                                    (4, nama),       # nama_lengkap
                                    (5, f"'{kontak}"), # no_hp (diawali ' untuk format nomor)
                                    (6, deskripsi),   # deskripsi
                                    (7, foto_url),    # foto_profil
                                    (8, datetime.now().strftime("%Y-%m-%d %H:%M:%S")) # last_edit
                                ]
                                
                                for col, value in updates:
                                    ws_user.update_cell(user_idx+2, col, value)
                                
                                st.success("Profil berhasil diperbarui!")
                                st.session_state.mode_edit = False
                                time.sleep(1)
                                st.rerun()
                                
                            except Exception as save_error:
                                st.error(f"Gagal menyimpan perubahan: {str(save_error)}")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat profil: {str(e)}")
        st.error("Silakan refresh halaman atau coba lagi nanti")
        
def manajemen():
    """Menu manajemen utama"""
    st.title("🗂️ Manajemen")
    
    submenu = st.selectbox(
        "Pilih Submenu", 
        ["Manajemen Penyewa", "Manajemen Pembayaran", "Manajemen Komplain"],
        key="submenu_manajemen"
    )
    
    if submenu == "Manajemen Penyewa":
        manajemen_penyewa()
    elif submenu == "Manajemen Pembayaran":
        manajemen_pembayaran()
    elif submenu == "Manajemen Komplain":
        manajemen_komplain()

def manajemen_penyewa():
    """Halaman manajemen penyewa"""
    st.title("👥 Manajemen Penyewa")
    
    try:
        ws_user = dapatkan_worksheet("User")
        ws_kamar = dapatkan_worksheet("Kamar")
        
        data_user = ws_user.get_all_records()
        data_kamar = ws_kamar.get_all_records()
        penyewa = [u for u in data_user if u.get('role') == 'penyewa']
        
        if not penyewa:
            st.info("Belum ada data penyewa")
            return
            
        pencarian = st.text_input("Cari Penyewa")
        if pencarian:
            penyewa = [p for p in penyewa if pencarian.lower() in p.get('nama_lengkap', '').lower()]
        
        for idx, p in enumerate(penyewa):
            with st.expander(f"{p.get('nama_lengkap', p['username'])} - {p.get('kamar','-')}"):
                with st.form(key=f"form_{p['username']}"):
                    nama = st.text_input("Nama Lengkap", value=p.get('nama_lengkap',''))
                    kontak = st.text_input("No HP/Email", value=p.get('no_hp',''))
                    
                    # Pilihan kamar
                    opsi_kamar = [k['Nama'] for k in data_kamar]
                    kamar_sekarang = p.get('kamar','')
                    index_kamar = opsi_kamar.index(kamar_sekarang) if kamar_sekarang in opsi_kamar else 0
                    kamar = st.selectbox(
                        "Kamar", 
                        options=opsi_kamar,
                        index=index_kamar
                    )
                    
                    deskripsi = st.text_area("Deskripsi", value=p.get('deskripsi',''))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.form_submit_button("💾 Simpan"):
                            # Validasi kontak
                            if kontak and not (validasi_nomor_hp(kontak) or validasi_email(kontak)):
                                st.error("Format kontak tidak valid (harus nomor HP atau email)")
                            else:
                                with tampilkan_loading("Menyimpan..."):
                                    ws_user.update(f"D{idx+2}", nama)
                                    ws_user.update(f"E{idx+2}", f"'{kontak}")
                                    ws_user.update(f"F{idx+2}", kamar)
                                    ws_user.update(f"G{idx+2}", deskripsi)
                                st.success("Data berhasil diperbarui!")
                    with col2:
                        if st.form_submit_button("🔄 Reset Password"):
                            if konfirmasi_aksi("reset password ke default (12345678)"):
                                password_baru = "12345678"
                                hashed = bcrypt.hashpw(password_baru.encode(), bcrypt.gensalt()).decode()
                                ws_user.update(f"B{idx+2}", hashed)
                                st.warning(f"Password direset ke {password_baru}")
                    with col3:
                        if st.form_submit_button("❌ Hapus"):
                            if konfirmasi_aksi("menghapus penyewa ini"):
                                ws_user.delete_rows(idx+2)
                                st.warning("Penyewa dihapus!")
                                time.sleep(1)
                                st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def manajemen_pembayaran():
    """Halaman manajemen pembayaran"""
    st.title("💸 Manajemen Pembayaran")
    
    try:
        ws_pembayaran = dapatkan_worksheet("Pembayaran")
        ws_user = dapatkan_worksheet("User")
        
        data_pembayaran = ws_pembayaran.get_all_records()
        
        if not data_pembayaran:
            st.info("Belum ada data pembayaran")
            return
            
        # Filter
        col1, col2 = st.columns(2)
        with col1:
            filter_bulan = st.selectbox(
                "Filter Bulan",
                options=["Semua"] + ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
                index=0
            )
        with col2:
            filter_tahun = st.selectbox(
                "Filter Tahun",
                options=["Semua"] + list(range(2020, datetime.now().year + 1)),
                index=0
            )
        
        # Terapkan filter
        filtered = data_pembayaran
        if filter_bulan != "Semua":
            filtered = [p for p in filtered if p.get('bulan') == filter_bulan]
        if filter_tahun != "Semua":
            filtered = [p for p in filtered if p.get('tahun') == str(filter_tahun)]
        
        # Tampilkan pembayaran
        for idx, p in enumerate(filtered):
            username = p.get('username', '-')
            bulan = p.get('bulan', '-')
            tahun = p.get('tahun', '-')
            nominal = p.get('nominal', '0')
            waktu = p.get('waktu', '-')
            bukti_link = p.get('bukti', '')
            
            with st.expander(f"{username} - Bulan {bulan}/{tahun} - {format_rupiah(nominal)}"):
                st.markdown(f"""
                **👤 Nama:** {username}  
                **📅 Bulan/Tahun:** {bulan} / {tahun}  
                **💰 Nominal:** {format_rupiah(nominal)}  
                **🕒 Waktu Upload:** {waktu}
                """)
                
                if bukti_link:
                    st.image(bukti_link, caption="Bukti Pembayaran", use_column_width=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Verifikasi", key=f"verif_{idx}"):
                        if konfirmasi_aksi("memverifikasi pembayaran ini"):
                            data_user = ws_user.get_all_records()
                            user_idx = next(
                                (i for i, u in enumerate(data_user) 
                                 if u.get('username') == username),
                                None
                            )
                            if user_idx is not None:
                                with tampilkan_loading("Memverifikasi..."):
                                    ws_user.update_cell(user_idx+2, 10, "Lunas")  # Kolom status_pembayaran
                                    ws_pembayaran.delete_rows(idx+2)
                                    st.success("Pembayaran berhasil diverifikasi!")
                                    time.sleep(1)
                                    st.rerun()
                with col2:
                    if st.button("❌ Tolak", key=f"tolak_{idx}"):
                        if konfirmasi_aksi("menolak pembayaran ini"):
                            ws_pembayaran.delete_rows(idx+2)
                            st.warning("Pembayaran ditolak!")
                            time.sleep(1)
                            st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def manajemen_komplain():
    """Halaman manajemen komplain"""
    st.title("📢 Manajemen Komplain")
    
    try:
        ws_komplain = dapatkan_worksheet("Komplain")
        data_komplain = ws_komplain.get_all_records()
        
        if not data_komplain:
            st.info("Belum ada data komplain")
            return
            
        # Filter status
        filter_status = st.selectbox(
            "Filter Status",
            options=["Semua", "Pending", "Selesai", "Ditolak"],
            index=0
        )
        
        # Terapkan filter
        filtered = data_komplain
        if filter_status != "Semua":
            filtered = [k for k in data_komplain if k.get('status', '').lower() == filter_status.lower()]
        
        # Tampilkan komplain
        for idx, k in enumerate(filtered):
            username = k.get("username", "-")
            bulan = k.get("bulan", "-")
            tahun = k.get("tahun", "-")
            isi = k.get("isi_komplain", "-")
            foto = k.get("link_foto", "")
            status = k.get("status", "Pending").capitalize()
            
            warna_status = {
                "Pending": "orange",
                "Selesai": "green",
                "Ditolak": "red"
            }.get(status, "gray")
            
            with st.expander(f"{username} - Bulan {bulan}/{tahun} - 🏷️ <span style='color:{warna_status}'>{status}</span>", unsafe_allow_html=True):
                st.markdown(f"""
                **👤 Nama:** {username}  
                **📅 Bulan/Tahun:** {bulan} / {tahun}  
                **💬 Komplain:** {isi}
                """)
                
                if foto:
                    st.image(foto, caption="Bukti Komplain", use_column_width=True)
                
                if status == "Pending":
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Selesaikan", key=f"selesai_{idx}"):
                            if konfirmasi_aksi("menandai komplain sebagai selesai"):
                                ws_komplain.update_cell(idx + 2, 5, "Selesai")  # Kolom status
                                st.success("Komplain ditandai sebagai selesai!")
                                time.sleep(1)
                                st.rerun()
                    with col2:
                        if st.button("❌ Tolak", key=f"tolak_komplain_{idx}"):
                            if konfirmasi_aksi("menolak komplain ini"):
                                ws_komplain.update_cell(idx + 2, 5, "Ditolak")  # Kolom status
                                st.warning("Komplain ditolak!")
                                time.sleep(1)
                                st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def verifikasi_booking():
    """Halaman verifikasi booking"""
    st.title("✅ Verifikasi Booking")
    
    try:
        ws_booking = dapatkan_worksheet("Booking")
        ws_user = dapatkan_worksheet("User")
        ws_kamar = dapatkan_worksheet("Kamar")
        
        data_booking = ws_booking.get_all_records()
        data_kamar = ws_kamar.get_all_records()
        
        if not data_booking:
            st.info("Belum ada permintaan booking")
            return
            
        for idx, b in enumerate(data_booking):
            with st.expander(f"{b.get('nama', '')} - Kamar {b.get('kamar_dipilih', '')}"):
                st.markdown(f"""
                **👤 Nama:** {b.get('nama', '')}  
                **📞 Kontak:** {b.get('no_hp_email', '')}  
                **🏠 Kamar Dipilih:** {b.get('kamar_dipilih', '')}  
                **📅 Waktu Booking:** {b.get('waktu_booking', '')}
                """)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Setujui", key=f"setuju_{idx}"):
                        if konfirmasi_aksi("menyetujui booking ini"):
                            password_default = "12345678"
                            hashed = bcrypt.hashpw(password_default.encode(), bcrypt.gensalt()).decode()
                            
                            with tampilkan_loading("Memproses..."):
                                # Tambahkan user baru
                                ws_user.append_row([
                                    b['nama'], 
                                    hashed, 
                                    "penyewa", 
                                    b['kamar_dipilih'], 
                                    b['no_hp_email'],  # Simpan kontak
                                    '',  # Deskripsi
                                    '',  # Foto profil
                                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # last_edit
                                    'Belum'  # status_pembayaran
                                ])
                                
                                # Update status kamar
                                for i, k in enumerate(data_kamar):
                                    if k['Nama'] == b['kamar_dipilih']:
                                        ws_kamar.update_cell(i+2, 2, "Terisi")
                                
                                # Hapus booking
                                ws_booking.delete_rows(idx+2)
                            
                            st.success(f"{b['nama']} disetujui dengan password default 12345678")
                            time.sleep(1)
                            st.rerun()
                
                with col2:
                    if st.button("❌ Tolak", key=f"tolak_booking_{idx}"):
                        if konfirmasi_aksi("menolak booking ini"):
                            ws_booking.delete_rows(idx+2)
                            st.warning("Booking ditolak!")
                            time.sleep(1)
                            st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def profil_saya():
    """Halaman profil pengguna"""
    st.title("👤 Profil Saya")
    
    try:
        if 'username' not in st.session_state:
            st.error("Anda belum login")
            return
            
        ws_user = dapatkan_worksheet("User")
        data_user = ws_user.get_all_records()
        user_idx = next(
            (i for i, u in enumerate(data_user) 
             if u.get('username') == st.session_state.username),
            None
        )
        
        if user_idx is None:
            st.error("Profil tidak ditemukan")
            return
            
        user_data = data_user[user_idx]
        
        # Tampilkan profil
        col1, col2 = st.columns([1, 3])
        with col1:
            if user_data.get('foto_profil'):
                st.image(user_data['foto_profil'], width=150, caption="Foto Profil")
        
        with col2:
            st.markdown(f"""
            **👤 Username:** {user_data.get('username', '')}  
            **📛 Nama Lengkap:** {user_data.get('nama_lengkap', '')}  
            **📞 No HP/Email:** {user_data.get('no_hp', '')}  
            **🏠 Kamar:** {user_data.get('kamar', '-')}  
            **📝 Deskripsi Diri:** {user_data.get('deskripsi', '')}
            """)
        
        # Mode edit
        if st.button("✏️ Edit Profil"):
            st.session_state.mode_edit = True
        
        if st.session_state.get('mode_edit', False):
            st.markdown("---")
            st.subheader("Edit Profil")
            
            with st.form("form_edit_profil"):
                nama = st.text_input("Nama Lengkap", value=user_data.get('nama_lengkap', ''))
                kontak = st.text_input("No HP / Email", value=user_data.get('no_hp', ''))
                deskripsi = st.text_area("Deskripsi Diri", value=user_data.get('deskripsi', ''))
                foto = st.file_uploader("Foto Profil Baru", type=["jpg","jpeg","png"])
                password_baru = st.text_input("Password Baru (kosongkan jika tidak ingin mengubah)", type="password")
                konfirmasi_password = st.text_input("Konfirmasi Password Baru", type="password")
                
                submitted = st.form_submit_button("Simpan Perubahan")
                if submitted:
                    # Validasi input
                    errors = []
                    if kontak and not (validasi_nomor_hp(kontak) or validasi_email(kontak)):
                        errors.append("Format kontak tidak valid (harus nomor HP atau email)")
                    if password_baru and password_baru != konfirmasi_password:
                        errors.append("Konfirmasi password tidak cocok")
                    
                    if errors:
                        for error in errors:
                            st.error(error)
                    else:
                        with tampilkan_loading("Menyimpan perubahan..."):
                            # Upload foto baru jika ada
                            link_foto = user_data.get('foto_profil', '')
                            if foto:
                                link_foto = upload_to_cloudinary(foto, f"Profil_{st.session_state.username}")
                            
                            # Update password jika diubah
                            if password_baru:
                                hashed = bcrypt.hashpw(password_baru.encode(), bcrypt.gensalt()).decode()
                                ws_user.update_cell(user_idx+2, 2, hashed)
                            
                            # Update field lainnya
                            ws_user.update_cell(user_idx+2, 4, nama)  # nama_lengkap
                            ws_user.update_cell(user_idx+2, 5, f"'{kontak}")  # no_hp
                            ws_user.update_cell(user_idx+2, 6, deskripsi)  # deskripsi
                            ws_user.update_cell(user_idx+2, 7, link_foto)  # foto_profil
                            ws_user.update_cell(user_idx+2, 8, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # last_edit
                            
                            st.success("Profil berhasil diperbarui!")
                            st.session_state.mode_edit = False
                            time.sleep(1)
                            st.rerun()
                
                if st.button("Batal"):
                    st.session_state.mode_edit = False
                    st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
