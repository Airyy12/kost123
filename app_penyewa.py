import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

# --- Custom CSS untuk Tampilan Modern ---
st.markdown("""
<style>
    /* General Body Styling */
    body {
        font-family: 'Inter', sans-serif; /* Modern font */
        background-color: #f0f2f6; /* Light gray background */
        color: #333333;
    }

    /* Streamlit Main Container Adjustments */
    .stApp {
        background-color: #f0f2f6;
    }

    .css-1d391kg { /* Main content area */
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 5%;
        padding-right: 5%;
    }

    /* Card Styling */
    .card {
        background-color: #ffffff; /* White background for cards */
        border-radius: 12px; /* More rounded corners */
        box-shadow: 0 6px 15px rgba(0, 0, 0, 0.08); /* Softer, more prominent shadow */
        padding: 25px;
        margin-bottom: 25px;
        transition: transform 0.2s ease-in-out; /* Smooth hover effect */
    }

    .card:hover {
        transform: translateY(-5px); /* Lift effect on hover */
    }

    .card-title {
        font-size: 1.35em; /* Slightly larger title */
        font-weight: 700; /* Bolder */
        color: #2c3e50; /* Dark blue/gray for titles */
        margin-bottom: 20px;
        border-bottom: 2px solid #e0e0e0; /* Subtle separator */
        padding-bottom: 10px;
    }

    /* Image Styling within Cards */
    .stImage > img {
        border-radius: 8px; /* Slightly rounded images */
        max-width: 100%; /* Ensure images fit their container */
        height: auto;
        display: block;
        margin-left: auto;
        margin-right: auto;
        object-fit: cover; /* Cover the area, crop if necessary */
    }

    /* Message Boxes (Success, Warning, Info) */
    .success-box {
        background-color: #e6ffed; /* Lighter green */
        color: #1a6e35; /* Darker green text */
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #c8e6c9;
    }

    .warning-box {
        background-color: #fff8e1; /* Lighter yellow */
        color: #8c7100; /* Darker yellow text */
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #ffe0b2;
    }

    .info-box {
        background-color: #e0f2f7; /* Lighter blue */
        color: #0d47a1; /* Darker blue text */
        padding: 18px;
        border-radius: 8px;
        margin-bottom: 20px;
        border: 1px solid #b3e5fc;
    }

    /* Status Badges */
    .status-pending, .status-menunggu-verifikasi {
        background-color: #ffe082; /* Soft yellow */
        color: #553c02;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block; /* For proper padding */
    }
    .status-verified, .status-terverifikasi {
        background-color: #a5d6a7; /* Soft green */
        color: #1b5e20;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    .status-rejected, .status-ditolak {
        background-color: #ef9a9a; /* Soft red */
        color: #c62828;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }
    .status-terkirim {
        background-color: #bbdefb; /* Soft blue */
        color: #1a237e;
        padding: 4px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
    }

    /* Streamlit Widgets Styling */
    .stButton > button {
        background-color: #4CAF50; /* Green submit button */
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 1em;
        font-weight: bold;
        border: none;
        transition: background-color 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #45a049;
    }
    .stButton > button:disabled {
        background-color: #cccccc;
        cursor: not-allowed;
    }

    .stTextInput > div > div > input, .stTextArea > div > div > textarea, .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        padding: 10px;
        box-shadow: inset 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Expander Styling */
    .streamlit-expanderContent {
        padding: 15px;
        background-color: #fdfdfd;
        border-radius: 0 0 8px 8px;
        border: 1px solid #e0e0e0;
        border-top: none;
    }
    .streamlit-expanderHeader {
        background-color: #e8f5e9; /* Light green for expander header */
        color: #2e7d32;
        border-radius: 8px;
        padding: 12px 20px;
        font-weight: bold;
        border: 1px solid #c8e6c9;
        margin-bottom: 0; /* Remove space between header and content */
    }
    
    /* Custom Header for Pages */
    .page-header {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); /* Gradient background */
        color: white;
        border-radius: 15px;
        margin-bottom: 40px;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
    }
    .page-header h1 {
        color: white;
        font-size: 2.8em;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .page-header p {
        color: #e0e0e0;
        font-size: 1.1em;
    }

</style>
""", unsafe_allow_html=True)

# --- Fungsi Utama untuk Penyewa ---
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

# --- Dashboard ---
import streamlit as st
import pandas as pd
from datetime import datetime
from sheets import load_sheet_data
from cloudinary_upload import upload_to_cloudinary

def show_dashboard():
    st.markdown("<h2 style='text-align:center;'>📊 Dashboard Penyewa Kost</h2>", unsafe_allow_html=True)
    username = st.session_state.get("username")

    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    komplain_df = load_sheet_data("Komplain")
    pembayaran_df = load_sheet_data("Pembayaran")

    # Data user login
    user_data = user_df[user_df["username"] == username].iloc[0]

    # Grid layout 2x2
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.subheader("👤 Profil Penyewa")
            st.image(user_data["foto_profil"], width=100)
            st.write(f"**Nama:** {user_data['nama_lengkap']}")
            st.write(f"**No HP:** {user_data['no_hp']}")
            st.write(f"**Kamar:** {user_data['kamar']}")
            st.write(f"**Deskripsi:** {user_data['deskripsi']}")
            st.caption(f"🕒 Terakhir edit: {user_data['last_edit']}")

    with col2:
        with st.container():
            st.subheader("🛏️ Info Kamar")
            kamar_user = kamar_df[kamar_df["Nama"] == user_data["kamar"]]
            if not kamar_user.empty:
                kamar_info = kamar_user.iloc[0]
                st.image(kamar_info["link_foto"], width=120)
                st.write(f"**Harga:** Rp{int(kamar_info['Harga']):,}")
                st.write(f"**Status:** {kamar_info['Status']}")
                st.write(f"**Deskripsi:** {kamar_info['Deskripsi']}")
            else:
                st.warning("Data kamar tidak ditemukan.")

    col3, col4 = st.columns(2)

    with col3:
        with st.container():
            st.subheader("💬 Riwayat Komplain")
            if "username" in komplain_df.columns:
                komplain_user = komplain_df[komplain_df["username"] == username]
                if not komplain_user.empty:
                    st.dataframe(komplain_user[["isi_komplain", "status", "waktu"]].sort_values(by="waktu", ascending=False))
                else:
                    st.info("Belum ada komplain.")
            else:
                st.info("Kolom 'username' belum tersedia di sheet Komplain.")

    with col4:
        with st.container():
            st.subheader("💳 Pembayaran Terakhir")
            if "username" in pembayaran_df.columns:
                bayar_user = pembayaran_df[pembayaran_df["username"] == username]
                if not bayar_user.empty:
                    bayar_terakhir = bayar_user.sort_values(by="waktu", ascending=False).iloc[0]
                    st.write(f"**Bulan:** {bayar_terakhir['bulan']} {bayar_terakhir['tahun']}")
                    st.write(f"**Nominal:** Rp{int(bayar_terakhir['nominal']):,}")
                    st.write(f"**Status:** {bayar_terakhir['status']}")
                    st.image(bayar_terakhir["bukti"], width=150)
                else:
                    st.info("Belum ada data pembayaran.")
            else:
                st.info("Kolom 'username' belum tersedia di sheet Pembayaran.")

def run_penyewa(menu):
    if menu == "Dashboard":
        show_dashboard()
    elif menu == "Pembayaran":
        st.write("💳 Halaman Pembayaran (dalam pengembangan)")
    elif menu == "Komplain":
        st.write("💬 Halaman Komplain (dalam pengembangan)")
    elif menu == "Profil":
        st.write("👤 Halaman Profil (dalam pengembangan)")
    else:
        st.error("Menu tidak dikenal.")


# --- Pembayaran ---
def show_pembayaran():
    st.markdown(f"""
    <div class='page-header'>
        <h1>💸 Pembayaran Sewa</h1>
        <p>Upload bukti pembayaran dan lihat riwayat pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.expander("📤 **Upload Bukti Pembayaran Baru**", expanded=True):
        with st.form("form_bayar", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                                             "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            with cols[1]:
                tahun = st.selectbox("Tahun", [datetime.now().year - 1, datetime.now().year, datetime.now().year + 1])
            
            nominal = st.number_input("Nominal Pembayaran (Rp)", min_value=10000, step=100000, format="%d")
            bukti = st.file_uploader("Upload Bukti Transfer", type=['jpg', 'jpeg', 'png'])
            
            submitted = st.form_submit_button("Kirim Bukti Pembayaran", use_container_width=True)
            
            if submitted:
                if not bukti:
                    st.markdown("<div class='warning-box'>Mohon upload bukti transfer.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner('Mengupload bukti pembayaran...'):
                        try:
                            url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}_{datetime.now().isoformat()}")
                            ws.append_row([USERNAME, url, bulan, tahun, datetime.now().isoformat(), nominal, "Menunggu Verifikasi"])
                            st.markdown("<div class='success-box'>Bukti pembayaran berhasil dikirim! Admin akan memverifikasi pembayaran Anda.</div>", unsafe_allow_html=True)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Terjadi kesalahan saat mengupload: {e}. Mohon coba lagi.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h2 style='color: #2c3e50; text-align: center; margin-bottom: 30px;'>📋 Riwayat Pembayaran Saya</h2>", unsafe_allow_html=True)
    
    if not user_data.empty:
        # Sort data agar yang terbaru di atas
        sorted_user_data = user_data.sort_values("waktu", ascending=False)
        for i, row in sorted_user_data.iterrows():
            status_class = "status-" + str(row['status']).lower().replace(" ", "-") # Ensure status is string
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} - {row['status']}"):
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Waktu Upload:</b> {row['waktu']}</p>
                </div>
                """, unsafe_allow_html=True)
                if pd.notna(row['bukti']) and row['bukti']: # Check if bukti exists
                    st.image(row['bukti'], use_column_width=True)
                else:
                    st.markdown("<div class='info-box'>Tidak ada gambar bukti pembayaran.</div>", unsafe_allow_html=True)
                
                # Gunakan key unik untuk tombol hapus
                if st.button(f"Hapus Pembayaran", key=f"hapus_bayar_{row.name}"): # Using row.name (index) for unique key
                    # Hapus baris berdasarkan indeks asli di worksheet, perlu +2 karena header dan 0-indexed
                    original_index = data.index[data['waktu'] == row['waktu']].tolist()[0] + 2 
                    ws.delete_rows(original_index)
                    st.markdown("<div class='success-box'>Data pembayaran berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum memiliki riwayat pembayaran.</div>", unsafe_allow_html=True)

# --- Komplain ---
def show_komplain():
    st.markdown(f"""
    <div class='page-header'>
        <h1>📢 Komplain & Keluhan</h1>
        <p>Sampaikan keluhan Anda dan lihat riwayat komplain</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    with st.expander("📝 **Buat Komplain Baru**", expanded=True):
        with st.form("form_komplain", clear_on_submit=True):
            isi = st.text_area("Deskripsi Komplain/Keluhan",
                               placeholder="Tuliskan keluhan Anda secara detail...", height=150)
            foto = st.file_uploader("Upload Foto Pendukung (Opsional)",
                                     type=['jpg', 'jpeg', 'png'])
            
            submitted = st.form_submit_button("Kirim Komplain", use_container_width=True)
            
            if submitted:
                if not isi:
                    st.markdown("<div class='warning-box'>Mohon isi deskripsi komplain.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner('Mengirim komplain...'):
                        try:
                            url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
                            ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
                            st.markdown("<div class='success-box'>Komplain berhasil dikirim! Admin akan menindaklanjuti keluhan Anda.</div>", unsafe_allow_html=True)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Terjadi kesalahan saat mengirim komplain: {e}. Mohon coba lagi.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h2 style='color: #2c3e50; text-align: center; margin-bottom: 30px;'>📜 Riwayat Komplain Saya</h2>", unsafe_allow_html=True)
    
    if not user_data.empty:
        sorted_user_data = user_data.sort_values("waktu", ascending=False)
        for i, row in sorted_user_data.iterrows():
            status_class = "status-" + str(row['status']).lower().replace(" ", "-") # Ensure status is string
            with st.expander(f"{row['waktu']} - Status: {row['status']}"):
                st.markdown(f"""
                <div style='margin-bottom: 15px;'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Isi Komplain:</b></p>
                    <div style='padding: 10px; background-color: #f8f9fa; border-radius: 5px; border: 1px solid #e0e0e0;'>
                        {row['isi_komplain']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if pd.notna(row['link_foto']) and row['link_foto']: # Check if foto exists
                    st.image(row['link_foto'], use_column_width=True)
                
                if st.button(f"Hapus Komplain", key=f"hapus_komplain_{row.name}"): # Using row.name (index) for unique key
                    # Hapus baris berdasarkan indeks asli di worksheet, perlu +2 karena header dan 0-indexed
                    original_index = data.index[data['waktu'] == row['waktu']].tolist()[0] + 2 
                    ws.delete_rows(original_index)
                    st.markdown("<div class='success-box'>Komplain berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum pernah mengirim komplain.</div>", unsafe_allow_html=True)

# --- Profil Saya ---
def show_profil():
    st.markdown(f"""
    <div class='page-header'>
        <h1>👤 Profil Saya</h1>
        <p>Kelola informasi profil Anda</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("User")
    data = pd.DataFrame(ws.get_all_records())
    
    # Pastikan username ada di dataframe
    if USERNAME not in data['username'].values:
        st.error("Data profil tidak ditemukan. Silakan login ulang.")
        return

    idx = data.index[data['username'] == USERNAME].tolist()[0]
    row = data.iloc[idx]

    # Menggunakan layout kolom untuk tampilan yang lebih rapi
    col_img, col_form = st.columns([1, 2])
    
    with col_img:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        # Tampilkan foto profil saat ini
        st.image(row['foto_profil'] if pd.notna(row['foto_profil']) and row['foto_profil'] else 'https://via.placeholder.com/150?text=No+Photo', width=180)
        st.markdown(f"<p style='text-align: center; margin-top: 15px;'><b>Terakhir Diubah:</b> {row['last_edit']}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col_form:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        with st.form("edit_profil"):
            st.markdown("<div class='card-title'>📝 Edit Profil</div>", unsafe_allow_html=True)
            
            nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
            no_hp = st.text_input("Nomor HP", value=row['no_hp'])
            deskripsi = st.text_area("Deskripsi Tambahan", value=row['deskripsi'], height=100)
            foto_baru = st.file_uploader("Ubah Foto Profil", type=['jpg', 'jpeg', 'png'])
            
            # Cek apakah bisa edit (7 hari setelah terakhir edit)
            edit_allowed = True
            warning_message = ""
            try:
                last_edit_dt = datetime.fromisoformat(row['last_edit'])
                time_since_last_edit = datetime.now() - last_edit_dt
                if time_since_last_edit < timedelta(days=7):
                    edit_allowed = False
                    remaining_time = timedelta(days=7) - time_since_last_edit
                    hours, remainder = divmod(remaining_time.total_seconds(), 3600)
                    minutes, seconds = divmod(remainder, 60)
                    warning_message = f"""
                    <div class='warning-box'>
                        Anda hanya bisa mengedit profil sekali dalam 7 hari. 
                        Terakhir edit: {row['last_edit']}.
                        Anda bisa mengedit lagi dalam **{int(hours)} jam {int(minutes)} menit**.
                    </div>
                    """
            except ValueError: # Handle cases where last_edit might be invalid format
                warning_message = "<div class='info-box'>Tanggal terakhir edit tidak valid. Anda dapat mengedit profil Anda.</div>"
                pass # Allow editing if date format is bad
            
            if warning_message:
                st.markdown(warning_message, unsafe_allow_html=True)
            
            submitted = st.form_submit_button("Simpan Perubahan", use_container_width=True, disabled=not edit_allowed)
            
            if submitted:
                with st.spinner('Menyimpan perubahan...'):
                    try:
                        url_foto_profil = upload_to_cloudinary(foto_baru, f"foto_profil_{USERNAME}_{datetime.now().isoformat()}") if foto_baru else row['foto_profil']
                        
                        # Update data di Google Sheet
                        # Pastikan kolom sesuai dengan urutan di Google Sheet Anda
                        # Misal: nama_lengkap di kolom D, no_hp E, deskripsi F, foto_profil G, last_edit I
                        ws.update_acell(f"D{idx+2}", nama)
                        ws.update_acell(f"E{idx+2}", no_hp)
                        ws.update_acell(f"F{idx+2}", deskripsi)
                        ws.update_acell(f"G{idx+2}", url_foto_profil)
                        ws.update_acell(f"I{idx+2}", datetime.now().isoformat())
                        
                        st.markdown("<div class='success-box'>Profil berhasil diperbarui!</div>", unsafe_allow_html=True)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat memperbarui profil: {e}. Mohon coba lagi.")
        st.markdown("</div>", unsafe_allow_html=True)
