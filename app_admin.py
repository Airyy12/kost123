import streamlit as st
from sheets import get_bookings, get_data

st.title("Dashboard Admin Kost")

if st.text_input("Masukkan password admin", type="password") == "admin123":
    st.success("Login berhasil")
    bookings = get_bookings()
    st.write("Data Booking:")
    st.dataframe(bookings)
else:
    st.warning("Masukkan password untuk akses dashboard")
