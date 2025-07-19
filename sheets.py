import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        st.secrets["gcp_service_account"],
        scope
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["gsheet_id"])
    return sheet
