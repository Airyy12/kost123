import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Scope untuk Google Sheets dan Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Autentikasi dengan kredensial dari Streamlit Secrets
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)

client = gspread.authorize(credentials)

# Ganti dengan nama file Google Sheets kamu
SPREADSHEET_NAME = "kost-db"
spreadsheet = client.open(SPREADSHEET_NAME)

# Nama-nama sheet
SHEET_USERS = "users"
SHEET_KAMAR = "kamar"
SHEET_PENYEWA = "penyewa"
SHEET_PEMBAYARAN = "pembayaran"

# Fungsi untuk ambil worksheet
def get_worksheet(sheet_name):
    return spreadsheet.worksheet(sheet_name)

# Fungsi bantu ambil semua data dari sheet sebagai list of dicts
def get_all_records(sheet_name):
    sheet = get_worksheet(sheet_name)
    return sheet.get_all_records()

# Fungsi untuk menambahkan data ke sheet
def append_row(sheet_name, row_data):
    sheet = get_worksheet(sheet_name)
    sheet.append_row(row_data)

# Fungsi update sel
def update_cell(sheet_name, row, col, value):
    sheet = get_worksheet(sheet_name)
    sheet.update_cell(row, col, value)
