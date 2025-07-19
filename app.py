import streamlit as st
from sheets import connect_gsheet

st.title("Aplikasi Manajemen Kost")

# Login sederhana (sementara)
email = st.text_input("Masukkan email")
if st.button("Login"):
    sheet = connect_gsheet()
    users_sheet = sheet.worksheet("users")
    users = users_sheet.get_all_records()
    user = next((u for u in users if u["email"] == email), None)
    
    if user:
        st.success(f"Halo, {user['nama']}! Role Anda: {user['role']}")
        if user['role'] == "admin":
            st.subheader("Dashboard Admin")
            # Tambahkan fitur admin di sini
        elif user['role'] == "penyewa":
            st.subheader("Dashboard Penyewa")
            # Tambahkan fitur penyewa di sini
    else:
        st.error("Email tidak ditemukan.")
