import streamlit as st
import pandas as pd
from sheets import load_sheet_data
from cloudinary_upload import upload_to_cloudinary
from datetime import datetime

st.set_page_config(page_title="Admin Kost123", layout="wide")

sheet_user = "User"
sheet_kamar = "Kamar"
sheet_booking = "Booking"
sheet_pembayaran = "Pembayaran"
sheet_komplain = "Komplain"

def admin_dashboard():
    st.title("Dashboard Admin")
    st.write("Selamat datang di halaman admin Kost123!")

def kelola_kamar():
    st.title("Kelola Kamar")

    df_kamar = load_sheet_data(sheet_kamar)
    st.dataframe(df_kamar)

    with st.expander("Tambah Kamar Baru"):
        with st.form("form_tambah_kamar"):
            nama = st.text_input("Nama Kamar")
            harga = st.number_input("Harga", min_value=0)
            deskripsi = st.text_area("Deskripsi")
            foto = st.file_uploader("Upload Foto Kamar", type=["jpg", "png"])
            submitted = st.form_submit_button("Tambah")

            if submitted:
                link_foto = upload_to_cloudinary(foto) if foto else ""
                new_row = {
                    "Nama": nama,
                    "Status": "Kosong",
                    "Harga": harga,
                    "Deskripsi": deskripsi,
                    "link_foto": link_foto
                }
                df_kamar = pd.concat([df_kamar, pd.DataFrame([new_row])], ignore_index=True)
                st.success("Kamar berhasil ditambahkan!")
                st.rerun()

def manajemen():
    st.title("Manajemen Penyewa")

    df_user = load_sheet_data(sheet_user)
    penyewa = df_user[df_user["role"] == "penyewa"]

    for idx, penyewa_row in penyewa.iterrows():
        with st.expander(f"👤 {penyewa_row['nama_lengkap']} - Kamar: {penyewa_row['kamar']}"):
            with st.form(f"form_penyewa_{idx}"):
                nama_lengkap = st.text_input("Nama Lengkap", value=penyewa_row.get("nama_lengkap", ""))
                no_hp = st.text_input("No HP", value=penyewa_row.get("no_hp", ""))
                deskripsi = st.text_area("Deskripsi", value=penyewa_row.get("deskripsi", ""))
                status_pembayaran = st.selectbox("Status Pembayaran", ["Lunas", "Belum"], index=0 if penyewa_row.get("status_pembayaran") == "Lunas" else 1)
                submit = st.form_submit_button("💾 Simpan Perubahan", key=f"simpan_penyewa_{idx}")

                if submit:
                    df_user.at[idx, "nama_lengkap"] = nama_lengkap
                    df_user.at[idx, "no_hp"] = no_hp
                    df_user.at[idx, "deskripsi"] = deskripsi
                    df_user.at[idx, "status_pembayaran"] = status_pembayaran
                    df_user.at[idx, "last_edit"] = datetime.now().isoformat()
                    st.success("Data berhasil diperbarui")
                    st.rerun()

    st.header("Manajemen Pembayaran")
    df_pembayaran = load_sheet_data(sheet_pembayaran)

    for idx, bayar in df_pembayaran.iterrows():
        with st.expander(f"💰 {bayar['username']} - {bayar['bulan']} {bayar['tahun']}"):
            with st.form(f"form_bayar_{idx}"):
                nominal = st.number_input("Nominal", value=int(bayar.get("nominal", 0)))
                status = st.selectbox("Status", ["Terverifikasi", "Pending"], index=0 if bayar.get("status") == "Terverifikasi" else 1)
                submit_bayar = st.form_submit_button("💾 Simpan Pembayaran", key=f"submit_bayar_{idx}")

                if submit_bayar:
                    df_pembayaran.at[idx, "nominal"] = nominal
                    df_pembayaran.at[idx, "status"] = status
                    st.success("Pembayaran berhasil diperbarui")
                    st.rerun()

    st.header("Manajemen Komplain")
    df_komplain = load_sheet_data(sheet_komplain)

    for idx, komplain in df_komplain.iterrows():
        with st.expander(f"📢 {komplain['username']} - {komplain['waktu']}"):
            st.write(f"**Isi Komplain:** {komplain.get('isi_komplain', '-')}")
            st.image(komplain.get("link_foto", ""), width=300)
            status = st.selectbox("Status", ["Pending", "Ditanggapi"], index=0 if komplain.get("status") == "Pending" else 1, key=f"status_komplain_{idx}")
            tanggapan = st.text_area("Tanggapan", value=komplain.get("tanggapan", ""), key=f"tanggapan_{idx}")
            if st.button("💬 Simpan Tanggapan", key=f"tanggapi_{idx}"):
                df_komplain.at[idx, "status"] = status
                df_komplain.at[idx, "tanggapan"] = tanggapan
                st.success("Tanggapan disimpan")
                st.rerun()

def run_admin(menu):
    if menu == "Dashboard Admin":
        admin_dashboard()
    elif menu == "Kelola Kamar":
        kelola_kamar()
    elif menu == "Manajemen":
        manajemen()
    elif menu == "Kelola Kamar":
        kelola_kamar()
    elif menu == "Manajemen":
        manajemen()
