import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# ======================== CSS Kustom ========================
st.markdown("""
<style>
    /* Font & Warna Utama */
    :root {
        --primary: #4a6bff;
        --secondary: #6c757d;
        --success: #28a745;
        --warning: #ffc107;
        --danger: #dc3545;
        --light: #f8f9fa;
        --dark: #343a40;
    }
    
    /* Card Modern */
    .card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
        transition: transform 0.2s;
    }
    .card:hover {
        transform: translateY(-2px);
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #4a6bff, #6a8eff);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    /* Status */
    .status-pending { color: var(--warning); font-weight: 600; }
    .status-verified { color: var(--success); font-weight: 600; }
    .status-ditolak { color: var(--danger); font-weight: 600; }
    .status-terkirim { color: var(--primary); font-weight: 600; }
    
    /* Notifikasi */
    .notif-success {
        background-color: #d4edda;
        color: #155724;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ======================== Fungsi Bantuan (Mock) ========================
# Fungsi ini diganti dengan implementasi asli Anda
def connect_gsheet():
    return None

def load_sheet_data(sheet_name):
    # Data dummy untuk testing
    if sheet_name == "User":
        return pd.DataFrame([{
            'username': 'user1',
            'nama_lengkap': 'John Doe',
            'no_hp': '08123456789',
            'kamar': 'A1',
            'status_pembayaran': 'Lunas',
            'foto_profil': 'https://via.placeholder.com/150',
            'deskripsi': 'Penyewa baru',
            'last_edit': datetime.now().isoformat()
        }])
    elif sheet_name == "Kamar":
        return pd.DataFrame([{
            'Nama': 'A1',
            'Status': 'Terisi',
            'Harga': 1500000,
            'Deskripsi': 'Kamar luas dengan AC',
            'link_foto': 'https://via.placeholder.com/300'
        }])
    elif sheet_name == "Pembayaran":
        return pd.DataFrame([{
            'username': 'user1',
            'bukti': 'https://via.placeholder.com/300',
            'bulan': 'Januari',
            'tahun': 2023,
            'waktu': datetime.now().isoformat(),
            'nominal': 1500000,
            'status': 'Verified'
        }])
    elif sheet_name == "Komplain":
        return pd.DataFrame([{
            'username': 'user1',
            'isi_komplain': 'AC tidak dingin',
            'link_foto': '',
            'waktu': datetime.now().isoformat(),
            'status': 'Terkirim'
        }])
    return pd.DataFrame()

def upload_to_cloudinary(file, public_id):
    return "https://via.placeholder.com/300"

# ======================== Fungsi Utama ========================
def run_penyewa(menu):
    if menu == "Beranda":
        show_dashboard()
    elif menu == "Pembayaran":
        show_pembayaran()
    elif menu == "Komplain":
        show_komplain()
    elif menu == "Profil":
        show_profil()
    elif menu == "Keluar":
        st.session_state.login_status = False
        st.session_state.username = ""
        st.session_state.role = None
        st.session_state.menu = None
        st.rerun()

# ======================== Dashboard ========================
def show_dashboard():
    # Header dengan gradient
    st.markdown(f"""
    <div class="header">
        <h1>👋 Selamat Datang, {st.session_state.get("username", "Penyewa")}</h1>
        <p>Dashboard Informasi Kamar & Pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    username = st.session_state.get("username", "user1")  # Default untuk testing
    data_user = user_df[user_df['username'] == username].iloc[0]
    data_kamar = kamar_df[kamar_df['Nama'] == data_user['kamar']].iloc[0]
    data_pembayaran = pembayaran_df[pembayaran_df['username'] == username]
    pembayaran_terakhir = data_pembayaran.sort_values("waktu", ascending=False).head(1).to_dict("records")
    data_komplain = komplain_df[komplain_df['username'] == username]
    riwayat_komplain = data_komplain.sort_values("waktu", ascending=False).head(5)

    # Layout 2x2 Grid
    col1, col2 = st.columns(2)

    with col1:
        # Card Profil Penyewa
        st.markdown(f"""
        <div class="card">
            <h3>👤 Profil Saya</h3>
            <img src="{data_user['foto_profil']}" width="100%" style="border-radius: 8px; margin-bottom: 10px;">
            <p><b>Nama:</b> {data_user['nama_lengkap']}</p>
            <p><b>No HP:</b> {data_user['no_hp']}</p>
            <p><b>Kamar:</b> {data_user['kamar']}</p>
            <p><b>Status:</b> <span class="status-{data_user['status_pembayaran'].lower()}">{data_user['status_pembayaran']}</span></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # Card Info Kamar
        st.markdown(f"""
        <div class="card">
            <h3>🛏️ Kamar Saya</h3>
            <img src="{data_kamar['link_foto']}" width="100%" style="border-radius: 8px; margin-bottom: 10px;">
            <p><b>Nama Kamar:</b> {data_kamar['Nama']}</p>
            <p><b>Harga:</b> Rp{data_kamar['Harga']:,}/bulan</p>
            <p><b>Status:</b> {data_kamar['Status']}</p>
            <p><b>Deskripsi:</b> {data_kamar['Deskripsi']}</p>
        </div>
        """, unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        # Card Riwayat Komplain
        with st.container():
            st.markdown("""
            <div class="card">
                <h3>💬 Komplain Terakhir</h3>
            """, unsafe_allow_html=True)
            
            if riwayat_komplain.empty:
                st.markdown('<div class="notif-info">Belum ada komplain</div>', unsafe_allow_html=True)
            else:
                for _, row in riwayat_komplain.iterrows():
                    st.markdown(f"""
                    <div style="margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <p><b>{row['waktu']}</b> - <span class="status-{row['status'].lower()}">{row['status']}</span></p>
                        <p>{row['isi_komplain']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        # Card Pembayaran Terakhir
        with st.container():
            st.markdown("""
            <div class="card">
                <h3>💳 Pembayaran Terakhir</h3>
            """, unsafe_allow_html=True)
            
            if pembayaran_terakhir:
                p = pembayaran_terakhir[0]
                st.image(p["bukti"], use_column_width=True)
                st.markdown(f"""
                <p><b>Periode:</b> {p['bulan']} {p['tahun']}</p>
                <p><b>Nominal:</b> Rp{p['nominal']:,}</p>
                <p><b>Status:</b> <span class="status-{p['status'].lower()}">{p['status']}</span></p>
                <p><b>Waktu Upload:</b> {p['waktu']}</p>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="notif-warning">Belum ada pembayaran</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# ======================== Pembayaran ========================
def show_pembayaran():
    st.markdown("""
    <div class="header">
        <h1>💸 Pembayaran Sewa</h1>
        <p>Upload bukti pembayaran & lihat riwayat</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "user1")
    data = load_sheet_data("Pembayaran")
    user_data = data[data['username'] == USERNAME]

    # Form Upload Pembayaran
    with st.expander("📤 Upload Bukti Pembayaran Baru", expanded=True):
        with st.form("form_bayar"):
            bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                        "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            tahun = st.selectbox("Tahun", [datetime.now().year, datetime.now().year + 1])
            nominal = st.number_input("Nominal (Rp)", min_value=100000, step=50000, value=1500000)
            bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("💾 Simpan Pembayaran"):
                if bukti:
                    st.markdown("""
                    <div class="notif-success">
                        ✅ Bukti pembayaran berhasil dikirim! (Simulasi)
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Harap upload bukti pembayaran.")

    # Riwayat Pembayaran
    st.markdown("### 📋 Riwayat Pembayaran")
    if not user_data.empty:
        for _, row in user_data.sort_values("waktu", ascending=False).iterrows():
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,}"):
                st.image(row['bukti'], use_column_width=True)
                st.markdown(f"""
                **Status:** <span class="status-{row['status'].lower()}">{row['status']}</span>  
                **Waktu Upload:** {row['waktu']}
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="notif-info">Belum ada riwayat pembayaran</div>', unsafe_allow_html=True)

# ======================== Komplain ========================
def show_komplain():
    st.markdown("""
    <div class="header">
        <h1>📢 Komplain & Keluhan</h1>
        <p>Sampaikan keluhan Anda kepada admin</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "user1")
    data = load_sheet_data("Komplain")
    user_data = data[data['username'] == USERNAME]

    # Form Komplain Baru
    with st.expander("📝 Buat Komplain Baru", expanded=True):
        with st.form("form_komplain"):
            isi = st.text_area("Keluhan Anda", placeholder="Tuliskan keluhan secara detail...")
            foto = st.file_uploader("Foto Pendukung (Opsional)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("📤 Kirim Komplain"):
                if isi:
                    st.markdown("""
                    <div class="notif-success">
                        ✅ Komplain berhasil dikirim! (Simulasi)
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("Harap isi keluhan Anda.")

    # Riwayat Komplain
    st.markdown("### 📜 Riwayat Komplain")
    if not user_data.empty:
        for _, row in user_data.sort_values("waktu", ascending=False).iterrows():
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(f"""
                **Status:** <span class="status-{row['status'].lower()}">{row['status']}</span>
                """, unsafe_allow_html=True)
                st.markdown(f"**Isi Komplain:**\n\n{row['isi_komplain']}")
                if row['link_foto']:
                    st.image(row['link_foto'], width=200)
    else:
        st.markdown('<div class="notif-info">Belum ada komplain</div>', unsafe_allow_html=True)

# ======================== Profil ========================
def show_profil():
    st.markdown("""
    <div class="header">
        <h1>👤 Profil Saya</h1>
        <p>Kelola informasi profil Anda</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "user1")
    data = load_sheet_data("User")
    row = data[data['username'] == USERNAME].iloc[0]

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(row['foto_profil'], width=200)
        st.markdown(f"<p style='text-align: center;'><b>Terakhir Diubah:</b> {row['last_edit']}</p>", unsafe_allow_html=True)
    
    with col2:
        with st.form("edit_profil"):
            st.markdown("<h3>📝 Edit Profil</h3>", unsafe_allow_html=True)
            
            nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
            no_hp = st.text_input("Nomor HP", value=row['no_hp'])
            deskripsi = st.text_area("Deskripsi Tambahan", value=row['deskripsi'])
            foto = st.file_uploader("Ubah Foto Profil", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("💾 Simpan Perubahan"):
                st.markdown("""
                <div class="notif-success">
                    ✅ Profil berhasil diperbarui! (Simulasi)
                </div>
                """, unsafe_allow_html=True)

# ======================== Testing ========================
if __name__ == "__main__":
    # Inisialisasi session state untuk testing
    if 'username' not in st.session_state:
        st.session_state.username = "user1"
    
    # Menu navigasi
    menu = st.sidebar.radio("Menu", ["Beranda", "Pembayaran", "Komplain", "Profil", "Keluar"])
    
    # Jalankan aplikasi
    run_penyewa(menu)
