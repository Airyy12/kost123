import streamlit as st
from sheets import get_data, add_booking
from drive import upload_file

st.title("Kost Putri Aman & Nyaman")

# Ambil data kamar dari Google Sheets
kamar = get_data(sheet_name="Kamar")

for k in kamar:
    st.subheader(k["nama"])
    st.image(k["foto_url"])
    st.write(f"Harga: {k['harga']}/bulan")
    st.write(k["deskripsi"])
    if st.button(f"Booking {k['nama']}", key=k["nama"]):
        st.session_state['kamar_dipilih'] = k["nama"]
        st.switch_page("booking")

# Form booking nanti ditaruh di halaman/form booking tersendiri
