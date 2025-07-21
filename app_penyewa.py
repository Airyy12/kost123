import streamlit as st
from datetime import datetime, timedelta
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
import bcrypt
import requests

def load_user_data():
    """Fungsi untuk memuat data pengguna dari Google Sheets"""
    try:
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        user = next((u for u in users if u['username'] == st.session_state.username), None)
        
        if not user:
            st.error("Data pengguna tidak ditemukan")
            return {
                'username': st.session_state.username,
                'nama_lengkap': 'Nama tidak ditemukan',
                'kamar': 'Belum terdaftar',
                'status_pembayaran': 'Tidak diketahui'
            }
        return user
    except Exception as e:
        st.error(f"Gagal memuat data pengguna: {str(e)}")
        return {}

def penyewa_dashboard():
    st.title("🏠 Dashboard Penyewa")
    
    # Pastikan user sudah login
    if 'username' not in st.session_state:
        st.error("Silakan login terlebih dahulu")
        return
    
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
        pembayaran_data = load_sheet_data('pembayaran') or []
        kamar_data = load_sheet_data('kamar') or []
        
        # Info pengguna
        col1, col2 = st.columns([1,3])
        with col1:
            if user_data.get('foto_profil'):
                st.image(user_data['foto_profil'], width=120, caption="Foto Profil")
            else:
                st.image("https://via.placeholder.com/150?text=No+Photo", width=120, caption="Belum Ada Foto")
        
        with col2:
            st.markdown(f"""
            <div class="welcome-header">Selamat Datang, {user_data.get('nama_lengkap', user_data.get('username', 'Pengguna'))}</div>
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

def run_penyewa(menu):
    """Fungsi utama untuk navigasi menu penyewa"""
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
