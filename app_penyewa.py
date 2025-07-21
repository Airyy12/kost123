import streamlit as st
import pandas as pd
from sheets import connect_gsheet, load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime, timedelta
import bcrypt
import requests

# --- Custom CSS mirip admin ---
st.markdown("""
<style>
body { background-color: #1e1e1e; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; }
.info-card, .card, .p-card {
    background: rgba(60,60,60,0.7);
    padding: 18px;
    border-radius: 12px;
    margin-bottom: 18px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.18);
}
.p-card-title {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 12px;
    color: #E0E0E0;
}
.p-card-content {
    color: #E0E0E0;
}
.p-card-time {
    font-size: 14px;
    color: #B0B0B0;
    margin-bottom: 5px;
}
.status-pending, .status-menunggu-verifikasi {
    background-color: #ffe082;
    color: #553c02;
    padding: 4px 10px;
    border-radius: 5px;
    font-weight: bold;
    display: inline-block;
}
.status-verified, .status-terverifikasi, .status-lunas {
    background-color: #a5d6a7;
    color: #1b5e20;
    padding: 4px 10px;
    border-radius: 5px;
    font-weight: bold;
    display: inline-block;
}
.status-rejected, .status-ditolak {
    background-color: #ef9a9a;
    color: #c62828;
    padding: 4px 10px;
    border-radius: 5px;
    font-weight: bold;
    display: inline-block;
}
.status-terkirim {
    background-color: #bbdefb;
    color: #1a237e;
    padding: 4px 10px;
    border-radius: 5px;
    font-weight: bold;
    display: inline-block;
}
.success-box {
    background: #388e3c22;
    color: #a5d6a7;
    border-left: 5px solid #66bb6a;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 18px;
}
.warning-box {
    background: #ffa72622;
    color: #ffe082;
    border-left: 5px solid #ffa726;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 18px;
}
.info-box {
    background: #1976d222;
    color: #90caf9;
    border-left: 5px solid #1976d2;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 18px;
}
.stImage > img {
    border-radius: 8px;
    max-width: 100%;
    object-fit: cover;
}
.p-header {
    text-align: center;
    padding: 28px 0 18px 0;
    background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
    color: white;
    border-radius: 15px;
    margin-bottom: 32px;
    box-shadow: 0 8px 20px rgba(0,0,0,0.18);
}
.p-header h1 {
    color: white;
    font-size: 2.1em;
    margin-bottom: 8px;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.18);
}
.p-header p {
    color: #e0e0e0;
    font-size: 1.08em;
}
.stButton > button {
    background-color: #42A5F5;
    color: white;
    border-radius: 8px;
    padding: 10px 20px;
    font-size: 1em;
    font-weight: bold;
    border: none;
    transition: background-color 0.3s;
}
.stButton > button:hover {
    background-color: #1976d2;
}
.stButton > button:disabled {
    background-color: #cccccc;
    cursor: not-allowed;
}
</style>
""", unsafe_allow_html=True)

def run_penyewa(menu):
    if menu in ("Beranda", "Dashboard"):
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
    st.markdown(f"""
    <div class='p-header'>
        <h1>👋 Selamat datang, {st.session_state.get("nama", "Penyewa")}</h1>
        <p>Dashboard Informasi Kamar dan Pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    # Muat semua data yang dibutuhkan
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    # Ambil data penyewa saat ini
    username = st.session_state.get("username", "")
    user_rows = user_df[user_df['username'] == username]
    if user_rows.empty:
        st.markdown("<div class='warning-box'>Data user tidak ditemukan. Silakan hubungi admin.</div>", unsafe_allow_html=True)
        return
    data_user = user_rows.iloc[0]

    kamar_rows = kamar_df[kamar_df['Nama'] == data_user['kamar']]
    if kamar_rows.empty:
        st.markdown("<div class='warning-box'>Data kamar tidak ditemukan. Silakan hubungi admin.</div>", unsafe_allow_html=True)
        return
    data_kamar = kamar_rows.iloc[0]

    data_pembayaran = pembayaran_df[pembayaran_df['username'] == username]
    pembayaran_terakhir = data_pembayaran.sort_values("waktu", ascending=False).head(1).to_dict("records")
    data_komplain = komplain_df[komplain_df['username'] == username]
    riwayat_komplain = data_komplain.sort_values("waktu", ascending=False).head(5)

    # --- Modern horizontal info cards ---
    st.markdown("<div style='margin-bottom: 18px;'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 2])
    with col1:
        if data_user.get('foto_profil'):
            st.image(data_user['foto_profil'], width=64)
    with col2:
        st.markdown(f"""
        <div style='font-size:1.1em;'><b>{data_user.get('nama_lengkap','-')}</b></div>
        <div style='color:#aaa;font-size:0.95em;'>Kamar: <b>{data_user.get('kamar','-')}</b></div>
        <div style='color:#aaa;font-size:0.95em;'>No HP: {data_user.get('no_hp','-')}</div>
        """, unsafe_allow_html=True)
    with col3:
        status = data_user.get('status_pembayaran','-')
        status_class = "status-" + status.lower()
        st.markdown(f"""
        <div style='text-align:right;'>
            <span class='{status_class}' style='font-size:1.1em;'>{status}</span>
            <div style='color:#aaa;font-size:0.85em;'>Terakhir edit: {data_user.get('last_edit','-')}</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Info kamar ringkas ---
    st.markdown("<div class='info-card' style='padding:12px 18px;'>", unsafe_allow_html=True)
    colk1, colk2 = st.columns([1, 4])
    with colk1:
        if data_kamar.get('link_foto'):
            st.image(data_kamar['link_foto'], width=56)
    with colk2:
        st.markdown(f"""
        <b>{data_kamar.get('Nama','-')}</b> | Status: <span style='color:#42A5F5'>{data_kamar.get('Status','-')}</span><br>
        <span style='font-size:0.97em;'>Harga: <b>Rp{data_kamar.get('Harga',0):,}/bulan</b></span><br>
        <span style='font-size:0.95em;color:#aaa;'>Fasilitas: {data_kamar.get('Deskripsi','-')}</span>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Highlight pembayaran & komplain terakhir ---
    colA, colB = st.columns(2)
    with colA:
        st.markdown("<div class='info-card' style='padding:12px 18px;'>", unsafe_allow_html=True)
        st.markdown("<div class='p-card-title' style='font-size:1.08em;'>💳 Pembayaran Terakhir</div>", unsafe_allow_html=True)
        if pembayaran_terakhir:
            p = pembayaran_terakhir[0]
            status_class = "status-" + str(p.get('status','')).lower().replace(" ", "-")
            st.markdown(f"""
            <div style='display:flex;align-items:center;gap:10px;'>
                {f"<img src='{p.get('bukti','')}' width='48' style='border-radius:6px;'/>" if p.get('bukti') else ""}
                <div>
                    <b>{p.get('bulan','-')} {p.get('tahun','-')}</b><br>
                    <span style='font-size:0.97em;'>Rp{p.get('nominal',0):,}</span><br>
                    <span class='{status_class}'>{p.get('status','-')}</span>
                </div>
            </div>
            <div style='font-size:0.85em;color:#aaa;'>Upload: {p.get('waktu','-')}</div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Belum ada pembayaran</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with colB:
        st.markdown("<div class='info-card' style='padding:12px 18px;'>", unsafe_allow_html=True)
        st.markdown("<div class='p-card-title' style='font-size:1.08em;'>💬 Komplain Terakhir</div>", unsafe_allow_html=True)
        if not riwayat_komplain.empty:
            row = riwayat_komplain.iloc[0]
            status_class = "status-" + str(row.get('status','')).lower().replace(" ", "-")
            st.markdown(f"""
            <div>
                <span class='{status_class}'>{row.get('status','-')}</span>
                <div style='font-size:0.93em;color:#aaa;margin-bottom:3px;'>{row.get('waktu','-')}</div>
                <div style='font-size:0.97em;'>{row.get('isi_komplain','-')}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Belum ada komplain</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Riwayat komplain & pembayaran (ringkas, 2 kolom) ---
    st.markdown("---")
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<div class='p-card-title'>📜 Riwayat Komplain</div>", unsafe_allow_html=True)
        if riwayat_komplain.empty:
            st.markdown("<div class='info-box'>Belum ada komplain</div>", unsafe_allow_html=True)
        else:
            for _, row in riwayat_komplain.iterrows():
                status_class = "status-" + str(row.get('status','')).lower().replace(" ", "-")
                st.markdown(f"""
                <div style='margin-bottom: 10px; padding: 8px; background: #23272f; border-radius: 8px;'>
                    <span class='p-card-time'>{row.get('waktu','-')}</span>
                    <span class='{status_class}' style='margin-left:8px;'>{row.get('status','-')}</span>
                    <div style='font-size:0.97em;'>{row.get('isi_komplain','-')}</div>
                </div>
                """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.markdown("<div class='p-card-title'>📋 Riwayat Pembayaran</div>", unsafe_allow_html=True)
        if not data_pembayaran.empty:
            for _, p in data_pembayaran.sort_values("waktu", ascending=False).head(5).iterrows():
                status_class = "status-" + str(p.get('status','')).lower().replace(" ", "-")
                st.markdown(f"""
                <div style='margin-bottom: 10px; padding: 8px; background: #23272f; border-radius: 8px;display:flex;align-items:center;gap:10px;'>
                    {f"<img src='{p.get('bukti','')}' width='36' style='border-radius:5px;'/>" if p.get('bukti') else ""}
                    <div>
                        <b>{p.get('bulan','-')} {p.get('tahun','-')}</b> <span class='{status_class}' style='margin-left:8px;'>{p.get('status','-')}</span><br>
                        <span style='font-size:0.95em;'>Rp{p.get('nominal',0):,}</span>
                        <div style='font-size:0.85em;color:#aaa;'>Upload: {p.get('waktu','-')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div class='info-box'>Belum ada pembayaran</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

def show_pembayaran():
    st.markdown(f"""
    <div class='p-header'>
        <h1>💸 Pembayaran Sewa</h1>
        <p>Upload bukti pembayaran dan lihat riwayat pembayaran</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
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
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3 style='color: #E0E0E0; text-align: center;'>📋 Riwayat Pembayaran Saya</h3>", unsafe_allow_html=True)
    if not user_data.empty:
        for i, row in user_data.sort_values("waktu", ascending=False).iterrows():
            status_class = "status-" + row['status'].lower().replace(" ", "-")
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} - {row['status']}"):
                st.markdown(f"""
                <div class='p-card-content'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Waktu Upload:</b> {row['waktu']}</p>
                </div>
                """, unsafe_allow_html=True)
                st.image(row['bukti'], use_container_width=True)
                if st.button(f"Hapus Pembayaran", key=f"hapus_{i}"):
                    ws.delete_rows(i+2)
                    st.markdown("<div class='success-box'>Data pembayaran berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum memiliki riwayat pembayaran.</div>", unsafe_allow_html=True)

def show_komplain():
    st.markdown(f"""
    <div class='p-header'>
        <h1>📢 Komplain & Keluhan</h1>
        <p>Sampaikan keluhan Anda dan lihat riwayat komplain</p>
    </div>
    """, unsafe_allow_html=True)

    USERNAME = st.session_state.get("username", "")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.markdown("<div class='info-card'>", unsafe_allow_html=True)
    with st.expander("📝 Buat Komplain Baru", expanded=True):
        with st.form("form_komplain"):
            isi = st.text_area("Deskripsi Komplain/Keluhan", placeholder="Tuliskan keluhan Anda secara detail...")
            foto = st.file_uploader("Upload Foto Pendukung (Opsional)", type=['jpg', 'jpeg', 'png'])
            submitted = st.form_submit_button("Kirim Komplain", use_container_width=True)
            if submitted and isi:
                with st.spinner('Mengirim komplain...'):
                    url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
                    ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
                    st.markdown("<div class='success-box'>Komplain berhasil dikirim! Admin akan menindaklanjuti keluhan Anda.</div>", unsafe_allow_html=True)
                    st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3 style='color: #E0E0E0; text-align: center;'>📜 Riwayat Komplain Saya</h3>", unsafe_allow_html=True)
    if not user_data.empty:
        for i, row in user_data.sort_values("waktu", ascending=False).iterrows():
            status_class = "status-" + row['status'].lower().replace(" ", "-")
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(f"""
                <div class='p-card-content'>
                    <p><b>Status:</b> <span class='{status_class}'>{row['status']}</span></p>
                    <p><b>Isi Komplain:</b></p>
                    <div style='padding: 10px; background: #23272f; border-radius: 5px;'>
                        {row['isi_komplain']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if row['link_foto']:
                    st.image(row['link_foto'], use_container_width=True)
                if st.button(f"Hapus Komplain", key=f"hapus_komplain_{i}"):
                    ws.delete_rows(i+2)
                    st.markdown("<div class='success-box'>Komplain berhasil dihapus.</div>", unsafe_allow_html=True)
                    st.rerun()
    else:
        st.markdown("<div class='info-box'>Anda belum pernah mengirim komplain.</div>", unsafe_allow_html=True)

def show_profil():
    st.markdown(f"""
    <div class='p-header'>
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
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        st.image(row['foto_profil'], width=180, use_container_width=True)
        st.markdown(f"<p style='text-align: center;'><b>Terakhir Diubah:</b> {row['last_edit']}</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='info-card'>", unsafe_allow_html=True)
        with st.form("edit_profil"):
            st.markdown("<div class='p-card-title'>📝 Edit Profil</div>", unsafe_allow_html=True)
            nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
            no_hp = st.text_input("Nomor HP", value=row['no_hp'])
            deskripsi = st.text_area("Deskripsi Tambahan", value=row['deskripsi'])
            foto = st.file_uploader("Ubah Foto Profil", type=['jpg', 'jpeg', 'png'])
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
        st.markdown("</div>", unsafe_allow_html=True)
