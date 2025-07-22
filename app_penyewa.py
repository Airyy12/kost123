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

    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    if data.empty:
        data = pd.DataFrame(columns=["username", "bukti", "bulan", "tahun", "waktu", "nominal", "status"])
    user_data = data[data['username'] == USERNAME]

    # --- Custom CSS untuk tab pembayaran ---
    st.markdown("""
    <style>
    .pay-card {
        background: rgba(60,60,60,0.7);
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 18px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        color: #E0E0E0;
    }
    .pay-title {
        font-size: 1.1rem;
        font-weight: bold;
        color: #42A5F5;
        margin-bottom: 8px;
    }
    .pay-row {
        display: flex;
        align-items: center;
        gap: 18px;
        margin-bottom: 10px;
    }
    .pay-label {
        font-weight: bold;
        color: #E0E0E0;
        margin-right: 8px;
    }
    .pay-status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 0.95em;
        margin-right: 8px;
    }
    .status-lunas { background: #66BB6A; color: #fff; }
    .status-belum { background: #EF5350; color: #fff; }
    .status-ditolak { background: #FFA726; color: #222; }
    .status-default { background: #888; color: #fff; }
    .pay-img {
        border-radius: 8px;
        margin-bottom: 8px;
        max-width: 180px;
        max-height: 180px;
    }
    .tab-menu {
        display: flex;
        gap: 24px;
        margin-bottom: 8px;
        align-items: center;
    }
    .tab-item {
        font-size: 1.1rem;
        font-weight: bold;
        color: #E0E0E0;
        cursor: pointer;
        padding: 2px 8px;
        border-radius: 6px;
        transition: background 0.2s;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    .tab-item.active {
        color: #FF5252;
        border-bottom: 3px solid #FF5252;
        background: rgba(255,82,82,0.08);
    }
    .tab-item:not(.active):hover {
        background: rgba(66,165,245,0.08);
        color: #42A5F5;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Tab menu pembayaran ---
    if "pembayaran_tab" not in st.session_state:
        st.session_state.pembayaran_tab = "Upload Bukti"

    tab_col1, tab_col2 = st.columns([1, 1])
    with tab_col1:
        if st.button("📄 Daftar Pembayaran", key="tab_riwayat"):
            st.session_state.pembayaran_tab = "Riwayat Pembayaran"
    with tab_col2:
        if st.button("➕ Upload Bukti", key="tab_upload"):
            st.session_state.pembayaran_tab = "Upload Bukti"

    st.markdown(f"""
    <div class="tab-menu">
        <span class="tab-item {'active' if st.session_state.pembayaran_tab == 'Riwayat Pembayaran' else ''}">📄 Daftar Pembayaran</span>
        <span class="tab-item {'active' if st.session_state.pembayaran_tab == 'Upload Bukti' else ''}">➕ Upload Bukti</span>
    </div>
    <hr style="border:1px solid #FF5252;margin-bottom:16px;">
    """, unsafe_allow_html=True)

    if st.session_state.pembayaran_tab == "Upload Bukti":
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

    elif st.session_state.pembayaran_tab == "Riwayat Pembayaran":
        st.subheader("Riwayat Pembayaran Saya")
        if not user_data.empty:
            sorted_user_data = user_data.sort_values("waktu", ascending=False)
            for i, (idx, row) in enumerate(sorted_user_data.iterrows()):
                status_class = "status-lunas" if str(row['status']).lower() == "lunas" else \
                               "status-ditolak" if str(row['status']).lower() == "ditolak" else \
                               "status-belum" if "belum" in str(row['status']).lower() or "pending" in str(row['status']).lower() or "menunggu" in str(row['status']).lower() else \
                               "status-default"
                st.markdown(f"""
                <div class="pay-card">
                    <div class="pay-title">🗓️ {row['bulan']} {row['tahun']}</div>
                    <div class="pay-row">
                        <span class="pay-label">Nominal:</span> Rp{int(row['nominal']):,}
                    </div>
                    <div class="pay-row">
                        <span class="pay-label">Status:</span>
                        <span class="pay-status-badge {status_class}">{row['status']}</span>
                    </div>
                    <div class="pay-row">
                        <span class="pay-label">Waktu Upload:</span> {format_waktu(row['waktu'])}
                    </div>
                    {"<img src='" + row['bukti'] + "' class='pay-img'>" if row['bukti'] else ""}
                    <div class="pay-row">
                        <!-- Tombol hapus di luar HTML, gunakan key unik dari index asli DataFrame -->
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Hapus Pembayaran", key=f"hapus_{idx}"):
                    ws.delete_rows(idx+2)  # header + index asli
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
            with st.expander(f"{format_waktu(row['waktu'])} - {row['status']}"):
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
    st.markdown(f"**Terakhir Edit:** {format_waktu(row['last_edit'])}")

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
