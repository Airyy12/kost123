import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

def upload_to_drive(file, filename, mimetype="image/jpeg"):
    creds = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    service = build("drive", "v3", credentials=creds)

    media = MediaIoBaseUpload(io.BytesIO(file.read()), mimetype=mimetype)
    file_metadata = {
        "name": filename,
        "parents": [st.secrets["gdrive_folder_id"]],
    }

    uploaded = service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id"
    ).execute()

    return f"https://drive.google.com/uc?id={uploaded['id']}"
