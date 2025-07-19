import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

# Scope yang dibutuhkan untuk akses Drive
SCOPES = ["https://www.googleapis.com/auth/drive"]

# Buat kredensial dari st.secrets
creds = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], scopes=SCOPES
)

# Inisialisasi service Drive
drive_service = build("drive", "v3", credentials=creds)

# Fungsi upload file ke Google Drive
def upload_file_to_drive(file, filename, folder_id):
    file_bytes = io.BytesIO(file.read())
    media = MediaIoBaseUpload(file_bytes, mimetype=file.type)

    file_metadata = {
        "name": filename,
        "parents": [folder_id]
    }

    uploaded = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, webViewLink"
    ).execute()

    return uploaded["id"], uploaded["webViewLink"]

