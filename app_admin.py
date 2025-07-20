import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

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

    # Load semua data yang diperlukan
    try:
        df_kamar = load_sheet_data('kamar')
        df_user = load_sheet_data('user')
        df_komplain = load_sheet_data('komplain')
        df_booking = load_sheet_data('booking')
        df_pembayaran = load_sheet_data('pembayaran')
    except Exception as e:
        st.error(f"Gagal memuat data: {str(e)}")
        return

    # ========== STATISTIK KAMAR ==========
    st.markdown("## 📊 Statistik Kamar")
    
    # Hitung statistik
    total_kamar = len(df_kamar)
    kamar_kosong = len(df_kamar[df_kamar['Status'] == 'Kosong'])
    kamar_terisi = len(df_kamar[df_kamar['Status'] == 'Terisi'])
    penyewa_aktif = len(df_user[(df_user['role'] == 'penyewa') & (df_user['status_pembayaran'] == 'Lunas')])

    # Tampilkan dalam columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <h3>🏘️ Total Kamar</h3>
            <h2 style="color: #42A5F5;">{total_kamar}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <h3>🛏️ Kamar Kosong</h3>
            <h2 style="color: #66BB6A;">{kamar_kosong}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <h3>🧑 Kamar Terisi</h3>
            <h2 style="color: #FFA726;">{kamar_terisi}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="info-card" style="text-align: center;">
            <h3>✅ Penyewa Aktif</h3>
            <h2 style="color: #AB47BC;">{penyewa_aktif}</h2>
        </div>
        """, unsafe_allow_html=True)

    # ========== CUSTOM CSS UNTUK CARD ==========
    st.markdown("""
    <style>
    .komplain-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #FFA726;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
    .booking-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #42A5F5;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
    .pembayaran-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #66BB6A;
        box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    }
    .card-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 10px;
        color: #E0E0E0;
    }
    .card-content {
        color: #E0E0E0;
    }
    .card-time {
        font-size: 14px;
        color: #B0B0B0;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Membagi layout menjadi 3 kolom untuk menampilkan semua card dalam satu view
    col1, col2, col3 = st.columns(3)

    with col1:
        # ========== KOMPLAIN TERBARU ==========
        st.markdown("### 🛠️ Komplain Terbaru")
        if df_komplain.empty:
            st.info("Belum ada komplain.")
        else:
            komplain_terbaru = df_komplain.sort_values("waktu", ascending=False).head(2)
            for _, row in komplain_terbaru.iterrows():
                st.markdown(f"""
                <div class="komplain-card">
                    <div class="card-title">🧑 {row.get('username', 'N/A')}</div>
                    <div class="card-time">📅 {row.get('waktu', '')}</div>
                    <div class="card-content">📝 {row.get('isi_komplain', '')}</div>
                </div>
                """, unsafe_allow_html=True)

    with col2:
        # ========== BOOKING TERBARU ==========
        st.markdown("### 📝 Booking Terbaru")
        if df_booking.empty:
            st.info("Belum ada data booking.")
        else:
            booking_terbaru = df_booking.sort_values("waktu_booking", ascending=False).head(2)
            for _, row in booking_terbaru.iterrows():
                st.markdown(f"""
                <div class="booking-card">
                    <div class="card-title">🧑 {row.get('nama', 'N/A')}</div>
                    <div class="card-time">📅 {row.get('waktu_booking', '')}</div>
                    <div class="card-content">🏠 Kamar: {row.get('kamar_dipilih', '')}</div>
                </div>
                """, unsafe_allow_html=True)

    with col3:
        # ========== PEMBAYARAN TERBARU ==========
        st.markdown("### 💵 Pembayaran Terbaru")
        if df_pembayaran.empty:
            st.info("Belum ada data pembayaran.")
        else:
            pembayaran_terbaru = df_pembayaran.sort_values("waktu", ascending=False).head(2)
            for _, row in pembayaran_terbaru.iterrows():
                nominal = int(row.get('nominal', 0))
                st.markdown(f"""
                <div class="pembayaran-card">
                    <div class="card-title">🧑 {row.get('username', 'N/A')}</div>
                    <div class="card-time">📅 {row.get('waktu', '')}</div>
                    <div class="card-content">💸 Rp {nominal:,}</div>
                    <div class="card-content">🗓️ {row.get('bulan', '')} {row.get('tahun', '')}</div>
                </div>
                """, unsafe_allow_html=True)

def kelola_kamar():
    st.title("🛏️ Kelola Kamar")
    
    # Load data kamar
    try:
        kamar_ws = connect_gsheet().worksheet("Kamar")
        kamar_data = kamar_ws.get_all_records()
    except Exception as e:
        st.error(f"Gagal memuat data kamar: {str(e)}")
        return

    # Custom CSS untuk tampilan kamar
    st.markdown("""
    <style>
    .kamar-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .kamar-status-kosong {
        color: #66BB6A;
        font-weight: bold;
    }
    .kamar-status-terisi {
        color: #EF5350;
        font-weight: bold;
    }
    .kamar-harga {
        color: #FFA726;
        font-weight: bold;
    }
    .tab-content {
        padding: 15px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Tab untuk navigasi
    tab1, tab2 = st.tabs(["📋 Daftar Kamar", "➕ Tambah Kamar Baru"])

    with tab1:
        st.markdown("### Daftar Kamar Tersedia")
        
        if not kamar_data:
            st.info("Belum ada data kamar.")
        else:
            for kamar in kamar_data:
                with st.container():
                    status_class = "kamar-status-kosong" if kamar['Status'] == 'Kosong' else "kamar-status-terisi"
                    
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        if kamar.get('link_foto'):
                            st.image(kamar['link_foto'], width=150, caption=kamar['Nama'])
                        else:
                            st.image("https://via.placeholder.com/150", width=150, caption="No Image")
                    
                    with col2:
                        st.markdown(f"""
                        <div class="kamar-card">
                            <h3>{kamar['Nama']}</h3>
                            <p>Status: <span class="{status_class}">{kamar['Status']}</span></p>
                            <p>Harga: <span class="kamar-harga">Rp {int(kamar['Harga']):,}/bulan</span></p>
                            <p>{kamar.get('Deskripsi', 'Tidak ada deskripsi')}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Tombol aksi
                        col_edit, col_delete = st.columns(2)
                        with col_edit:
                            if st.button("✏️ Edit", key=f"edit_{kamar['Nama']}"):
                                st.session_state.edit_kamar = kamar
                        with col_delete:
                            if st.button("🗑️ Hapus", key=f"delete_{kamar['Nama']}"):
                                # Cari index kamar yang akan dihapus
                                all_values = kamar_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_values) if row[0] == kamar['Nama']), None)
                                if row_num:
                                    kamar_ws.delete_rows(row_num)
                                    st.success(f"Kamar {kamar['Nama']} berhasil dihapus!")
                                    st.rerun()

        # Form edit kamar (muncul ketika tombol edit diklik)
        if 'edit_kamar' in st.session_state:
            with st.form(key='edit_kamar_form'):
                st.markdown("### Edit Kamar")
                kamar = st.session_state.edit_kamar
                
                nama = st.text_input("Nama Kamar", value=kamar['Nama'])
                status = st.selectbox("Status", ["Kosong", "Terisi"], index=0 if kamar['Status'] == 'Kosong' else 1)
                harga = st.number_input("Harga", min_value=0, value=int(kamar['Harga']))
                deskripsi = st.text_area("Deskripsi", value=kamar.get('Deskripsi', ''))
                foto = st.file_uploader("Upload Foto Baru", type=["jpg","jpeg","png"], key="edit_foto")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Simpan Perubahan"):
                        # Cari index kamar yang akan diupdate
                        all_values = kamar_ws.get_all_values()
                        row_num = next((i+1 for i, row in enumerate(all_values) if row[0] == kamar['Nama']), None)
                        
                        if row_num:
                            # Jika ada foto baru diupload
                            link_foto = upload_to_cloudinary(foto, f"Kamar_{nama}") if foto else kamar.get('link_foto', '')
                            
                            # Update data
                            kamar_ws.update(f"A{row_num}", nama)
                            kamar_ws.update(f"B{row_num}", status)
                            kamar_ws.update(f"C{row_num}", harga)
                            kamar_ws.update(f"D{row_num}", deskripsi)
                            kamar_ws.update(f"E{row_num}", link_foto)
                            
                            st.success("Data kamar berhasil diperbarui!")
                            del st.session_state.edit_kamar
                            st.rerun()
                
                with col2:
                    if st.form_submit_button("❌ Batal"):
                        del st.session_state.edit_kamar
                        st.rerun()

    with tab2:
        st.markdown("### Tambah Kamar Baru")
        with st.form(key='tambah_kamar_form'):
            nama = st.text_input("Nama Kamar*")
            harga = st.number_input("Harga*", min_value=0)
            deskripsi = st.text_area("Deskripsi")
            foto = st.file_uploader("Upload Foto", type=["jpg","jpeg","png"])
            
            if st.form_submit_button("➕ Tambah Kamar"):
                if not nama:
                    st.error("Nama kamar wajib diisi!")
                else:
                    link = upload_to_cloudinary(foto, f"Kamar_{nama}") if foto else ""
                    kamar_ws.append_row([nama, "Kosong", harga, deskripsi, link])
                    st.success("Kamar berhasil ditambahkan!")
                    st.rerun()

def manajemen():
    st.title("📁 Manajemen Sistem")
    
    # Custom CSS untuk manajemen
    st.markdown("""
    <style>
    .management-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .status-lunas {
        color: #66BB6A;
        font-weight: bold;
    }
    .status-belum-bayar {
        color: #EF5350;
        font-weight: bold;
    }
    .status-ditolak {
        color: #9E9E9E;
        font-weight: bold;
    }
    .action-btn {
        margin: 5px 0;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    submenu = st.selectbox("Pilih Menu Manajemen", 
                         ["Manajemen Penyewa", "Manajemen Pembayaran", "Manajemen Komplain"],
                         key="submenu_selector")

    if submenu == "Manajemen Penyewa":
        manajemen_penyewa()
    elif submenu == "Manajemen Pembayaran":
        manajemen_pembayaran()
    elif submenu == "Manajemen Komplain":
        manajemen_komplain()

def manajemen_penyewa():
    st.header("👥 Manajemen Penyewa")
    
    try:
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        penyewa_list = [u for u in users if u['role'] == 'penyewa']
        
        if not penyewa_list:
            st.info("Belum ada data penyewa.")
            return
            
        st.markdown(f"**Total Penyewa:** {len(penyewa_list)}")
        
        # Filter dan pencarian
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("Filter Status Pembayaran", 
                                       ["Semua", "Lunas", "Belum Bayar", "Ditolak"])
        with col2:
            search_query = st.text_input("Cari Penyewa")
            
        # Apply filters
        filtered_penyewa = penyewa_list
        if filter_status != "Semua":
            filtered_penyewa = [p for p in filtered_penyewa if p['status_pembayaran'] == filter_status]
        if search_query:
            filtered_penyewa = [p for p in filtered_penyewa 
                              if search_query.lower() in p['nama_lengkap'].lower() 
                              or search_query.lower() in p['username'].lower()]

        for idx, penyewa in enumerate(filtered_penyewa):
            with st.expander(f"{penyewa.get('nama_lengkap', penyewa['username'])} - Kamar: {penyewa.get('kamar', '-')}", expanded=False):
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    if penyewa.get('foto_profil'):
                        st.image(penyewa['foto_profil'], width=100, caption="Foto Profil")
                
                with col2:
                    status_class = ""
                    if penyewa['status_pembayaran'] == 'Lunas':
                        status_class = "status-lunas"
                    elif penyewa['status_pembayaran'] == 'Ditolak':
                        status_class = "status-ditolak"
                    else:
                        status_class = "status-belum-bayar"
                    
                    st.markdown(f"""
                    <div class="management-card">
                        <p><strong>Username:</strong> {penyewa['username']}</p>
                        <p><strong>Nama Lengkap:</strong> {penyewa.get('nama_lengkap', '-')}</p>
                        <p><strong>No HP:</strong> {penyewa.get('no_hp', '-')}</p>
                        <p><strong>Kamar:</strong> {penyewa.get('kamar', '-')}</p>
                        <p><strong>Status Pembayaran:</strong> <span class="{status_class}">{penyewa['status_pembayaran']}</span></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Form edit
                    with st.form(key=f"edit_penyewa_{idx}"):
                        nama = st.text_input("Nama Lengkap", value=penyewa.get('nama_lengkap', ''), key=f"nama_{idx}")
                        no_hp = st.text_input("No HP", value=penyewa.get('no_hp', ''), key=f"hp_{idx}")
                        kamar = st.text_input("Kamar", value=penyewa.get('kamar', ''), key=f"kamar_{idx}")
                        deskripsi = st.text_area("Deskripsi", value=penyewa.get('deskripsi', ''), key=f"desc_{idx}")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.form_submit_button("💾 Simpan Perubahan"):
                                # Update data di Google Sheets
                                all_users = user_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == penyewa['username']), None)
                                if row_num:
                                    user_ws.update(f"D{row_num}", nama)
                                    user_ws.update(f"E{row_num}", f"'{no_hp}")
                                    user_ws.update(f"F{row_num}", kamar)
                                    user_ws.update(f"G{row_num}", deskripsi)
                                    st.success("Data penyewa berhasil diperbarui!")
                                    st.rerun()
                        with col2:
                            if st.form_submit_button("🔄 Reset Password"):
                                new_pass = "12345678"
                                hashed = bcrypt.hashpw(new_pass.encode(), bcrypt.gensalt()).decode()
                                all_users = user_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == penyewa['username']), None)
                                if row_num:
                                    user_ws.update(f"B{row_num}", hashed)
                                    st.warning(f"Password direset ke: {new_pass}")
                                    st.rerun()
                        with col3:
                            if st.form_submit_button("🗑️ Hapus Penyewa"):
                                all_users = user_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == penyewa['username']), None)
                                if row_num:
                                    user_ws.delete_rows(row_num)
                                    st.warning("Penyewa berhasil dihapus!")
                                    st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def manajemen_pembayaran():
    st.header("💰 Manajemen Pembayaran")
    
    try:
        pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
        pembayaran_data = pembayaran_ws.get_all_records()
        
        if not pembayaran_data:
            st.info("Belum ada data pembayaran.")
            return
            
        # Filter data
        col1, col2 = st.columns(2)
        with col1:
            filter_status = st.selectbox("Filter Status", 
                                       ["Semua", "Lunas", "Belum Verifikasi", "Ditolak"],
                                       key="filter_status_pembayaran")
        with col2:
            bulan_filter = st.selectbox("Filter Bulan", 
                                      ["Semua"] + sorted(list(set(p['bulan'] for p in pembayaran_data if 'bulan' in p))),
                                      key="filter_bulan")
        
        # Apply filters
        filtered_data = pembayaran_data
        if filter_status != "Semua":
            filtered_data = [p for p in filtered_data if p['status'] == filter_status]
        if bulan_filter != "Semua":
            filtered_data = [p for p in filtered_data if p['bulan'] == bulan_filter]
        
        for idx, bayar in enumerate(filtered_data):
            status_class = ""
            if bayar['status'] == 'Lunas':
                status_class = "status-lunas"
            elif bayar['status'] == 'Ditolak':
                status_class = "status-ditolak"
            else:
                status_class = "status-belum-bayar"
            
            with st.expander(f"{bayar['username']} - {bayar['bulan']} {bayar['tahun']} - Rp{int(bayar['nominal']):,}", expanded=False):
                st.markdown(f"""
                <div class="management-card">
                    <p><strong>Username:</strong> {bayar['username']}</p>
                    <p><strong>Periode:</strong> {bayar['bulan']} {bayar['tahun']}</p>
                    <p><strong>Nominal:</strong> Rp {int(bayar['nominal']):,}</p>
                    <p><strong>Waktu Upload:</strong> {bayar['waktu']}</p>
                    <p><strong>Status:</strong> <span class="{status_class}">{bayar['status']}</span></p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tampilkan bukti pembayaran
                if bayar.get('bukti'):
                    try:
                        st.image(bayar['bukti'], caption="Bukti Pembayaran", use_container_width=True)
                    except:
                        st.warning("Gagal memuat bukti pembayaran")
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if bayar['status'] != 'Lunas':
                        if st.button("✅ Verifikasi", key=f"verif_{idx}", use_container_width=True):
                            # Update status di sheet Pembayaran
                            all_payments = pembayaran_ws.get_all_values()
                            row_num = next(
                                (i+1 for i, row in enumerate(all_payments)
                                 if row[0] == bayar['username'] and row[3] == bayar['bulan'] and row[4] == bayar['tahun']),
                                None
                            )
                            if row_num:
                                pembayaran_ws.update_cell(row_num, 7, "Lunas")
                            
                            # Update status di sheet User
                            user_ws = connect_gsheet().worksheet("User")
                            users = user_ws.get_all_values()
                            user_row = next((i+1 for i, row in enumerate(users) if row[0] == bayar['username']), None)
                            if user_row:
                                user_ws.update_cell(user_row, 10, "Lunas")
                            
                            st.success("Pembayaran berhasil diverifikasi!")
                            st.rerun()
                with col2:
                    if bayar['status'] != 'Ditolak':
                        if st.button("❌ Tolak", key=f"tolak_{idx}", use_container_width=True):
                            all_payments = pembayaran_ws.get_all_values()
                            row_num = next(
                                (i+1 for i, row in enumerate(all_payments)
                                 if row[0] == bayar['username'] and row[3] == bayar['bulan'] and row[4] == bayar['tahun']),
                                None
                            )
                            if row_num:
                                pembayaran_ws.update_cell(row_num, 7, "Ditolak")
                            st.warning("Pembayaran ditolak!")
                            st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def manajemen_komplain():
    st.header("📢 Manajemen Komplain")
    
    try:
        komplain_ws = connect_gsheet().worksheet("Komplain")
        komplain_data = komplain_ws.get_all_records()
        
        if not komplain_data:
            st.info("Belum ada data komplain.")
            return
            
        # Filter komplain
        filter_status = st.selectbox("Filter Status", 
                                   ["Semua", "Belum Ditanggapi", "Sudah Ditanggapi"],
                                   key="filter_status_komplain")
        
        # Apply filter
        filtered_komplain = komplain_data
        if filter_status == "Belum Ditanggapi":
            filtered_komplain = [k for k in komplain_data if k.get('status', 'Belum Ditanggapi') == 'Belum Ditanggapi']
        elif filter_status == "Sudah Ditanggapi":
            filtered_komplain = [k for k in komplain_data if k.get('status', 'Belum Ditanggapi') == 'Sudah Ditanggapi']
        
        for idx, komplain in enumerate(filtered_komplain):
            with st.expander(f"{komplain['username']} - {komplain['waktu']}", expanded=False):
                st.markdown(f"""
                <div class="management-card">
                    <p><strong>Username:</strong> {komplain['username']}</p>
                    <p><strong>Waktu:</strong> {komplain['waktu']}</p>
                    <p><strong>Status:</strong> {komplain.get('status', 'Belum Ditanggapi')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("**Isi Komplain:**")
                st.write(komplain['isi_komplain'])
                
                # Tampilkan foto jika ada
                if komplain.get('link_foto'):
                    try:
                        st.image(komplain['link_foto'], caption="Foto Bukti", use_container_width=True)
                    except:
                        st.warning("Gagal memuat foto bukti")
                
                # Form tanggapan
                if komplain.get('status', 'Belum Ditanggapi') == 'Belum Ditanggapi':
                    with st.form(key=f"tanggapan_{idx}"):
                        tanggapan = st.text_area("Tanggapan Admin", key=f"respon_{idx}")
                        if st.form_submit_button("Kirim Tanggapan"):
                            # Update status komplain
                            all_komplain = komplain_ws.get_all_values()
                            row_num = next(
                                (i+1 for i, row in enumerate(all_komplain)
                                 if row[0] == komplain['username'] and row[3] == komplain['waktu']),
                                None
                            )
                            if row_num:
                                komplain_ws.update_cell(row_num, 5, "Sudah Ditanggapi")
                                komplain_ws.update_cell(row_num, 6, tanggapan)
                            st.success("Tanggapan berhasil dikirim!")
                            st.rerun()
                
                # Tampilkan tanggapan jika sudah ditanggapi
                if komplain.get('status') == 'Sudah Ditanggapi' and komplain.get('tanggapan'):
                    st.markdown("**Tanggapan Admin:**")
                    st.write(komplain['tanggapan'])
                
                # Tombol hapus
                if st.button("🗑️ Hapus Komplain", key=f"hapus_{idx}"):
                    all_komplain = komplain_ws.get_all_values()
                    row_num = next(
                        (i+1 for i, row in enumerate(all_komplain)
                         if row[0] == komplain['username'] and row[3] == komplain['waktu']),
                        None
                    )
                    if row_num:
                        komplain_ws.delete_rows(row_num)
                        st.warning("Komplain berhasil dihapus!")
                        st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def verifikasi_booking():
    st.title("✅ Verifikasi Booking Kamar")
    
    # Custom CSS untuk verifikasi booking
    st.markdown("""
    <style>
    .booking-card {
        background: rgba(60,60,60,0.7);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border-left: 4px solid #42A5F5;
    }
    .booking-header {
        color: #42A5F5;
        font-size: 1.2rem;
        margin-bottom: 10px;
    }
    .booking-detail {
        margin-bottom: 5px;
    }
    .action-btn {
        margin-top: 10px;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Load data dari Google Sheets
        booking_ws = connect_gsheet().worksheet("Booking")
        user_ws = connect_gsheet().worksheet("User")
        kamar_ws = connect_gsheet().worksheet("Kamar")
        
        bookings = booking_ws.get_all_records()
        kamar_data = kamar_ws.get_all_records()
        
        if not bookings:
            st.info("Tidak ada booking yang perlu diverifikasi")
            return
            
        st.markdown(f"**Total Booking Menunggu Verifikasi:** {len(bookings)}")
        
        # Filter berdasarkan kamar
        kamar_list = sorted(list(set(b['kamar_dipilih'] for b in bookings if 'kamar_dipilih' in b)))
        selected_kamar = st.selectbox("Filter Berdasarkan Kamar", ["Semua Kamar"] + kamar_list)
        
        # Apply filter
        filtered_bookings = bookings
        if selected_kamar != "Semua Kamar":
            filtered_bookings = [b for b in bookings if b['kamar_dipilih'] == selected_kamar]
        
        for idx, booking in enumerate(filtered_bookings):
            with st.expander(f"Booking #{idx+1}: {booking['nama']} - {booking['kamar_dipilih']}", expanded=False):
                st.markdown(f"""
                <div class="booking-card">
                    <div class="booking-header">Detail Booking</div>
                    <p class="booking-detail"><strong>Nama:</strong> {booking['nama']}</p>
                    <p class="booking-detail"><strong>Kamar Dipilih:</strong> {booking['kamar_dipilih']}</p>
                    <p class="booking-detail"><strong>Kontak:</strong> {booking.get('no_hp_email', '-')}</p>
                    <p class="booking-detail"><strong>Waktu Booking:</strong> {booking.get('waktu_booking', '-')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Tombol aksi
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Setujui Booking", key=f"approve_{idx}", 
                               help="Setujui booking dan buat akun penyewa baru",
                               use_container_width=True):
                        # Buat akun user baru
                        password = "12345678"  # Password default
                        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                        
                        # Data user baru
                        new_user = [
                            booking['nama'],           # username
                            hashed,                   # password_hash
                            "penyewa",                # role
                            booking['nama'],          # nama_lengkap
                            booking.get('no_hp_email', ''),  # no_hp
                            booking['kamar_dipilih'], # kamar
                            "",                       # deskripsi
                            "",                       # foto_profil
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # last_edit
                            "Belum Bayar"             # status_pembayaran
                        ]
                        
                        # Tambahkan user baru
                        user_ws.append_row(new_user)
                        
                        # Update status kamar menjadi "Terisi"
                        for i, kamar in enumerate(kamar_data):
                            if kamar['Nama'] == booking['kamar_dipilih']:
                                kamar_ws.update_cell(i+2, 2, "Terisi")
                                break
                        
                        # Hapus dari daftar booking
                        all_bookings = booking_ws.get_all_values()
                        row_num = next((i+1 for i, row in enumerate(all_bookings) if row[0] == booking['nama'] and row[1] == booking['kamar_dipilih']), None)
                        if row_num:
                            booking_ws.delete_rows(row_num)
                        
                        st.success(f"Booking disetujui! Akun untuk {booking['nama']} telah dibuat dengan password default: {password}")
                        st.rerun()
                
                with col2:
                    if st.button("❌ Tolak Booking", key=f"reject_{idx}",
                               help="Tolak booking dan hapus dari daftar",
                               use_container_width=True):
                        # Hapus dari daftar booking
                        all_bookings = booking_ws.get_all_values()
                        row_num = next((i+1 for i, row in enumerate(all_bookings) if row[0] == booking['nama'] and row[1] == booking['kamar_dipilih']), None)
                        if row_num:
                            booking_ws.delete_rows(row_num)
                            st.warning(f"Booking dari {booking['nama']} telah ditolak dan dihapus")
                            st.rerun()
                
                # Tambahkan informasi kamar
                kamar_info = next((k for k in kamar_data if k['Nama'] == booking['kamar_dipilih']), None)
                if kamar_info:
                    st.markdown("**Informasi Kamar:**")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Harga: Rp {int(kamar_info['Harga']):,}/bulan")
                        st.write(f"Status: {kamar_info['Status']}")
                    with col2:
                        if kamar_info.get('link_foto'):
                            st.image(kamar_info['link_foto'], caption=kamar_info['Nama'], width=150)
    
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses booking: {str(e)}")
        
def profil_saya():
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
    .password-toggle {
        position: absolute;
        right: 10px;
        top: 50%;
        transform: translateY(-50%);
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        # Load data user dari Google Sheets
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        user_data = next((u for u in users if u['username'] == st.session_state.username), None)
        
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
                <p><strong>Edit Profil Terakhir:</strong> {user_data.get('last_edit', '-')}</p>
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
                <p class="profile-detail"><strong>Role:</strong> {user_data['role'].capitalize()}</p>
                {f'<p class="profile-detail"><strong>Kamar:</strong> {user_data.get("kamar", "-")}</p>' if user_data['role'] == 'penyewa' else ''}
                {f'<p class="profile-detail"><strong>Status Pembayaran:</strong> {user_data.get("status_pembayaran", "-")}</p>' if user_data['role'] == 'penyewa' else ''}
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
                if st.session_state.role != 'admin':
                    last_edit_str = user_data.get('last_edit', '')
                    if last_edit_str:
                        try:
                            last_edit = datetime.strptime(last_edit_str, "%Y-%m-%d %H:%M:%S")
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
                    col1, col2, _ = st.columns([1, 1, 2])
                    with col1:
                        if st.form_submit_button("💾 Simpan Perubahan"):
                            # Validasi password
                            if new_password and new_password != confirm_password:
                                st.error("Password tidak cocok!")
                            else:
                                # Upload foto baru jika ada
                                link_foto = upload_to_cloudinary(foto, f"profil_{st.session_state.username}") if foto else user_data.get('foto_profil', '')
                                
                                # Update data di Google Sheets
                                all_users = user_ws.get_all_values()
                                row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == st.session_state.username), None)
                                
                                if row_num:
                                    updates = {
                                        4: nama,  # nama_lengkap
                                        5: f"'{kontak}",  # no_hp (ditambahkan ' untuk format nomor)
                                        6: user_data.get('kamar', ''),  # kamar
                                        7: deskripsi,  # deskripsi
                                        8: link_foto,  # foto_profil
                                        9: datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # last_edit
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
