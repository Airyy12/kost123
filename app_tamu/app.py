import streamlit as st
from sheets import get_kamar_list, simpan_booking
from drive import upload_file_to_drive
from datetime import datetime

st.set_page_config(page_title="Kost Online", layout="wide")
st.title("🏠 Daftar Kamar Kost")

# Ambil data kamar dari Google Sheets
kamar_list = get_kamar_list()

for kamar in kamar_list:
    with st.expander(f"{kamar['nama']} - {kamar['harga']}"):
        st.image(kamar.get("gambar_url", ""), width=300)
        st.markdown(f"**Fasilitas:** {kamar['fasilitas']}")
        st.markdown(f"**Status:** {kamar['status']}")

        if kamar['status'].lower() == "kosong":
            with st.form(key=f"form_booking_{kamar['nama']}"):
                st.subheader("Booking Kamar Ini")
                nama = st.text_input("Nama Lengkap")
                no_hp = st.text_input("No HP / WA")
                ktp_file = st.file_uploader("Upload Foto KTP", type=["jpg", "jpeg", "png"])

                submit = st.form_submit_button("Kirim Booking")
                if submit:
                    if nama and no_hp and ktp_file:
                        file_url = upload_file_to_drive(ktp_file, folder="ktp")
                        simpan_booking(nama, no_hp, kamar['nama'], file_url)
                        st.success("Booking berhasil dikirim! Admin akan segera menghubungi Anda.")
                    else:
                        st.warning("Mohon lengkapi semua data.")
