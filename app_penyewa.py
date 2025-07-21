import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

# CSS kustom untuk tampilan yang lebih baik
st.markdown("""
<style>
    .card {
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        margin-bottom: 20px;
        background-color: white;
    }
    .card-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 15px;
        color: #2c3e50;
    }
    .stImage {
        border-radius: 10px;
    }
    .success-box {
        background-color: #d4edda;
        color: #155724;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .warning-box {
        background-color: #fff3cd;
        color: #856404;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .info-box {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 20px;
    }
    .status-pending {
        color: #ffc107;
        font-weight: bold;
    }
    .status-verified {
        color: #28a745;
        font-weight: bold;
    }
    .status-rejected {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def run_penyewa(menu):
    if menu == "Beranda":
        show_dashboard()
    elif menu == "Pembayaran":
        show_pembayaran()
    elif menu == "Komplain":
        show_komplain()
    elif menu == "Profil Saya":
        show_profil()
    elif menu == "Keluar":
        st.session_state.login_status = False
        st.session_state.username = ""
        st.session_state.role = None
        st.session_state.menu = None
        st.rerun()

def show_dashboard():
    # Header dengan animasi
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: #2c3e50;'>👋 Selamat datang, {st.session_state.get("nama", "Penyewa")}</h1>
        <p style='color: #7f8c8d;'>Dashboard Informasi Kamar dan Pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    # Muat semua data yang dibutuhkan
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    # Ambil data penyewa saat ini
    username = st.session_state.get("username", "")
    data_user = user_df[user_df['username'] == username].iloc[0]
    data_kamar = kamar_df[kamar_df['Nama'] == data_user['kamar']].iloc[0]
    data_pembayaran = pembayaran_df[pembayaran_df['username'] == username]
    pembayaran_terakhir = data_pembayaran.sort_values("waktu", ascending=False).head(1).to_dict("records")
    data_komplain = komplain_df[komplain_df['username'] == username]
    riwayat_komplain = data_komplain.sort_values("waktu", ascending=False).head(5)

    # Layout menggunakan columns dan cards
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown("<div class='card'><div class='card-title'>👤 Profil Penyewa</div>", unsafe_allow_html=True)
            st.image(data_user['foto_profil'], width=200, use_column_width=False)
            st.markdown(f"""
            <div style='margin-top: 15px;'>
                <p><b>Nama:</b> {data_user['nama_lengkap']}</p>
                <p><b>No HP:</b> {data_user['no_hp']}</p>
                <p><b>Kamar:</b> {data_user['kamar']}</p>
                <p><b>Status Pembayaran:</b> <span class='status-{data_user['status_pembayaran'].lower()}'>{data_user['status_pembayaran']}</span></p>
                <p><b>Terakhir Diubah:</b> {data_user['last_edit']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        with st.container():
            st.markdown("<div class='card'><div class='card-title'>🛏️ Info Kamar</div>", unsafe_allow_html=True)
            st.image(data_kamar['link_foto'], width=200, use_column_width=False)
            st.markdown(f"""
            <div style='margin-top: 15px;'>
                <p><b>Nama Kamar:</b> {data_kamar['Nama']}</p>
                <p><b>Status:</b> {data_kamar['Status']}</p>
                <p><b>Harga:</b> Rp{data_kamar['Harga']:,}/bulan</p>
                <p><b>Fasilitas:</b> {data_kamar['Deskripsi']}</p>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        with st.container():
            st.markdown("<div class='card'><div class='card-title'>💬 Riwayat Komplain Terakhir</div>", unsafe_allow_html=True)
            if riwayat_komplain.empty:
                st.markdown("<div class='info-box'>Belum ada komplain</div>", unsafe_allow_html=True)
            else:
                for _, row in riwayat_komplain.iterrows():
                    status_class = "status-" + row['status'].lower().replace(" ", "-")
                    st.markdown(f"""
                    <div style='margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;'>
                        <p><b>{row['waktu']}</b> - <span class='{status_class}'>{row['status']}</span></p>
                        <p>{row['isi_komplain']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        with st.container():
            st.markdown("<div class='card'><div class='card-title'>💳 Pembayaran Terakhir</div>", unsafe_allow_html=True)
            if pembayaran_terakhir:
                p = pembayaran_terakhir[0]
                status_class = "status-" + p['status'].lower().replace(" ", "-")
                st.image(p["bukti"], width=200, use_column_width=False)
                st.markdown(f"""
                <div style='margin-top: 15px;'>
                    <p><b>Periode:</b> {p['bulan']} {p['tahun']}</p>
                    <p><b>Nominal:</b> Rp{p['nominal']:,}</p>
                    <p><b>Status:</b> <span class='{status_class}'>{p['status']}</span></p>
                    <p><b>Waktu Upload:</b> {p['waktu']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("<div class='warning-box'>Belum ada pembayaran tercatat</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

def show_pembayaran():
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: #2c3e50;'>💸 Pembayaran Sewa</h1>
        <p style='color: #7f8c8d;'>Upload bukti pembayaran dan lihat riwayat pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    with st.expander("📤 Upload Bukti Pembayaran Baru", expanded=True):
        with st.form("form_bayar"):
            cols = st.columns(2)
            with cols[0]:
                bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                             "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            with cols[1]:
                tahun = st.selectbox("Tahun", [datetime.now().year - 1, datetime.now().year, datetime.now().year + 1])
            
            nominal = st.number_input("Nominal Pembayaran (Rp)", min_value=10000, step=100000)
            bukti = st.file_uploader("Upload Bukti Transfer", type=['jpg', 'jpeg', 'png'])
            
            submitted = st.form_submit_button("Kirim Bukti Pembayaran", use_container_width=True)
            
            if submitted and bukti:
                with st.spinner('Mengupload bukti pembayaran...'):
                    url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}_{datetime.now().isoformat()}")
                    ws.append_row([USERNAME, url, bulan, tahun, datetime.now().isoformat(), nominal, "Menunggu Verifikasi"])
                    st.markdown("<div class='success-box'>Bukti pembayaran berhasil dikirim! Admin akan memverifikasi pembayaran Anda.</div>", unsafe_allow_html=True)
                    st.rerun()

    st.markdown("---")
    st.markdown("<h3 style='color: #2c3e50;'>📋 Riwayat Pembayaran Saya</h3>", unsafe_allow_html=True)
    
    if not user_data.empty:
        for i, row in user_data.sort_values("waktu", ascending=False).iterrows():
            status_class = "status-" + row['status'].lower().replace(" ", "-")
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} - {row['status']}"):
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Waktu Upload:</b> {row['waktu']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(row['bukti'], use_column_width=True)
                
                if st.button(f"Hapus Pembayaran", key=f"hapus_{i}"):
                    ws.delete_rows(i+2)
                    st.markdown("<div class='success-box'>Data pembayaran berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum memiliki riwayat pembayaran.</div>", unsafe_allow_html=True)

def show_komplain():
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: #2c3e50;'>📢 Komplain & Keluhan</h1>
        <p style='color: #7f8c8d;'>Sampaikan keluhan Anda dan lihat riwayat komplain</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    with st.expander("📝 Buat Komplain Baru", expanded=True):
        with st.form("form_komplain"):
            isi = st.text_area("Deskripsi Komplain/Keluhan", 
                             placeholder="Tuliskan keluhan Anda secara detail...")
            foto = st.file_uploader("Upload Foto Pendukung (Opsional)", 
                                  type=['jpg', 'jpeg', 'png'])
            
            submitted = st.form_submit_button("Kirim Komplain", use_container_width=True)
            
            if submitted and isi:
                with st.spinner('Mengirim komplain...'):
                    url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
                    ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
                    st.markdown("<div class='success-box'>Komplain berhasil dikirim! Admin akan menindaklanjuti keluhan Anda.</div>", unsafe_allow_html=True)
                    st.rerun()

    st.markdown("---")
    st.markdown("<h3 style='color: #2c3e50;'>📜 Riwayat Komplain Saya</h3>", unsafe_allow_html=True)
    
    if not user_data.empty:
        for i, row in user_data.sort_values("waktu", ascending=False).iterrows():
            status_class = "status-" + row['status'].lower().replace(" ", "-")
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Isi Komplain:</b></p>
                    <div style='padding: 10px; background-color: #f8f9fa; border-radius: 5px;'>
                        {row['isi_komplain']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if row['link_foto']:
                    st.image(row['link_foto'], use_column_width=True)
                
                if st.button(f"Hapus Komplain", key=f"hapus_komplain_{i}"):
                    ws.delete_rows(i+2)
                    st.markdown("<div class='success-box'>Komplain berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum pernah mengirim komplain.</div>", unsafe_allow_html=True)

def show_profil():
    st.markdown(f"""
    <div style='text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px; margin-bottom: 30px;'>
        <h1 style='color: #2c3e50;'>👤 Profil Saya</h1>
        <p style='color: #7f8c8d;'>Kelola informasi profil Anda</p>
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
            st.markdown("<div class='card-title'>📝 Edit Profil</div>", unsafe_allow_html=True)
            
            nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
            no_hp = st.text_input("Nomor HP", value=row['no_hp'])
            deskripsi = st.text_area("Deskripsi Tambahan", value=row['deskripsi'])
            foto = st.file_uploader("Ubah Foto Profil", type=['jpg', 'jpeg', 'png'])
            
            # Cek apakah bisa edit (7 hari setelah terakhir edit)
            edit_allowed = True
            try:
                last = datetime.fromisoformat(row['last_edit'])
                if datetime.now() - last < timedelta(days=7):
                    edit_allowed = False
                    st.markdown(f"""
                    <div class='warning-box'>
                        Anda hanya bisa mengedit profil sekali dalam 7 hari. 
                        Terakhir edit: {row['last_edit']}
                    </div>
                    """, unsafe_allow_html=True)
            except:
                pass
            
            submitted = st.form_submit_button("Simpan Perubahan", use_container_width=True, disabled=not edit_allowed)
            
            if submitted:
                with st.spinner('Menyimpan perubahan...'):
                    url = upload_to_cloudinary(foto, f"foto_profil_{USERNAME}_{datetime.now().isoformat()}") if foto else row['foto_profil']
                    ws.update(f"D{idx+2}:G{idx+2}", [[nama, no_hp, deskripsi, url]])
                    ws.update_acell(f"I{idx+2}", datetime.now().isoformat())
                    st.markdown("<div class='success-box'>Profil berhasil diperbarui!</div>", unsafe_allow_html=True)
                    st.rerun()
