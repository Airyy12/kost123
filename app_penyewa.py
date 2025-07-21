import streamlit as st
from datetime import datetime, timedelta
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
import bcrypt
import requests

def run_penyewa(menu):
    if menu == "Beranda":
        penyewa_dashboard()
    elif menu == "Pembayaran":
        pembayaran()
    elif menu == "Komplain":
        komplain()
    elif menu == "Profil":
        profil_saya()
    elif menu == "Fasilitas":
        fasilitas()
    elif menu == "Logout":
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

def penyewa_dashboard():
    st.title("🏠 Dashboard Penyewa")
    
    # Custom CSS
    st.markdown("""
    <style>
    .dashboard-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
    .welcome-header {
        color: #42A5F5;
        font-size: 1.5rem;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # Load data
        user_data = load_user_data()
        pembayaran_data = load_sheet_data('pembayaran')
        kamar_data = load_sheet_data('kamar')
        
        # Info pengguna
        col1, col2 = st.columns([1,3])
        with col1:
            if user_data.get('foto_profil'):
                st.image(user_data['foto_profil'], width=120, caption="Foto Profil")
            else:
                st.image("https://via.placeholder.com/150?text=No+Photo", width=120, caption="Belum Ada Foto")
        
        with col2:
            st.markdown(f"""
            <div class="welcome-header">Selamat Datang, {user_data.get('nama_lengkap', user_data['username'])}</div>
            <div class="dashboard-card">
                <p><strong>📌 Kamar:</strong> {user_data.get('kamar', 'Belum Terdaftar')}</p>
                <p><strong>💰 Status Pembayaran:</strong> {user_data.get('status_pembayaran', 'Belum Ada Data')}</p>
                <p><strong>📅 Terdaftar Sejak:</strong> {user_data.get('tanggal_daftar', '-')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Pembayaran Terdekat
        st.markdown("### ⏳ Pembayaran Mendatang")
        today = datetime.now()
        next_month = today.replace(day=1) + timedelta(days=32)
        st.markdown(f"""
        <div class="dashboard-card">
            <p>Tagihan untuk <strong>{next_month.strftime('%B %Y')}</strong> akan jatuh tempo pada:</p>
            <h4 style="color: #FFA726;">10 {next_month.strftime('%B %Y')}</h4>
            <p>Total yang harus dibayar: <strong>Rp 1,500,000</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Aktivitas Terakhir
        st.markdown("### 📝 Aktivitas Terakhir")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="dashboard-card">
                <p><strong>🛏️ Status Kamar:</strong> Normal</p>
                <p><strong>🧹 Terakhir Dibersihkan:</strong> 2 hari lalu</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="dashboard-card">
                <p><strong>💵 Pembayaran Terakhir:</strong> 15 Mei 2023</p>
                <p><strong>📢 Komplain Terakhir:</strong> 1 minggu lalu</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown("### ⚡ Akses Cepat")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💸 Bayar Sekarang", use_container_width=True):
                st.session_state.menu = "Pembayaran"
                st.rerun()
        with col2:
            if st.button("📢 Buat Komplain", use_container_width=True):
                st.session_state.menu = "Komplain"
                st.rerun()
        with col3:
            if st.button("👤 Edit Profil", use_container_width=True):
                st.session_state.menu = "Profil"
                st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        
def pembayaran():
    st.title("💳 Pembayaran")
    
    # Custom CSS
    st.markdown("""
    <style>
    .payment-form {
        background: rgba(60,60,60,0.7);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .bank-info {
        background: rgba(30,30,30,0.9);
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        # Info rekening kos
        st.markdown("### Informasi Rekening")
        st.markdown("""
        <div class="bank-info">
            <p><strong>Bank:</strong> BCA</p>
            <p><strong>Nomor Rekening:</strong> 1234567890</p>
            <p><strong>Atas Nama:</strong> Pengelola Kos ABC</p>
            <p><strong>Nominal Transfer:</strong> Sesuai tagihan kamar</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Form pembayaran
        with st.form(key='payment_form'):
            st.markdown("### Form Pembayaran")
            
            col1, col2 = st.columns(2)
            with col1:
                bulan = st.selectbox("Bulan", [
                    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
                ])
            with col2:
                tahun = st.selectbox("Tahun", [str(y) for y in range(datetime.now().year-1, datetime.now().year+2)])
            
            nominal = st.number_input("Nominal Pembayaran (Rp)", min_value=0, value=1500000)
            bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg","jpeg","png"], help="Foto/screenshot bukti transfer")
            catatan = st.text_area("Catatan (Opsional)")
            
            if st.form_submit_button("Kirim Bukti Pembayaran"):
                if bukti is not None:
                    # Upload bukti pembayaran
                    filename = f"bayar_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    link = upload_to_cloudinary(bukti, filename)
                    
                    # Simpan ke Google Sheets
                    pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
                    pembayaran_ws.append_row([
                        st.session_state.username,
                        link,
                        bulan,
                        tahun,
                        nominal,
                        catatan,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Belum Verifikasi"
                    ])
                    
                    st.success("✅ Bukti pembayaran berhasil dikirim!")
                    st.balloons()
                else:
                    st.warning("Silakan upload bukti transfer terlebih dahulu")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def komplain():
    st.title("📢 Buat Komplain/Keluhan")
    
    try:
        with st.form(key='complaint_form'):
            jenis = st.selectbox("Jenis Keluhan", [
                "Kebersihan", "Fasilitas", "Listrik/Air", "Lainnya"
            ])
            isi = st.text_area("Deskripsi Keluhan", height=150, 
                              placeholder="Jelaskan keluhan Anda secara detail...")
            bukti = st.file_uploader("Upload Foto Pendukung (Opsional)", 
                                   type=["jpg","jpeg","png"],
                                   help="Foto yang mendukung keluhan Anda")
            
            if st.form_submit_button("Kirim Keluhan"):
                if isi.strip():
                    # Upload bukti jika ada
                    link = ""
                    if bukti:
                        filename = f"komplain_{st.session_state.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                        link = upload_to_cloudinary(bukti, filename)
                    
                    # Simpan ke Google Sheets
                    komplain_ws = connect_gsheet().worksheet("Komplain")
                    komplain_ws.append_row([
                        st.session_state.username,
                        jenis,
                        isi,
                        link,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Belum Ditanggapi"
                    ])
                    
                    st.success("✅ Keluhan Anda telah terkirim!")
                    st.toast("Admin akan menindaklanjuti keluhan Anda segera")
                else:
                    st.warning("Silakan isi deskripsi keluhan")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def fasilitas():
    st.title("🏊 Fasilitas Kos")
    
    try:
        fasilitas_data = load_sheet_data('fasilitas')
        bookings = load_sheet_data('booking_fasilitas')
        
        st.markdown("### Daftar Fasilitas")
        
        if not fasilitas_data:
            st.info("Tidak ada fasilitas tersedia")
            return
            
        for fasilitas in fasilitas_data:
            with st.expander(f"🏷️ {fasilitas['nama']}", expanded=False):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if fasilitas.get('foto'):
                        st.image(fasilitas['foto'], width=150)
                with col2:
                    st.markdown(f"""
                    <p><strong>Deskripsi:</strong> {fasilitas.get('deskripsi', '-')}</p>
                    <p><strong>Jam Operasional:</strong> {fasilitas.get('jam_buka', '-')} - {fasilitas.get('jam_tutup', '-')}</p>
                    <p><strong>Status:</strong> {fasilitas.get('status', 'Tersedia')}</p>
                    """, unsafe_allow_html=True)
                    
                    # Cek booking
                    user_bookings = [b for b in bookings if b['username'] == st.session_state.username and b['fasilitas'] == fasilitas['nama']]
                    
                    if user_bookings:
                        st.info(f"✅ Anda sudah membooking fasilitas ini pada: {user_bookings[0]['tanggal']}")
                    else:
                        if st.button("Booking Fasilitas", key=f"book_{fasilitas['nama']}"):
                            tanggal = st.date_input("Pilih Tanggal", min_value=datetime.now())
                            jam = st.time_input("Pilih Jam")
                            
                            if st.button("Konfirmasi Booking"):
                                booking_ws = connect_gsheet().worksheet("Booking_Fasilitas")
                                booking_ws.append_row([
                                    st.session_state.username,
                                    fasilitas['nama'],
                                    tanggal.strftime("%Y-%m-%d"),
                                    str(jam),
                                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "Menunggu Konfirmasi"
                                ])
                                st.success("Booking fasilitas berhasil!")
                                st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def profil_saya():
    st.title("👤 Profil Saya")
    
    # Custom CSS
    st.markdown("""
    <style>
    .profile-section {
        background: rgba(60,60,60,0.7);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .profile-header {
        color: #42A5F5;
        border-bottom: 1px solid #444;
        padding-bottom: 10px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    try:
        user_data = load_user_data()
        
        # Tampilkan profil
        st.markdown("### Informasi Profil")
        col1, col2 = st.columns([1, 3])
        with col1:
            if user_data.get('foto_profil'):
                st.image(user_data['foto_profil'], width=150, caption="Foto Profil")
            else:
                st.image("https://via.placeholder.com/150?text=No+Photo", width=150, caption="Belum Ada Foto")
        
        with col2:
            st.markdown(f"""
            <div class="profile-section">
                <div class="profile-header">Data Pribadi</div>
                <p><strong>👤 Username:</strong> {user_data['username']}</p>
                <p><strong>🪪 Nama Lengkap:</strong> {user_data.get('nama_lengkap', '-')}</p>
                <p><strong>📞 No. HP/Email:</strong> {user_data.get('no_hp', '-')}</p>
                <p><strong>🏠 Kamar:</strong> {user_data.get('kamar', '-')}</p>
                <p><strong>💰 Status Pembayaran:</strong> {user_data.get('status_pembayaran', '-')}</p>
                <p><strong>📅 Bergabung Sejak:</strong> {user_data.get('tanggal_daftar', '-')}</p>
                <p><strong>✏️ Terakhir Diubah:</strong> {user_data.get('last_edit', '-')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Informasi Kamar
        kamar_data = load_sheet_data('kamar')
        if user_data.get('kamar'):
            kamar = next((k for k in kamar_data if k['Nama'] == user_data['kamar']), None)
            if kamar:
                st.markdown("### Informasi Kamar")
                st.markdown(f"""
                <div class="profile-section">
                    <div class="profile-header">Detail Kamar</div>
                    <p><strong>🏷️ Nama Kamar:</strong> {kamar['Nama']}</p>
                    <p><strong>💵 Harga:</strong> Rp {int(kamar.get('Harga', 0)):,}/bulan</p>
                    <p><strong>📝 Deskripsi:</strong> {kamar.get('Deskripsi', '-')}</p>
                    <p><strong>🔄 Status:</strong> {kamar.get('Status', '-')}</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Form edit profil
        if st.button("✏️ Edit Profil", key="edit_profile_btn"):
            st.session_state.edit_profile = True
        
        if st.session_state.get('edit_profile'):
            with st.form(key='edit_profile_form'):
                st.markdown("### Edit Profil")
                
                col1, col2 = st.columns(2)
                with col1:
                    nama = st.text_input("Nama Lengkap", value=user_data.get('nama_lengkap', ''))
                    no_hp = st.text_input("Nomor HP/Email", value=user_data.get('no_hp', ''))
                with col2:
                    foto = st.file_uploader("Ganti Foto Profil", type=["jpg","jpeg","png"])
                
                deskripsi = st.text_area("Deskripsi Diri", value=user_data.get('deskripsi', ''))
                
                st.markdown("### Ganti Password")
                password_baru = st.text_input("Password Baru", type="password")
                konfirmasi_password = st.text_input("Konfirmasi Password", type="password")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Simpan Perubahan"):
                        if password_baru and password_baru != konfirmasi_password:
                            st.error("Password tidak cocok!")
                        else:
                            # Update data
                            user_ws = connect_gsheet().worksheet("User")
                            all_users = user_ws.get_all_values()
                            row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == st.session_state.username), None)
                            
                            if row_num:
                                # Upload foto baru jika ada
                                foto_link = user_data.get('foto_profil', '')
                                if foto:
                                    foto_link = upload_to_cloudinary(foto, f"profil_{st.session_state.username}")
                                
                                # Update data
                                updates = {
                                    4: nama,  # nama_lengkap
                                    5: no_hp,  # no_hp
                                    6: deskripsi,  # deskripsi
                                    7: foto_link,  # foto_profil
                                    8: datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # last_edit
                                }
                                
                                for col, value in updates.items():
                                    user_ws.update_cell(row_num, col, value)
                                
                                # Update password jika diisi
                                if password_baru:
                                    hashed = bcrypt.hashpw(password_baru.encode(), bcrypt.gensalt()).decode()
                                    user_ws.update_cell(row_num, 2, hashed)
                                
                                st.success("Profil berhasil diperbarui!")
                                st.session_state.edit_profile = False
                                st.rerun()
                
                with col2:
                    if st.form_submit_button("❌ Batal"):
                        st.session_state.edit_profile = False
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

# Helper function
def load_user_data():
    user_ws = connect_gsheet().worksheet("User")
    users = user_ws.get_all_records()
    return next(u for u in users if u['username'] == st.session_state.username)
