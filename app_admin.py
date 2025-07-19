import streamlit as st
from sheets import get_kamar_list, get_booking_list

st.set_page_config(page_title="Admin Kost", layout="wide")
st.title("🔒 Dashboard Admin & Penyewa")

# 👤 Login sederhana (nanti bisa dikembangkan jadi login aman)
role = st.selectbox("Masuk sebagai:", ["Admin", "Penyewa"])

if role == "Admin":
    st.header("📋 Daftar Kamar")
    kamar_list = get_kamar_list()
    for kamar in kamar_list:
        st.write(f"- {kamar['nama']} | {kamar['status']} | {kamar['harga']}")

    st.header("📥 Booking Masuk")
    booking_list = get_booking_list()
    for b in booking_list:
        st.write(f"👤 {b['nama']} - {b['kamar']} - 📞 {b['no_hp']}")
        st.markdown(f"[🔗 Lihat KTP]({b['ktp_url']})")

elif role == "Penyewa":
    st.info("📌 Fitur penyewa (upload bukti bayar, lihat kamar disewa) menyusul...")

