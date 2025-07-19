import streamlit as st
from sheets import connect_gsheet

st.title("📊 Dashboard Admin & Penyewa")

sheet = connect_gsheet()
kamar_ws = sheet.worksheet("Kamar")
booking_ws = sheet.worksheet("Booking")

st.subheader("Data Booking")
data = booking_ws.get_all_records()
for item in data:
    st.write(item)

st.subheader("Data Kamar")
kamar_data = kamar_ws.get_all_records()
for k in kamar_data:
    st.write(k)
