import streamlit as st
from sheets import get_kamar_data, tambah_booking
import datetime

st.set_page_config(page_title="Kost Online - Tamu", layout="wide")
st.title("Selamat Datang di Kost Online!")

tab1, tab2 = st.tabs(["💺 Lihat Kamar", "📝 Booking Kamar"])
with tab1:
    kamar_data = get_kamar_data()
    if kamar_data:
        for kamar in kamar_data:
            st.subheader(f"Kamar {kamar['Nomor']}")
            st.write(f"✅ Tipe: {kamar['Tipe']}")
            st.write(f"💵 Harga: Rp{kamar['Harga']}/bulan")
            st.write(f"📌 Status: {kamar['Status']}")
            st.markdown("---")
    else:
        st.info("Belum ada data kamar tersedia.")
with tab2:
    st.subheader("Form Booking")

    nama = st.text_input("Nama Lengkap")
    kontak = st.text_input("Kontak (HP/WA)")
    no_kamar = st.selectbox("Pilih Nomor Kamar", [k['Nomor'] for k in kamar_data if k['Status'].lower() == "kosong"])
    tanggal_masuk = st.date_input("Tanggal Masuk", datetime.date.today())

    if st.button("Kirim Booking"):
        if nama and kontak and no_kamar:
            tambah_booking(nama, kontak, no_kamar, tanggal_masuk)
            st.success("Booking berhasil dikirim!")
        else:
            st.warning("Mohon lengkapi semua isian.")
def get_kamar_data():
    sheet = connect_gsheet()
    kamar_ws = sheet.worksheet("kamar")
    records = kamar_ws.get_all_records()
    return records
def tambah_booking(nama, kontak, no_kamar, tanggal_masuk):
    sheet = connect_gsheet()
    booking_ws = sheet.worksheet("booking")
    booking_ws.append_row([nama, kontak, no_kamar, str(tanggal_masuk), "pending"])
