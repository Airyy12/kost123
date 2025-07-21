import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

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
    
    /* Tombol */
    .stButton>button {
        border-radius: 8px !important;
        padding: 8px 16px !important;
        transition: all 0.3s !important;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
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
    .notif-warning {
        background-color: #fff3cd;
        color: #856404;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    .notif-info {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 12px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Input */
    .stTextInput>div>div>input, 
    .stTextArea>div>div>textarea {
        border-radius: 8px !important;
    }
    
    /* Tab */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        border-radius: 8px !important;
    }
</style>
""", unsafe_allow_html=True)

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
        <h1>👋 Selamat Datang, {st.session_state.get("nama", "Penyewa")}</h1>
        <p>Dashboard Informasi Kamar & Pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    # Load data
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    username = st.session_state.get("username", "")
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
            <p><b>Status:</b> <span class="status-{data_user['status_pembayaran'].lower().replace(' ', '-')}">{data_user['status_pembayaran']}</span></p>
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
                        <p><b>{row['waktu']}</b> - <span class="status-{row['status'].lower().replace(' ', '-')}">{row['status']}</span></p>
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
                <p><b>Status:</b> <span class="status-{p['status'].lower().replace(' ', '-')}">{p['status']}</span></p>
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

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    # Form Upload Pembayaran
    with st.expander("📤 Upload Bukti Pembayaran Baru", expanded=True):
        with st.form("form_bayar"):
            cols = st.columns(2)
            with cols[0]:
                bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                            "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            with cols[1]:
                tahun = st.selectbox("Tahun", [datetime.now().year, datetime.now().year + 1])
            
            nominal = st.number_input("Nominal (Rp)", min_value=100000, step=50000)
            bukti = st.file_uploader("Upload Bukti Transfer", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("💾 Simpan Pembayaran", use_container_width=True)
            
            if submitted:
                if bukti:
                    with st.spinner("Mengupload bukti pembayaran..."):
                        url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}")
                        ws.append_row([
                            USERNAME, 
                            url, 
                            bulan, 
                            tahun, 
                            datetime.now().strftime("%Y-%m-%d %H:%M"), 
                            nominal, 
                            "Menunggu Verifikasi"
                        ])
                        st.markdown("""
                        <div class="notif-success">
                            ✅ Bukti pembayaran berhasil dikirim!
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                else:
                    st.error("Harap upload bukti pembayaran.")

    # Riwayat Pembayaran
    st.markdown("### 📋 Riwayat Pembayaran")
    if not user_data.empty:
        for _, row in user_data.sort_values("waktu", ascending=False).iterrows():
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,}"):
                st.image(row['bukti'], use_column_width=True)
                st.markdown(f"""
                **Status:** <span class="status-{row['status'].lower().replace(' ', '-')}">{row['status']}</span>  
                **Waktu Upload:** {row['waktu']}
                """, unsafe_allow_html=True)
                
                if st.button("Hapus Pembayaran", key=f"hapus_{row.name}"):
                    ws.delete_rows(row.name + 2)  # +2 karena header + index 0
                    st.markdown("""
                    <div class="notif-success">
                        ✅ Pembayaran berhasil dihapus
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
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

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    # Form Komplain Baru
    with st.expander("📝 Buat Komplain Baru", expanded=True):
        with st.form("form_komplain"):
            isi = st.text_area("Keluhan Anda", placeholder="Tuliskan keluhan secara detail...")
            foto = st.file_uploader("Foto Pendukung (Opsional)", type=["jpg", "jpeg", "png"])
            
            submitted = st.form_submit_button("📤 Kirim Komplain", use_container_width=True)
            
            if submitted:
                if isi:
                    with st.spinner("Mengirim komplain..."):
                        url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().timestamp()}") if foto else ""
                        ws.append_row([
                            USERNAME, 
                            isi, 
                            url, 
                            datetime.now().strftime("%Y-%m-%d %H:%M"), 
                            "Terkirim"
                        ])
                        st.markdown("""
                        <div class="notif-success">
                            ✅ Komplain berhasil dikirim!
                        </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                else:
                    st.error("Harap isi keluhan Anda.")

    # Riwayat Komplain
    st.markdown("### 📜 Riwayat Komplain")
    if not user_data.empty:
        for _, row in user_data.sort_values("waktu", ascending=False).iterrows():
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(f"""
                **Status:** <span class="status-{row['status'].lower().replace(' ', '-')}">{row['status']}</span>
                """, unsafe_allow_html=True)
                st.markdown(f"**Isi Komplain:**\n\n{row['isi_komplain']}")
                if row['link_foto']:
                    st.image(row['link_foto'], width=200)
                
                if st.button("Hapus Komplain", key=f"hapus_komplain_{row.name}"):
                    ws.delete_rows(row.name + 2)
                    st.markdown("""
                    <div class="notif-success">
                        ✅ Komplain berhasil dihapus
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
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

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("User")
    data = pd.DataFrame(ws.get_all_records())
    idx = data.index[data['username'] == USERNAME].tolist()[0]
    row = data.iloc[idx]

    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image(row['foto_profil'], width=200, use_column_width=False)
        st.markdown(f"<p style='text-align: center;'><b>Terakhir Diubah:</b> {row['last_edit']}</p>", unsafe_allow_html=True)
    
    with col2:
        with st.form("edit_profil"):
            st.markdown("<h3>📝 Edit Profil</h3>", unsafe_allow_html=True)
            
            nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
            no_hp = st.text_input("Nomor HP", value=row['no_hp'])
            deskripsi = st.text_area("Deskripsi Tambahan", value=row['deskripsi'])
            foto = st.file_uploader("Ubah Foto Profil", type=["jpg", "jpeg", "png"])
            
            # Cek apakah bisa edit (7 hari setelah terakhir edit)
            edit_allowed = True
            try:
                last = datetime.fromisoformat(row['last_edit'])
                if datetime.now() - last < timedelta(days=7):
                    edit_allowed = False
                    st.markdown(f"""
                    <div class="notif-warning">
                        Anda hanya bisa mengedit profil sekali dalam 7 hari. 
                        Terakhir edit: {row['last_edit']}
                    </div>
                    """, unsafe_allow_html=True)
            except:
                pass
            
            submitted = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True, disabled=not edit_allowed)
            
            if submitted:
                with st.spinner('Menyimpan perubahan...'):
                    url = upload_to_cloudinary(foto, f"foto_profil_{USERNAME}_{datetime.now().timestamp()}") if foto else row['foto_profil']
                    ws.update(f"D{idx+2}:G{idx+2}", [[nama, no_hp, deskripsi, url]])
                    ws.update_acell(f"I{idx+2}", datetime.now().isoformat())
                    st.markdown("""
                    <div class="notif-success">
                        ✅ Profil berhasil diperbarui!
                    </div>
                    """, unsafe_allow_html=True)
                    st.rerun()
