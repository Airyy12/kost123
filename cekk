import streamlit as st
import gspread
import json
import tempfile
from oauth2client.service_account import ServiceAccountCredentials

st.title("🔍 Cek Koneksi ke Google Sheets")

try:
    # Scope untuk API
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]

    # Ambil secrets
    creds_dict = json.loads(st.secrets["gcp_service_account"])

    # Simpan sementara
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmpfile:
        json.dump(creds_dict, tmpfile)
        tmpfile.flush()
        creds = ServiceAccountCredentials.from_json_keyfile_name(tmpfile.name, scope)

    # Autentikasi dan buka spreadsheet
    client = gspread.authorize(creds)
    sheet = client.open("kost-db")  # ganti jika nama sheet berbeda

    st.success("✅ Berhasil terhubung ke Google Sheets!")

    # Tampilkan nama semua worksheet
    st.subheader("Daftar Worksheet:")
    for ws in sheet.worksheets():
        st.write(f"- {ws.title}")

    # Ambil data dari worksheet pertama
    ws = sheet.get_worksheet(0)
    data = ws.get_all_records()

    st.subheader(f"Data dari Sheet: {ws.title}")
    st.dataframe(data)

except Exception as e:
    st.error("❌ Gagal mengakses Google Sheets")
    st.exception(e)
