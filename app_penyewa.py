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
    riwayat_komplain = data_komplain.sort_values("waktu", ascending=False).head(2)

    # Statistik
    total_kamar = len(kamar_df)
    kamar_kosong = len(kamar_df[kamar_df['Status'] == 'Kosong'])
    kamar_terisi = len(kamar_df[kamar_df['Status'] == 'Terisi'])
    status_pembayaran = data_user.get('status_pembayaran', '-')

    # Custom CSS
    st.markdown("""
    <style>
    .info-card {
        background: #fff;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    .card-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
        color: #2c3e50;
    }
    .card-content {
        color: #444;
        font-size: 16px;
        margin-bottom: 4px;
    }
    .card-time {
        font-size: 14px;
        color: #888;
        margin-bottom: 5px;
    }
    .komplain-card, .pembayaran-card {
        background: #f7f7fa;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 15px;
        border-left: 5px solid #42A5F5;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"<h1 style='text-align:center;'>👋 Selamat datang, {data_user['nama_lengkap']}</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # Statistik Kamar & Status
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🏘️ Total Kamar</div>
            <div class="card-content">{total_kamar}</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🛏️ Kamar Kosong</div>
            <div class="card-content">{kamar_kosong}</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">🧑 Kamar Terisi</div>
            <div class="card-content">{kamar_terisi}</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="info-card">
            <div class="card-title">💳 Status Pembayaran</div>
            <div class="card-content">{status_pembayaran}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Layout 3 kolom: Profil, Komplain, Pembayaran
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 👤 Profil Saya")
        st.markdown(f"""
        <div class="info-card">
            <img src="{data_user['foto_profil'] if data_user['foto_profil'] else 'https://via.placeholder.com/150'}" width="120" style="border-radius:8px;margin-bottom:10px;">
            <div class="card-title">{data_user['nama_lengkap']}</div>
            <div class="card-content">No HP: {data_user['no_hp']}</div>
            <div class="card-content">Kamar: {data_user['kamar']}</div>
            <div class="card-content">Deskripsi: {data_user['deskripsi']}</div>
            <div class="card-content">Terakhir Edit: {data_user['last_edit']}</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("### 🛏️ Info Kamar")
        st.markdown(f"""
        <div class="info-card">
            <img src="{data_kamar['link_foto'] if data_kamar['link_foto'] else 'https://via.placeholder.com/150'}" width="120" style="border-radius:8px;margin-bottom:10px;">
            <div class="card-title">{data_kamar['Nama']}</div>
            <div class="card-content">Status: {data_kamar['Status']}</div>
            <div class="card-content">Harga: Rp{int(data_kamar['Harga']):,}/bulan</div>
            <div class="card-content">{data_kamar['Deskripsi']}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 💬 Komplain Terbaru")
        if riwayat_komplain.empty:
            st.info("Belum ada komplain.")
        else:
            for _, row in riwayat_komplain.iterrows():
                st.markdown(f"""
                <div class="komplain-card">
                    <div class="card-title">📅 {row['waktu']}</div>
                    <div class="card-content">{row['isi_komplain']}</div>
                    <div class="card-content">Status: {row['status']}</div>
                </div>
                """, unsafe_allow_html=True)

    with col3:
        st.markdown("### 💳 Pembayaran Terakhir")
        if pembayaran_terakhir:
            p = pembayaran_terakhir[0]
            st.markdown(f"""
            <div class="pembayaran-card">
                <img src="{p['bukti'] if p['bukti'] else 'https://via.placeholder.com/150'}" width="120" style="border-radius:8px;margin-bottom:10px;">
                <div class="card-title">{p['bulan']} {p['tahun']}</div>
                <div class="card-content">Nominal: Rp{int(p['nominal']):,}</div>
                <div class="card-content">Status: {p['status']}</div>
                <div class="card-content">Waktu: {p['waktu']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Belum ada pembayaran tercatat.")

    st.markdown("---")


def show_pembayaran():
    USERNAME = st.session_state.get("username", "")
    st.title("💸 Pembayaran")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "bukti", "bulan", "tahun", "waktu", "nominal", "status"])
    user_data = data[data['username'] == USERNAME]

    # --- Form Input Pembayaran ---
    st.subheader("Upload Bukti Pembayaran")
    with st.form("form_bayar"):
        bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        tahun = st.selectbox("Tahun", [datetime.now().year - 1, datetime.now().year, datetime.now().year + 1])
        nominal = st.number_input("Nominal (Rp)", min_value=10000)
        bukti = st.file_uploader("Upload Bukti Pembayaran", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Kirim")

        if submit:
            if not bukti:
                st.warning("Mohon upload bukti pembayaran.")
            else:
                url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}_{datetime.now().isoformat()}")
                ws.append_row([USERNAME, url, bulan, tahun, datetime.now().isoformat(), nominal, "Menunggu Verifikasi"])
                st.success("Bukti pembayaran berhasil dikirim!")
                st.rerun()

    # --- Riwayat Pembayaran ---
    st.markdown("---")
    st.subheader("Riwayat Pembayaran Saya")
    if not user_data.empty:
        for i, row in user_data.iterrows():
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} [{row['status']}]"):
                if row['bukti']:
                    st.image(row['bukti'], width=300)
                st.markdown(f"- Waktu: `{row['waktu']}`")
                if st.button(f"Hapus Pembayaran {i}", key=f"hapus_{i}"):
                    ws.delete_rows(i+2)  # header + index
                    st.success("Dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada pembayaran.")

def show_komplain():
    USERNAME = st.session_state.get("username", "")
    st.title("📢 Komplain")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "isi_komplain", "link_foto", "waktu", "status"])
    user_data = data[data['username'] == USERNAME]

    # --- Form Input Komplain ---
    st.subheader("Kirim Komplain Baru")
    with st.form("form_komplain"):
        isi = st.text_area("Isi Komplain")
        foto = st.file_uploader("Upload Foto (Opsional)", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Kirim Komplain")

        if submit:
            if not isi:
                st.warning("Mohon isi komplain terlebih dahulu.")
            else:
                url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
                ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
                st.success("Komplain berhasil dikirim!")
                st.rerun()

    # --- Riwayat Komplain ---
    st.markdown("---")
    st.subheader("Riwayat Komplain Saya")
    if not user_data.empty:
        for i, row in user_data.iterrows():
            with st.expander(f"{row['waktu']} - {row['status']}"):
                st.markdown(row['isi_komplain'])
                if row['link_foto']:
                    st.image(row['link_foto'], width=300)
                if st.button(f"Hapus Komplain {i}", key=f"hapus_komplain_{i}"):
                    ws.delete_rows(i+2)
                    st.success("Komplain dihapus.")
                    st.rerun()
    else:
        st.info("Belum ada komplain.")


def show_profil():
    USERNAME = st.session_state.get("username", "")
    st.title("👤 Profil Saya")
    sheet = connect_gsheet()
    ws = sheet.worksheet("User")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "nama_lengkap", "no_hp", "kamar", "deskripsi", "foto_profil", "status_pembayaran", "last_edit"])
    idx = data.index[data['username'] == USERNAME].tolist()[0]
    row = data.iloc[idx]

    st.image(row['foto_profil'], width=150)
    st.markdown(f"**Terakhir Edit:** {row['last_edit']}")

    edit_allowed = True
    try:
        last = datetime.fromisoformat(row['last_edit'])
        if datetime.now() - last < timedelta(days=7):
            edit_allowed = False
    except:
        pass

    with st.form("edit_profil"):
        nama = st.text_input("Nama Lengkap", value=row['nama_lengkap'])
        no_hp = st.text_input("No HP", value=row['no_hp'])
        deskripsi = st.text_area("Deskripsi", value=row['deskripsi'])
        foto = st.file_uploader("Ganti Foto Profil")
        submit = st.form_submit_button("Simpan Perubahan")

        if not edit_allowed:
            st.warning("Profil hanya bisa diedit sekali setiap 7 hari.")
            st.stop()

        if submit:
            url = upload_to_cloudinary(foto, f"foto_profil_{USERNAME}_{datetime.now().isoformat()}") if foto else row['foto_profil']
            ws.update(f"D{idx+2}:G{idx+2}", [[nama, no_hp, deskripsi, url]])
            ws.update_acell(f"I{idx+2}", datetime.now().isoformat())
            st.success("Profil berhasil diperbarui!")
            st.rerun()

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
    
