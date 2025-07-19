import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import tempfile

def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
    
    # Ambil data dari st.secrets
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    
    # Simpan sementara ke file .json agar bisa dibaca oleh Google API
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmpfile:
        json.dump(creds_dict, tmpfile)
        tmpfile.flush()
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmpfile.name, scope)
    
    # Autentikasi dan buka spreadsheet
    client = gspread.authorize(creds)
    sheet = client.open("kost-db")
    return sheet
