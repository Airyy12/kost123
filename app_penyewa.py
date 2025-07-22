import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

def run_penyewa(menu):
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Pembayaran":
        show_pembayaran()
    elif menu == "Komplain":
        show_komplain()
    elif menu == "Profil Saya":
        show_profil()
    elif menu == "Logout":
        st.session_state.login_status = False
        st.session_state.username = ""
        st.session_state.role = None
        st.session_state.menu = None
        st.rerun()

def format_waktu(waktu_str):
    try:
        dt = datetime.fromisoformat(waktu_str)
        return dt.strftime("%d %B %Y %H:%M")
    except Exception:
        return waktu_str

def bulan_indo(dt):
    bulan_map = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    return bulan_map[dt.month]

def show_dashboard():
    USERNAME = st.session_state.get("username", "")
    st.markdown("---")

    # Muat semua data yang dibutuhkan
    user_df = load_sheet_data("User")
    if user_df.empty:
        user_df = pd.DataFrame(columns=["username", "nama_lengkap", "no_hp", "kamar", "deskripsi", "foto_profil", "status_pembayaran", "last_edit"])
    kamar_df = load_sheet_data("Kamar")
    if kamar_df.empty:
        kamar_df = pd.DataFrame(columns=["Nama", "Status", "Harga", "Deskripsi", "link_foto"])
    pembayaran_df = load_sheet_data("Pembayaran")
    if pembayaran_df.empty:
        pembayaran_df = pd.DataFrame(columns=["username", "bukti", "bulan", "tahun", "waktu", "nominal", "status"])
    komplain_df = load_sheet_data("Komplain")
    if komplain_df.empty:
        komplain_df = pd.DataFrame(columns=["username", "isi_komplain", "link_foto", "waktu", "status"])

    username = USERNAME
    try:
        data_user = user_df[user_df['username'] == username].iloc[0]
    except:
        st.error("Data pengguna tidak ditemukan.")
        return
    try:
        data_kamar = kamar_df[kamar_df['Nama'] == data_user['kamar']].iloc[0]
    except:
        data_kamar = pd.Series({"Nama": "-", "Status": "-", "Harga": 0, "Deskripsi": "-", "link_foto": ""})

    data_pembayaran = pembayaran_df[pembayaran_df['username'] == username]
    pembayaran_terakhir = data_pembayaran.sort_values("waktu", ascending=False).head(1).to_dict("records")
    data_komplain = komplain_df[komplain_df['username'] == username]

    # --- Hitung status pembayaran 3 bulan ---
    now = datetime.now()
    bulan_sekarang = bulan_indo(now)
    tahun_sekarang = now.year
    bulan_sebelumnya = bulan_indo((now.replace(day=1) - timedelta(days=1)))
    tahun_sebelumnya = (now.replace(day=1) - timedelta(days=1)).year
    bulan_nanti = bulan_indo((now.replace(day=28) + timedelta(days=4)).replace(day=1))
    tahun_nanti = (now.replace(day=28) + timedelta(days=4)).replace(day=1).year

    def get_status(bulan, tahun):
        df = data_pembayaran[(data_pembayaran['bulan'] == bulan) & (data_pembayaran['tahun'] == tahun)]
        if not df.empty:
            return df.iloc[0]['status']
        return "-"

    status_sebelumnya = get_status(bulan_sebelumnya, tahun_sebelumnya)
    status_sekarang = get_status(bulan_sekarang, tahun_sekarang)
    status_nanti = get_status(bulan_nanti, tahun_nanti)
    nominal_perbulan = int(data_kamar['Harga']) if 'Harga' in data_kamar else 0

    # --- Komplain statistik ---
    jumlah_selesai = len(data_komplain[data_komplain['status'].str.lower() == 'selesai']) if not data_komplain.empty else 0
    jumlah_pending = len(data_komplain[data_komplain['status'].str.lower().str.contains('pending|belum')]) if not data_komplain.empty else 0
    jumlah_ditolak = len(data_komplain[data_komplain['status'].str.lower() == 'ditolak']) if not data_komplain.empty else 0
    komplain_terakhir = data_komplain.sort_values("waktu", ascending=False).head(1)
    isi_komplain_terakhir = komplain_terakhir.iloc[0]['isi_komplain'] if not komplain_terakhir.empty else "-"

    # --- Custom CSS ---
    st.markdown("""
    <style>
    .dashboard-card {
        background: rgba(60,60,60,0.7);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        color: #E0E0E0;
        margin-bottom: 18px;
    }
    .dashboard-label {
        font-weight: bold;
        color: #E0E0E0;
        margin-bottom: 6px;
    }
    .dashboard-value {
        margin-bottom: 10px;
        color: #E0E0E0;
    }
    .dashboard-section-title {
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: #42A5F5;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.95em;
        margin-right: 8px;
    }
    .status-lunas { background: #66BB6A; color: #fff; }
    .status-belum { background: #FFA726; color: #222; }
    .status-ditolak { background: #EF5350; color: #fff; }
    .status-default { background: #888; color: #fff; }
    .info-row {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 12px;
    }
    .info-icon {
        font-size: 1.5em;
        margin-right: 10px;
    }
    .komplain-row {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 12px;
    }
    .komplain-icon {
        font-size: 1.5em;
        margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align:center;'>👋 Selamat datang, {data_user['nama_lengkap']}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # --- Layout utama: 2 kolom ---
    col_left, col_right = st.columns([1,2])

    with col_left:
        st.markdown("""
        <div class="dashboard-card">
            <img src="{foto}" width="120" style="border-radius:8px;margin-bottom:10px;">
            <div class="dashboard-label">Nama</div>
            <div class="dashboard-value">{nama}</div>
            <div class="dashboard-label">Username</div>
            <div class="dashboard-value">{username}</div>
            <div class="dashboard-label">Kamar</div>
            <div class="dashboard-value">{kamar}</div>
            <div class="dashboard-label">Deskripsi</div>
            <div class="dashboard-value">{deskripsi}</div>
        </div>
        """.format(
            foto=data_user['foto_profil'] if data_user['foto_profil'] else 'https://via.placeholder.com/150',
            nama=data_user['nama_lengkap'],
            username=data_user['username'],
            kamar=data_user['kamar'],
            deskripsi=data_user['deskripsi']
        ), unsafe_allow_html=True)

    with col_right:
        st.markdown('<div class="dashboard-section-title">Info Pembayaran</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="dashboard-label">Nominal Perbulan</div>
            <div class="dashboard-value">Rp{nominal_perbulan:,}</div>
            <div class="info-row">
                <span class="info-icon">🗓️</span>
                <b>{bulan_sebelumnya} {tahun_sebelumnya}</b>
                <span class="status-badge {get_status_class(status_sebelumnya)}">{status_sebelumnya}</span>
            </div>
            <div class="info-row">
                <span class="info-icon">🗓️</span>
                <b>{bulan_sekarang} {tahun_sekarang}</b>
                <span class="status-badge {get_status_class(status_sekarang)}">{status_sekarang}</span>
            </div>
            <div class="info-row">
                <span class="info-icon">🗓️</span>
                <b>{bulan_nanti} {tahun_nanti}</b>
                <span class="status-badge {get_status_class(status_nanti)}">{status_nanti}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="dashboard-section-title">Info Komplain</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="dashboard-card">
            <div class="komplain-row">
                <span class="komplain-icon">✅</span>
                <b>Selesai:</b> {jumlah_selesai}
            </div>
            <div class="komplain-row">
                <span class="komplain-icon">⏳</span>
                <b>Pending:</b> {jumlah_pending}
            </div>
            <div class="komplain-row">
                <span class="komplain-icon">❌</span>
                <b>Ditolak:</b> {jumlah_ditolak}
            </div>
            <div class="komplain-row">
                <span class="komplain-icon">📝</span>
                <b>Komplain terakhir:</b> {isi_komplain_terakhir}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

# Tambahkan fungsi utilitas untuk badge status
def get_status_class(status):
    status = str(status).lower()
    if status == "lunas":
        return "status-lunas"
    elif "belum" in status or "pending" in status or "menunggu" in status:
        return "status-belum"
    elif status == "ditolak":
        return "status-ditolak"
    else:
        return "status-default"

def show_pembayaran():
    USERNAME = st.session_state.get("username", "")
    st.title("💸 Pembayaran")

    # Load data
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "bukti", "bulan", "tahun", "waktu", "nominal", "status"])
    user_data = data[data['username'] == USERNAME]

    # Custom CSS
    st.markdown("""
    <style>
    .payment-container {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: rgba(30, 30, 30, 0.7);
        border-left: 4px solid #42A5F5;
    }
    .payment-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        padding: 0.5rem 0;
    }
    .payment-title {
        font-size: 1rem;
        font-weight: bold;
        color: #42A5F5;
        margin: 0;
    }
    .payment-status {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-lunas { background: #4CAF50; color: white; }
    .status-pending { background: #FF9800; color: black; }
    .status-ditolak { background: #F44336; color: white; }
    .payment-content {
        padding: 1rem 0;
        border-top: 1px solid #444;
        margin-top: 0.5rem;
    }
    .payment-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .payment-label {
        font-size: 0.85rem;
        color: #9E9E9E;
        margin-bottom: 0.25rem;
    }
    .payment-value {
        font-size: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Tab navigation
    tab1, tab2 = st.tabs(["📋 Riwayat Pembayaran", "💳 Upload Pembayaran"])

    with tab1:
        if user_data.empty:
            st.info("Belum ada riwayat pembayaran")
        else:
            # Sort by date descending
            sorted_data = user_data.sort_values(["tahun", "bulan"], ascending=[False, False])
            
            for idx, payment in sorted_data.iterrows():
                # Status styling
                status = payment['status'].lower()
                status_class = "status-lunas" if status == "lunas" else \
                             "status-ditolak" if status in ["ditolak", "rejected"] else \
                             "status-pending"
                
                # Create expandable section
                with st.expander(f"{payment['bulan']} {payment['tahun']}", expanded=False):
                    st.markdown('<div class="payment-container">', unsafe_allow_html=True)
                    
                    # Header with status
                    st.markdown(
                        f'<div class="payment-header">'
                        f'<div class="payment-status {status_class}">{payment["status"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    
                    # Payment details
                    st.markdown('<div class="payment-content">', unsafe_allow_html=True)
                    st.markdown('<div class="payment-grid">', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown('<div class="payment-label">Nominal</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="payment-value">Rp {int(payment["nominal"]):,}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="payment-label">Tanggal Upload</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="payment-value">{format_waktu(payment["waktu"])}</div>', unsafe_allow_html=True)
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Payment proof
                    if payment['bukti']:
                        st.image(payment['bukti'], use_container_width=True)
                    else:
                        st.markdown("_Tidak ada bukti pembayaran_")
                    
                    # Delete button
                    if st.button(f"Hapus Pembayaran", key=f"delete_{idx}"):
                        ws.delete_rows(idx+2)
                        st.success("Pembayaran berhasil dihapus!")
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        # Initialize form
        with st.form(key='payment_form', clear_on_submit=True):
            st.subheader("Form Pembayaran")
            
            col1, col2 = st.columns(2)
            with col1:
                bulan = st.selectbox(
                    "Bulan",
                    ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                     "Juli", "Agustus", "September", "Oktober", "November", "Desember"],
                    index=datetime.now().month-1
                )
            with col2:
                tahun = st.selectbox(
                    "Tahun",
                    [datetime.now().year-1, datetime.now().year, datetime.now().year+1],
                    index=1
                )
            
            nominal = st.number_input(
                "Nominal Pembayaran (Rp)",
                min_value=100000,
                value=1500000,
                step=50000
            )
            
            bukti = st.file_uploader(
                "Upload Bukti Pembayaran",
                type=["jpg", "jpeg", "png"],
                help="Upload bukti transfer atau pembayaran"
            )
            
            # Proper submit button
            submitted = st.form_submit_button("Kirim Pembayaran")
            
            if submitted:
                if not bukti:
                    st.error("Harap upload bukti pembayaran")
                else:
                    try:
                        image_url = upload_to_cloudinary(
                            bukti, 
                            f"payment_{USERNAME}_{bulan}_{tahun}_{datetime.now().timestamp()}"
                        )
                        
                        ws.append_row([
                            USERNAME,
                            image_url,
                            bulan,
                            tahun,
                            datetime.now().isoformat(),
                            nominal,
                            "Menunggu Verifikasi"
                        ])
                        
                        st.success("Bukti pembayaran berhasil dikirim!")
                        # Form will auto-clear because of clear_on_submit=True
                    except Exception as e:
                        st.error(f"Gagal mengupload: {str(e)}")

def show_komplain():
    USERNAME = st.session_state.get("username", "")
    st.title("📢 Komplain")
    
    # Load data
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "isi_komplain", "link_foto", "waktu", "status", "tanggapan"])
    user_data = data[data['username'] == USERNAME]

    # Custom CSS
    st.markdown("""
    <style>
    .complaint-container {
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: rgba(30, 30, 30, 0.7);
        border-left: 4px solid #FF5252;
    }
    .complaint-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        padding: 0.5rem 0;
    }
    .complaint-title {
        font-size: 1rem;
        font-weight: bold;
        color: #FF5252;
        margin: 0;
    }
    .complaint-status {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: bold;
    }
    .status-selesai { background: #4CAF50; color: white; }
    .status-pending { background: #FF9800; color: black; }
    .status-ditolak { background: #F44336; color: white; }
    .status-terkirim { background: #2196F3; color: white; }
    .complaint-content {
        padding: 1rem 0;
        border-top: 1px solid #444;
        margin-top: 0.5rem;
    }
    .complaint-text {
        margin-bottom: 1rem;
        white-space: pre-line;
    }
    .response-container {
        background: rgba(60, 60, 60, 0.5);
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
        border-left: 3px solid #42A5F5;
    }
    .response-label {
        font-weight: bold;
        color: #42A5F5;
        margin-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # Tab navigation
    tab1, tab2 = st.tabs(["📋 Riwayat Komplain", "📝 Buat Komplain Baru"])

    with tab1:
        if user_data.empty:
            st.info("Belum ada riwayat komplain")
        else:
            # Sort by date descending
            sorted_data = user_data.sort_values("waktu", ascending=False)
            
            for idx, complaint in sorted_data.iterrows():
                # Status styling
                status = complaint['status'].lower()
                status_class = "status-selesai" if status == "selesai" else \
                              "status-ditolak" if status == "ditolak" else \
                              "status-pending" if status in ["pending", "menunggu"] else \
                              "status-terkirim"
                
                # Create expandable section
                with st.expander(f"{format_waktu(complaint['waktu'])} - {complaint['status']}", expanded=False):
                    st.markdown('<div class="complaint-container">', unsafe_allow_html=True)
                    
                    # Complaint content
                    st.markdown('<div class="complaint-content">', unsafe_allow_html=True)
                    st.markdown('<div class="complaint-text">', unsafe_allow_html=True)
                    st.markdown(complaint['isi_komplain'])
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Complaint photo
                    if complaint['link_foto']:
                        st.image(complaint['link_foto'], use_container_width=True)
                    
                    # Admin response (if exists)
                    if complaint.get('tanggapan'):
                        st.markdown('<div class="response-container">', unsafe_allow_html=True)
                        st.markdown('<div class="response-label">Tanggapan Admin:</div>', unsafe_allow_html=True)
                        st.markdown(complaint['tanggapan'])
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Delete button
                    if st.button(f"Hapus Komplain", key=f"delete_{idx}"):
                        ws.delete_rows(idx+2)
                        st.success("Komplain berhasil dihapus!")
                        st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)

    with tab2:
        with st.form(key='new_complaint_form', clear_on_submit=True):
            st.subheader("Form Komplain Baru")
            
            complaint_text = st.text_area(
                "Isi Komplain*",
                placeholder="Jelaskan komplain Anda secara detail...",
                height=150
            )
            
            complaint_photo = st.file_uploader(
                "Upload Foto Pendukung (Opsional)",
                type=["jpg", "jpeg", "png"],
                help="Upload foto jika diperlukan untuk memperjelas komplain"
            )
            
            # Proper submit button
            submitted = st.form_submit_button("Kirim Komplain")
            
            if submitted:
                if not complaint_text:
                    st.error("Harap isi komplain terlebih dahulu")
                else:
                    try:
                        photo_url = upload_to_cloudinary(
                            complaint_photo, 
                            f"complaint_{USERNAME}_{datetime.now().timestamp()}"
                        ) if complaint_photo else ""
                        
                        ws.append_row([
                            USERNAME,
                            complaint_text,
                            photo_url,
                            datetime.now().isoformat(),
                            "Terkirim",
                            ""  # Empty for admin response
                        ])
                        
                        st.success("Komplain berhasil dikirim!")
                        # Form will auto-clear because of clear_on_submit=True
                    except Exception as e:
                        st.error(f"Gagal mengirim komplain: {str(e)}")
                        
def show_profil():
    USERNAME = st.session_state.get("username", "")
    st.title("👤 Profil Saya")
    
    # Custom CSS untuk halaman profil
    st.markdown("""
    <style>
    .profile-card {
        background: rgba(60,60,60,0.7);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        margin-bottom: 20px;
    }
    .profile-header {
        color: #42A5F5;
        font-size: 1.3rem;
        margin-bottom: 15px;
        border-bottom: 1px solid #444;
        padding-bottom: 10px;
    }
    .profile-detail {
        margin-bottom: 10px;
    }
    .edit-form {
        background: rgba(60,60,60,0.9);
        padding: 20px;
        border-radius: 12px;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Load data user dari Google Sheets
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        user_data = next((u for u in users if u['username'] == USERNAME), None)
        
        if not user_data:
            st.error("Data pengguna tidak ditemukan")
            return

        # Tampilkan data profil
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("### Foto Profil")
            if user_data.get('foto_profil'):
                st.image(user_data['foto_profil'], width=150, caption="Foto Profil Saat Ini")
            else:
                st.image("https://via.placeholder.com/150", width=150, caption="Belum Ada Foto")
            
            # Statistik aktivitas
            st.markdown("### Aktivitas Terakhir")
            st.markdown(f"""
            <div class="profile-detail">
                <p><strong>Login Terakhir:</strong> {user_data.get('last_login', '-')}</p>
                <p><strong>Edit Profil Terakhir:</strong> {format_waktu(user_data.get('last_edit', '-'))}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Informasi Profil")
            st.markdown(f"""
            <div class="profile-card">
                <div class="profile-header">Data Pribadi</div>
                <p class="profile-detail"><strong>Username:</strong> {user_data['username']}</p>
                <p class="profile-detail"><strong>Nama Lengkap:</strong> {user_data.get('nama_lengkap', '-')}</p>
                <p class="profile-detail"><strong>Nomor HP/Email:</strong> {user_data.get('no_hp', '-')}</p>
                <p class="profile-detail"><strong>Kamar:</strong> {user_data.get('kamar', '-')}</p>
                <p class="profile-detail"><strong>Status Pembayaran:</strong> {user_data.get('status_pembayaran', '-')}</p>
                <p class="profile-detail"><strong>Deskripsi:</strong> {user_data.get('deskripsi', '-')}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tombol edit profil
        if st.button("✏️ Edit Profil", key="edit_profile_btn"):
            st.session_state.edit_profile = True
        
        # Form edit profil
        if st.session_state.get('edit_profile'):
            with st.form(key='edit_profile_form'):
                st.markdown("### Edit Profil")
                
                # Cek apakah bisa edit (untuk non-admin, maksimal 1x seminggu)
                can_edit = True
                last_edit_str = user_data.get('last_edit', '')
                if last_edit_str:
                    try:
                        last_edit = datetime.fromisoformat(last_edit_str)
                        if datetime.now() - last_edit < timedelta(days=7):
                            can_edit = False
                            st.warning("Anda hanya bisa mengedit profil 1 kali dalam seminggu")
                    except:
                        pass
                
                if can_edit:
                    col1, col2 = st.columns(2)
                    with col1:
                        nama = st.text_input("Nama Lengkap", value=user_data.get('nama_lengkap', ''))
                        kontak = st.text_input("Nomor HP/Email", value=user_data.get('no_hp', ''))
                        deskripsi = st.text_area("Deskripsi Diri", value=user_data.get('deskripsi', ''))
                    
                    with col2:
                        foto = st.file_uploader("Upload Foto Profil Baru", type=["jpg", "jpeg", "png"])
                        
                        # Toggle password visibility
                        st.markdown("### Ganti Password (Opsional)")
                        show_password = st.checkbox("Tampilkan Password", key="show_pass")
                        password_type = "text" if show_password else "password"
                        new_password = st.text_input("Password Baru", type=password_type)
                        confirm_password = st.text_input("Konfirmasi Password", type=password_type)
                        
                        if new_password and new_password != confirm_password:
                            st.error("Password tidak cocok!")
                    
                    # Tombol aksi
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Simpan Perubahan"):
                            # Validasi password
                            if new_password and new_password != confirm_password:
                                st.error("Password tidak cocok!")
                            else:
                                # Upload foto baru jika ada
                                link_foto = upload_to_cloudinary(foto, f"profil_{USERNAME}") if foto else user_data.get('foto_profil', '')
                                
                                # Update data di Google Sheets
                                all_users = user_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == USERNAME), None)
                                
                                if row_num:
                                    updates = {
                                        4: nama,  # nama_lengkap
                                        5: f"'{kontak}",  # no_hp (ditambahkan ' untuk format nomor)
                                        6: user_data.get('kamar', ''),  # kamar
                                        7: deskripsi,  # deskripsi
                                        8: link_foto,  # foto_profil
                                        9: datetime.now().isoformat()  # last_edit
                                    }
                                    
                                    for col, value in updates.items():
                                        user_ws.update_cell(row_num, col, value)
                                    
                                    # Update password jika diisi
                                    if new_password:
                                        hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
                                        user_ws.update_cell(row_num, 2, hashed)  # password_hash
                                    
                                    st.success("Profil berhasil diperbarui!")
                                    st.session_state.edit_profile = False
                                    st.rerun()
                    
                    with col2:
                        if st.form_submit_button("❌ Batal"):
                            st.session_state.edit_profile = False
                            st.rerun()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat profil: {str(e)}")

# --- Entry Point untuk Streamlit App ---
if __name__ == "__main__":
    # Inisialisasi session state jika belum ada
    if "login_status" not in st.session_state:
        st.session_state.login_status = True
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = "penyewa"
    if "menu" not in st.session_state:
        st.session_state.menu = "Dashboard"

    # Simulasi login sederhana
    if not st.session_state.login_status or not st.session_state.username:
        st.title("Login Penyewa")
        username_input = st.text_input("Username")
        if st.button("Login"):
            st.session_state.username = username_input
            st.session_state.login_status = True
            st.session_state.role = "penyewa"
            st.session_state.menu = "Dashboard"
            st.rerun()
        st.stop()

    # Sidebar Menu Navigasi
    menu = st.sidebar.radio(
        "Menu Penyewa",
        ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"],
        index=["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"].index(st.session_state.menu)
    )
    st.session_state.menu = menu

    # Jalankan fitur sesuai menu
    run_penyewa(menu)
    # Inisialisasi session state jika belum ada
    if "login_status" not in st.session_state:
        st.session_state.login_status = True
    if "username" not in st.session_state:
        st.session_state.username = ""
    if "role" not in st.session_state:
        st.session_state.role = "penyewa"
    if "menu" not in st.session_state:
        st.session_state.menu = "Dashboard"

    # Simulasi login sederhana
    if not st.session_state.login_status or not st.session_state.username:
        st.title("Login Penyewa")
        username_input = st.text_input("Username")
        if st.button("Login"):
            st.session_state.username = username_input
            st.session_state.login_status = True
            st.session_state.role = "penyewa"
            st.session_state.menu = "Dashboard"
            st.rerun()
        st.stop()

    # Sidebar Menu Navigasi
    menu = st.sidebar.radio(
        "Menu Penyewa",
        ["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"],
        index=["Dashboard", "Pembayaran", "Komplain", "Profil Saya", "Logout"].index(st.session_state.menu)
    )
    st.session_state.menu = menu

    # Jalankan fitur sesuai menu
    run_penyewa(menu)
 
