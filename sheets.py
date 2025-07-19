import gspread
import streamlit as st

gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
sh = gc.open("kost-db")

def get_data(sheet_name="Kamar"):
    worksheet = sh.worksheet(sheet_name)
    return worksheet.get_all_records()

def add_booking(nama, nohp, kamar, link_ktp):
    worksheet = sh.worksheet("Booking")
    worksheet.append_row([nama, nohp, kamar, link_ktp])
