import streamlit as st
import sys
import os
sys.path.append(os.path.abspath(".."))  # agar bisa impor sheets.py dan drive.py

from sheets import get_kamar_data, tambah_booking

st.set_page_config(page_title="Kost Online - Tamu", layout="wide")

st.title("🏡 Daftar Kamar Kos")

# Ambil data kamar dari Google Sheets
kamar_data = get_kamar_data()

if not kamar_data:
    st.warning("Belum ada data kamar yang tersedia.")
else:
    for kamar in kamar_data:
        nama_kamar = kamar.get("nama", "Kamar Tanpa Nama")
        harga = kamar.get("harga", "Tidak ada harga")
        deskripsi = kamar.get("deskripsi", "")
        foto_url = kamar.get("foto_url", "")

        with st.container():
            st.subheader(nama_kamar)
            if foto_url:
                st.image(foto_url, width=300)
            st.write(f"💰 Harga: {harga}")
            st.write(f"📝 {deskripsi}")
            st.markdown("---")

    st.header("📋 Form Booking Kamar")

    nama = st.text_input("Nama Lengkap")
    no_hp = st.text_input("No. HP")
    pilih_kamar = st.selectbox("Pilih Kamar", [k["nama"] for k in kamar_data])

    if st.button("Kirim Booking"):
        if not nama or not no_hp or not pilih_kamar:
            st.error("Mohon lengkapi semua kolom.")
        else:
            # Tambahkan ke Google Sheets
            tambah_booking(nama, no_hp, pilih_kamar)

            st.success("Booking berhasil dikirim!")
            st.balloons()
