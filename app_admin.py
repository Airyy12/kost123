import streamlit as st
import pandas as pd
from sheets import connect_gsheet
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import re
import time
import logging
from typing import List, Dict, Optional, Tuple

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konstanta konfigurasi
class Config:
    DEFAULT_PASSWORD = "12345678"
    SUPPORTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
    PASSWORD_MIN_LENGTH = 8
    CACHE_TTL = 300  # 5 menit
    
class DatabaseColumns:
    """Mapping kolom database untuk menghindari magic numbers"""
    class User:
        USERNAME = 1
        PASSWORD = 2
        ROLE = 3
        NAMA_LENGKAP = 4
        NO_HP = 5
        KAMAR = 6
        DESKRIPSI = 7
        FOTO_PROFIL = 8
        LAST_EDIT = 9
        STATUS_PEMBAYARAN = 10
    
    class Kamar:
        NAMA = 1
        STATUS = 2
        HARGA = 3
        DESKRIPSI = 4
        FOTO = 5
    
    class Pembayaran:
        USERNAME = 1
        BULAN = 2
        TAHUN = 3
        NOMINAL = 4
        WAKTU = 5
        BUKTI = 6
    
    class Komplain:
        USERNAME = 1
        BULAN = 2
        TAHUN = 3
        ISI_KOMPLAIN = 4
        STATUS = 5
        LINK_FOTO = 6
        WAKTU = 7

# Cache untuk data worksheet
@st.cache_data(ttl=Config.CACHE_TTL)
def get_cached_worksheet_data(sheet_name: str) -> List[Dict]:
    """Mendapatkan data worksheet dengan caching"""
    try:
        sheet = connect_gsheet()
        worksheet = sheet.worksheet(sheet_name)
        data = worksheet.get_all_records()
        logger.info(f"Cache updated for worksheet: {sheet_name}")
        return data
    except Exception as e:
        logger.error(f"Error getting cached data for {sheet_name}: {str(e)}")
        raise

# Fungsi utilitas yang diperbaiki
class Validator:
    """Kelas untuk semua validasi input"""
    
    @staticmethod
    def validasi_nomor_hp(nomor: str) -> bool:
        """Validasi format nomor HP"""
        if not nomor:
            return False
        return re.match(r'^[0-9+\- ]+$', nomor) is not None

    @staticmethod
    def validasi_email(email: str) -> bool:
        """Validasi format email"""
        if not email:
            return False
        return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None
    
    @staticmethod
    def validate_user_data(nama: str, kontak: str, password: str = None) -> List[str]:
        """Validasi data pengguna dengan error messages"""
        errors = []
        
        if not nama or nama.strip() == "":
            errors.append("Nama lengkap wajib diisi")
        
        if not kontak or kontak.strip() == "":
            errors.append("Kontak wajib diisi")
        elif not (Validator.validasi_nomor_hp(kontak) or Validator.validasi_email(kontak)):
            errors.append("Format kontak tidak valid (gunakan nomor HP atau email)")
        
        if password:
            if len(password) < Config.PASSWORD_MIN_LENGTH:
                errors.append(f"Password minimal {Config.PASSWORD_MIN_LENGTH} karakter")
        
        return errors

class DatabaseHelper:
    """Helper class untuk operasi database"""
    
    @staticmethod
    def dapatkan_worksheet(nama: str):
        """Mendapatkan worksheet dengan penanganan error"""
        try:
            sheet = connect_gsheet()
            return sheet.worksheet(nama)
        except Exception as e:
            logger.error(f"Failed to connect to worksheet {nama}: {str(e)}")
            st.error(f"Gagal terhubung ke worksheet {nama}: {str(e)}")
            st.stop()
    
    @staticmethod
    def update_user_field(username: str, column: int, value: str) -> bool:
        """Update field user berdasarkan username"""
        try:
            ws_user = DatabaseHelper.dapatkan_worksheet("User")
            data_user = ws_user.get_all_records()
            
            user_idx = next(
                (i for i, u in enumerate(data_user) 
                 if u.get('username') == username),
                None
            )
            
            if user_idx is not None:
                ws_user.update_cell(user_idx + 2, column, value)
                logger.info(f"Updated user {username} column {column}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating user field: {str(e)}")
            return False
    
    @staticmethod
    def get_user_by_username(username: str) -> Tuple[Optional[Dict], Optional[int]]:
        """Mendapatkan data user berdasarkan username"""
        try:
            data_user = get_cached_worksheet_data("User")
            user_idx = next(
                (i for i, u in enumerate(data_user) 
                 if u.get('username') == username),
                None
            )
            
            if user_idx is not None:
                return data_user[user_idx], user_idx
            return None, None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None, None

class UIHelper:
    """Helper class untuk UI components"""
    
    @staticmethod
    def format_rupiah(jumlah: int) -> str:
        """Format angka menjadi mata uang Rupiah"""
        try:
            return f"Rp {int(jumlah):,}"
        except (ValueError, TypeError):
            return f"Rp 0"

    @staticmethod
    def konfirmasi_aksi(nama_aksi: str) -> bool:
        """Dialog konfirmasi untuk aksi penting"""
        return st.checkbox(f"Yakin ingin {nama_aksi}?", key=f"konfirmasi_{nama_aksi}_{int(time.time())}")

    @staticmethod
    def tampilkan_loading(pesan: str):
        """Menampilkan indikator loading"""
        return st.spinner(pesan)

    @staticmethod
    def safe_display_image(image_url: str):
        """Menampilkan gambar dengan error handling"""
        if not image_url:
            return
            
        try:
            st.image(image_url, use_column_width=True)
        except Exception as e:
            logger.warning(f"Image display failed: {str(e)}")
            st.warning("Gambar tidak dapat dimuat")
            st.text(f"URL: {image_url}")

class ImageHandler:
    """Handler untuk upload dan display gambar"""
    
    @staticmethod
    def handle_image_upload(uploaded_file, prefix: str) -> str:
        """Fungsi untuk menangani upload gambar dengan error handling"""
        if uploaded_file is None:
            return ""
        
        try:
            # Pastikan file adalah gambar
            if uploaded_file.type not in Config.SUPPORTED_IMAGE_TYPES:
                st.error("Format file tidak didukung. Harap upload gambar JPEG atau PNG")
                return ""
            
            # Upload ke Cloudinary dengan penanganan error
            try:
                result = upload_to_cloudinary(uploaded_file, prefix)
                url = result.get("secure_url", "") if result else ""
                if url:
                    logger.info(f"Image uploaded successfully: {prefix}")
                return url
            except Exception as upload_error:
                logger.error(f"Cloudinary upload failed: {str(upload_error)}")
                st.error(f"Gagal mengupload gambar: {str(upload_error)}")
                return ""
                
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            st.error(f"Terjadi kesalahan saat memproses gambar: {str(e)}")
            return ""

# Fungsi utama admin yang diperbaiki
def jalankan_admin(menu: str):
    """Router menu utama admin"""
    logger.info(f"Admin {st.session_state.get('username', 'unknown')} accessed: {menu}")
    
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
    username = st.session_state.get('username', 'unknown')
    logger.info(f"User {username} logged out")
    
    try:
        for key in list(st.session_state.keys()):
            if key not in ['rerun', '_']:  # Menyimpan key internal streamlit
                del st.session_state[key]
        st.rerun()
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        # Force clear session state
        st.session_state.clear()
        st.rerun()

def dashboard_admin():
    """Halaman dashboard admin yang diperbaiki"""
    st.title("📊 Dashboard Admin")
    
    try:
        with UIHelper.tampilkan_loading("Memuat data dashboard..."):
            # Muat semua data dengan caching
            data_kamar = get_cached_worksheet_data("Kamar")
            data_user = get_cached_worksheet_data("User")
            data_pembayaran = get_cached_worksheet_data("Pembayaran")
            data_komplain = get_cached_worksheet_data("Komplain")
            
            # Hitung metrik dengan error handling
            total_kamar = len(data_kamar)
            kamar_terisi = sum(1 for k in data_kamar if k.get('Status', '').lower() == 'terisi')
            kamar_kosong = total_kamar - kamar_terisi
            penyewa = sum(1 for u in data_user if u.get('role') == 'penyewa')
            
            # Hitung pendapatan bulan ini
            bulan_ini = datetime.now().strftime("%B")
            tahun_ini = str(datetime.now().year)
            
            pemasukan_bulan_ini = 0
            for p in data_pembayaran:
                try:
                    nominal = p.get('nominal', '0')
                    if str(nominal).replace('.', '').isdigit():
                        if p.get('bulan') == bulan_ini and p.get('tahun') == tahun_ini:
                            pemasukan_bulan_ini += int(float(str(nominal)))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid payment amount: {nominal}")
                    continue
        
        # Tampilkan metrik dalam card layout
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Kamar", total_kamar)
        with col2:
            st.metric("Kamar Terisi", kamar_terisi)
        with col3:
            st.metric("Kamar Kosong", kamar_kosong)
        with col4:
            st.metric("Penyewa Aktif", penyewa)

        # Pemasukan section
        st.markdown("### 💰 Pemasukan Bulan Ini")
        st.write(UIHelper.format_rupiah(pemasukan_bulan_ini))

        # Komplain terbaru section
        st.markdown("### 📢 Komplain Terbaru")
        if not data_komplain:
            st.info("Belum ada komplain")
        else:
            # Sort dan ambil 5 terbaru
            komplain_terbaru = sorted(
                data_komplain, 
                key=lambda x: x.get('waktu', ''), 
                reverse=True
            )[:5]
            
            for k in komplain_terbaru:
                status = k.get('status', 'Pending')
                warna_map = {
                    'selesai': 'green',
                    'ditolak': 'red',
                    'pending': 'orange'
                }
                warna = warna_map.get(status.lower(), 'gray')
                
                isi_preview = k.get('isi_komplain', '')[:100]
                if len(k.get('isi_komplain', '')) > 100:
                    isi_preview += "..."
                
                st.markdown(f"""
                **{k.get('username', 'N/A')}**  
                📅 {k.get('waktu', '')}  
                🏷️ <span style='color:{warna}'>{status}</span>  
                💬 {isi_preview}
                """, unsafe_allow_html=True)
                st.markdown("---")
                
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        st.error(f"Terjadi kesalahan saat memuat dashboard: {str(e)}")
        if st.button("🔄 Refresh Dashboard"):
            st.cache_data.clear()
            st.rerun()

def profil_saya():
    """Halaman profil pengguna - SINGLE DEFINITION"""
    st.title("👤 Profil Saya")
    
    # Cek session login
    if 'username' not in st.session_state:
        st.error("Anda belum login. Silakan login terlebih dahulu.")
        return
    
    username = st.session_state.username
    logger.info(f"User {username} accessing profile")
    
    try:
        # Dapatkan data pengguna
        user_data, user_idx = DatabaseHelper.get_user_by_username(username)
        
        if user_data is None:
            st.error("Profil tidak ditemukan dalam database")
            return
        
        # Tampilkan profil dalam layout yang lebih baik
        col_profil, col_aksi = st.columns([3, 1])
        
        with col_profil:
            st.subheader("Informasi Profil")
            
            # Tampilkan foto profil dengan error handling
            foto_url = user_data.get('foto_profil', '')
            if foto_url:
                try:
                    st.image(
                        foto_url,
                        width=200,
                        caption="Foto Profil Saat Ini"
                    )
                except Exception as img_error:
                    logger.warning(f"Profile image display failed: {str(img_error)}")
                    st.warning("Gambar profil tidak dapat dimuat")
                    st.text(f"URL: {foto_url}")
            else:
                st.info("Belum ada foto profil")
            
            # Tampilkan data profil
            st.markdown(f"""
            **🔹 Username:** `{user_data.get('username', '-')}`  
            **🔹 Nama Lengkap:** {user_data.get('nama_lengkap', '-')}  
            **📞 Kontak:** {user_data.get('no_hp', '-')}  
            **🏠 Kamar:** {user_data.get('kamar', '-')}  
            **👤 Role:** {user_data.get('role', '-').title()}  
            **📝 Deskripsi:**  
            {user_data.get('deskripsi', 'Belum ada deskripsi')}
            """)
        
        with col_aksi:
            st.subheader("Aksi")
            if st.button("✏️ Edit Profil", use_container_width=True):
                st.session_state.mode_edit = True
                st.rerun()
                
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # Mode Edit Profil
        if st.session_state.get('mode_edit', False):
            _render_edit_profile_form(user_data, user_idx)
        
    except Exception as e:
        logger.error(f"Profile error for {username}: {str(e)}")
        st.error(f"Terjadi kesalahan saat memuat profil: {str(e)}")
        st.error("Silakan refresh halaman atau coba lagi nanti")

def _render_edit_profile_form(user_data: Dict, user_idx: int):
    """Render form edit profil - Helper function"""
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
            help=f"Minimal {Config.PASSWORD_MIN_LENGTH} karakter"
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
            _process_profile_update(
                user_data, user_idx, nama, kontak, deskripsi, 
                foto, password_baru, konfirmasi_password
            )

def _process_profile_update(user_data: Dict, user_idx: int, nama: str, 
                          kontak: str, deskripsi: str, foto, 
                          password_baru: str, konfirmasi_password: str):
    """Process profile update - Helper function"""
    # Validasi input
    error_messages = Validator.validate_user_data(nama, kontak, password_baru)
    
    if password_baru and (password_baru != konfirmasi_password):
        error_messages.append("Konfirmasi password tidak cocok")
    
    # Tampilkan error jika ada
    if error_messages:
        for err in error_messages:
            st.error(err)
        return
    
    # Proses update
    with UIHelper.tampilkan_loading("Menyimpan perubahan..."):
        try:
            ws_user = DatabaseHelper.dapatkan_worksheet("User")
            
            # Handle upload foto
            foto_url = user_data.get('foto_profil', '')
            if foto:
                foto_url = ImageHandler.handle_image_upload(
                    foto, 
                    f"Profil_{st.session_state.username}"
                )
            
            # Update password jika diubah
            if password_baru:
                hashed = bcrypt.hashpw(
                    password_baru.encode(), 
                    bcrypt.gensalt()
                ).decode()
                ws_user.update_cell(user_idx + 2, DatabaseColumns.User.PASSWORD, hashed)
            
            # Update data lainnya menggunakan konstanta
            updates = [
                (DatabaseColumns.User.NAMA_LENGKAP, nama),
                (DatabaseColumns.User.NO_HP, f"'{kontak}"),  # Prefix ' untuk format nomor
                (DatabaseColumns.User.DESKRIPSI, deskripsi),
                (DatabaseColumns.User.FOTO_PROFIL, foto_url),
                (DatabaseColumns.User.LAST_EDIT, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            ]
            
            for col, value in updates:
                ws_user.update_cell(user_idx + 2, col, value)
            
            logger.info(f"Profile updated for user: {st.session_state.username}")
            st.success("Profil berhasil diperbarui!")
            st.session_state.mode_edit = False
            
            # Clear cache untuk refresh data
            st.cache_data.clear()
            time.sleep(1)
            st.rerun()
            
        except Exception as save_error:
            logger.error(f"Profile update error: {str(save_error)}")
            st.error(f"Gagal menyimpan perubahan: {str(save_error)}")

def manajemen():
    """Menu manajemen utama yang diperbaiki"""
    st.title("🗂️ Manajemen")
    
    submenu = st.selectbox(
        "Pilih Submenu", 
        ["Manajemen Penyewa", "Manajemen Pembayaran", "Manajemen Komplain"],
        key="submenu_manajemen"
    )
    
    logger.info(f"Admin accessing submenu: {submenu}")
    
    try:
        if submenu == "Manajemen Penyewa":
            manajemen_penyewa()
        elif submenu == "Manajemen Pembayaran":
            manajemen_pembayaran()
        elif submenu == "Manajemen Komplain":
            manajemen_komplain()
    except Exception as e:
        logger.error(f"Management submenu error: {str(e)}")
        st.error(f"Terjadi kesalahan: {str(e)}")

def manajemen_penyewa():
    """Halaman manajemen penyewa yang diperbaiki"""
    st.title("👥 Manajemen Penyewa")
    
    try:
        # Load data dengan caching
        data_user = get_cached_worksheet_data("User")
        data_kamar = get_cached_worksheet_data("Kamar")
        
        penyewa = [u for u in data_user if u.get('role') == 'penyewa']
        
        if not penyewa:
            st.info("Belum ada data penyewa")
            return
        
        # Search functionality
        pencarian = st.text_input("🔍 Cari Penyewa (nama atau kamar)")
        if pencarian:
            pencarian_lower = pencarian.lower()
            penyewa = [p for p in penyewa 
                      if pencarian_lower in p.get('nama_lengkap', '').lower() or
                         pencarian_lower in p.get('kamar', '').lower()]
        
        st.write(f"Menampilkan {len(penyewa)} penyewa")
        
        # Display penyewa
        for idx, p in enumerate(penyewa):
            username = p.get('username', '')
            nama = p.get('nama_lengkap', username)
            kamar = p.get('kamar', '-')
            
            with st.expander(f"👤 {nama} - 🏠 {kamar}"):
                _render_penyewa_management_form(p, idx, data_kamar)
    
    except Exception as e:
        logger.error(f"Penyewa management error: {str(e)}")
        st.error(f"Terjadi kesalahan: {str(e)}")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()

def _render_penyewa_management_form(penyewa_data: Dict, idx: int, data_kamar: List[Dict]):
    """Render form manajemen penyewa - Helper function"""
    username = penyewa_data.get('username', '')
    
    with st.form(key=f"form_penyewa_{username}_{idx}"):
        col1, col2 = st.columns(2)
        
        with col1:
            nama = st.text_input(
                "Nama Lengkap", 
                value=penyewa_data.get('nama_lengkap', ''),
                key=f"nama_{username}_{idx}"
            )
            kontak = st.text_input(
                "No HP/Email", 
                value=penyewa_data.get('no_hp', ''),
                key=f"kontak_{username}_{idx}"
            )
        
        with col2:
            # Pilihan kamar
            opsi_kamar = [""] + [k.get('Nama', '') for k in data_kamar if k.get('Nama')]
            kamar_sekarang = penyewa_data.get('kamar', '')
            
            try:
                index_kamar = opsi_kamar.index(kamar_sekarang) if kamar_sekarang in opsi_kamar else 0
            except ValueError:
                index_kamar = 0
            
            kamar = st.selectbox(
                "Kamar", 
                options=opsi_kamar,
                index=index_kamar,
                key=f"kamar_{username}_{idx}"
            )
        
        deskripsi = st.text_area(
            "Deskripsi", 
            value=penyewa_data.get('deskripsi', ''),
            key=f"desc_{username}_{idx}"
        )
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.form_submit_button("💾 Simpan", use_container_width=True):
                _process_penyewa_update(username, nama, kontak, kamar, deskripsi)
        
        with col2:
            if st.form_submit_button("🔄 Reset Password", use_container_width=True):
                _process_password_reset(username)
        
        with col3:
            if st.form_submit_button("❌ Hapus", use_container_width=True):
                _process_penyewa_deletion(username)

def _process_penyewa_update(username: str, nama: str, kontak: str, kamar: str, deskripsi: str):
    """Process penyewa update - Helper function"""
    # Validasi
    errors = Validator.validate_user_data(nama, kontak)
    if errors:
        for error in errors:
            st.error(error)
        return
    
    try:
        with UIHelper.tampilkan_loading("Menyimpan perubahan..."):
            ws_user = DatabaseHelper.dapatkan_worksheet("User")
            data_user = ws_user.get_all_records()
            
            user_idx = next(
                (i for i, u in enumerate(data_user) if u.get('username') == username),
                None
            )
            
            if user_idx is not None:
                # Update menggunakan konstanta
                updates = [
                    (DatabaseColumns.User.NAMA_LENGKAP, nama),
                    (DatabaseColumns.User.NO_HP, f"'{kontak}"),
                    (DatabaseColumns.User.KAMAR, kamar),
                    (DatabaseColumns.User.DESKRIPSI, deskripsi),
                    (DatabaseColumns.User.LAST_EDIT, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                ]
                
                for col, value in updates:
                    ws_user.update_cell(user_idx + 2, col, value)
                
                st.cache_data.clear()  # Clear cache
                st.success("Data penyewa berhasil diperbarui!")
                logger.info(f"Penyewa {username} updated by admin")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Data penyewa tidak ditemukan")
    
    except Exception as e:
        logger.error(f"Penyewa update error: {str(e)}")
        st.error(f"Gagal memperbarui data: {str(e)}")

def _process_password_reset(username: str):
    """Process password reset - Helper function"""
    if UIHelper.konfirmasi_aksi(f"reset password {username} ke default ({Config.DEFAULT_PASSWORD})"):
        try:
            hashed = bcrypt.hashpw(Config.DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
            if DatabaseHelper.update_user_field(username, DatabaseColumns.User.PASSWORD, hashed):
                st.success(f"Password {username} berhasil direset ke: {Config.DEFAULT_PASSWORD}")
                logger.info(f"Password reset for user: {username}")
            else:
                st.error("Gagal mereset password")
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            st.error(f"Gagal mereset password: {str(e)}")

def _process_penyewa_deletion(username: str):
    """Process penyewa deletion - Helper function"""
    if UIHelper.konfirmasi_aksi(f"menghapus penyewa {username} secara permanen"):
        try:
            ws_user = DatabaseHelper.dapatkan_worksheet("User")
            data_user = ws_user.get_all_records()
            
            user_idx = next(
                (i for i, u in enumerate(data_user) if u.get('username') == username),
                None
            )
            
            if user_idx is not None:
                ws_user.delete_rows(user_idx + 2)
                st.cache_data
