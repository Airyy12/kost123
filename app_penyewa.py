import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from sheets import connect_gsheet
from sheets import load_sheet_data, connect_gsheet
from cloudinary_upload import upload_to_cloudinary

USERNAME = st.session_state.username

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
    st.markdown("<h1 style='text-align: center;'>👋 Selamat datang, {}</h1>".format(
        st.session_state.get("nama", "Penyewa")), unsafe_allow_html=True)
    st.markdown("---")

    # Muat semua data yang dibutuhkan
    user_df = load_sheet_data("User")
    kamar_df = load_sheet_data("Kamar")
    pembayaran_df = load_sheet_data("Pembayaran")
    komplain_df = load_sheet_data("Komplain")

    # Ambil data penyewa saat ini berdasarkan username login
    username = st.session_state.get("username")
    data_user = user_df[user_df['username'] == username].iloc[0]

    # Ambil info kamar
    data_kamar = kamar_df[kamar_df['Nama'] == data_user['kamar']].iloc[0]

    # Ambil pembayaran terakhir
    data_pembayaran = pembayaran_df[pembayaran_df['username'] == username]
    pembayaran_terakhir = data_pembayaran.sort_values("waktu", ascending=False).head(1).to_dict("records")

    # Ambil komplain terakhir
    data_komplain = komplain_df[komplain_df['username'] == username]
    riwayat_komplain = data_komplain.sort_values("waktu", ascending=False).head(5)

    # ────────────────────────────────────────────────
    # Layout: 2x2 Grid
    col1, col2 = st.columns(2)

    with col1:
        with st.container():
            st.markdown("### 👤 Profil Penyewa")
            st.image(data_user['foto_profil'], width=150)
            st.markdown(f"- **Nama:** {data_user['nama_lengkap']}")
            st.markdown(f"- **No HP:** {data_user['no_hp']}")
            st.markdown(f"- **Kamar:** {data_user['kamar']}")
            st.markdown(f"- **Deskripsi:** {data_user['deskripsi']}")
            st.markdown(f"- **Status Pembayaran:** `{data_user['status_pembayaran']}`")
            st.markdown(f"- ⏱️ Edit profil terakhir: `{data_user['last_edit']}`")

    with col2:
        with st.container():
            st.markdown("### 🛏️ Info Kamar")
            st.image(data_kamar['link_foto'], width=150)
            st.markdown(f"- **Nama:** {data_kamar['Nama']}")
            st.markdown(f"- **Status:** {data_kamar['Status']}")
            st.markdown(f"- **Harga:** Rp{data_kamar['Harga']:,}")
            st.markdown(f"- **Deskripsi:** {data_kamar['Deskripsi']}")

    col3, col4 = st.columns(2)

    with col3:
        with st.container():
            st.markdown("### 💬 Riwayat Komplain")
            if riwayat_komplain.empty:
                st.info("Belum ada komplain.")
            else:
                for _, row in riwayat_komplain.iterrows():
                    st.markdown(f"- `{row['waktu']}`: {row['isi_komplain']}")

    with col4:
        with st.container():
            st.markdown("### 💳 Pembayaran Terakhir")
            if pembayaran_terakhir:
                p = pembayaran_terakhir[0]
                st.image(p["bukti"], width=150)
                st.markdown(f"- **Bulan:** {p['bulan']} {p['tahun']}")
                st.markdown(f"- **Nominal:** Rp{p['nominal']:,}")
                st.markdown(f"- **Status:** `{p['status']}`")
                st.markdown(f"- **Waktu:** `{p['waktu']}`")
            else:
                st.info("Belum ada pembayaran tercatat.")

    st.markdown("---")


def show_pembayaran():
    st.title("💸 Pembayaran")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Pembayaran")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.subheader("Upload Bukti Pembayaran")
    with st.form("form_bayar"):
        bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        tahun = st.selectbox("Tahun", [datetime.now().year - 1, datetime.now().year])
        nominal = st.number_input("Nominal (Rp)", min_value=10000)
        bukti = st.file_uploader("Upload Bukti Pembayaran")
        submit = st.form_submit_button("Kirim")

        if submit and bukti:
            url = upload_to_cloudinary(bukti, f"bukti_{USERNAME}_{bulan}_{tahun}_{datetime.now().isoformat()}")
            ws.append_row([USERNAME, url, bulan, tahun, datetime.now().isoformat(), nominal, "Menunggu Verifikasi"])
            st.success("Bukti pembayaran berhasil dikirim!")
            st.experimental_rerun()

    st.markdown("---")
    st.subheader("Riwayat Pembayaran Saya")
    if not user_data.empty:
        for i, row in user_data.iterrows():
            with st.expander(f"{row['bulan']} {row['tahun']} - Rp {row['nominal']:,} [{row['status']}]"):
                st.image(row['bukti'], width=300)
                if st.button(f"Hapus Pembayaran {i}", key=f"hapus_{i}"):
                    ws.delete_rows(i+2)  # header + index
                    st.success("Dihapus.")
                    st.experimental_rerun()
    else:
        st.info("Belum ada pembayaran.")


def show_komplain():
    st.title("📢 Komplain")
    sheet = connect_gsheet()
    ws = sheet.worksheet("Komplain")
    data = pd.DataFrame(ws.get_all_records())
    user_data = data[data['username'] == USERNAME]

    st.subheader("Kirim Komplain Baru")
    with st.form("form_komplain"):
        isi = st.text_area("Isi Komplain")
        foto = st.file_uploader("Upload Foto (Opsional)")
        submit = st.form_submit_button("Kirim Komplain")

        if submit and isi:
            url = upload_to_cloudinary(foto, f"komplain_{USERNAME}_{datetime.now().isoformat()}") if foto else ""
            ws.append_row([USERNAME, isi, url, datetime.now().isoformat(), "Terkirim"])
            st.success("Komplain berhasil dikirim!")
            st.experimental_rerun()

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
                    st.experimental_rerun()
    else:
        st.info("Belum ada komplain.")


def show_profil():
    st.title("👤 Profil Saya")
    sheet = connect_gsheet()
    ws = sheet.worksheet("User")
    data = pd.DataFrame(ws.get_all_records())
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
            st.experimental_rerun()
