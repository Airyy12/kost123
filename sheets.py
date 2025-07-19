import streamlit as st
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials
import json

def get_drive():
    credentials_dict = json.loads(st.secrets["gcp_service_account"])
    scope = ["https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
    
    gauth = GoogleAuth()
    gauth.credentials = creds
    return GoogleDrive(gauth)

def upload_file_to_drive(file, filename):
    drive = get_drive()
    folder_id = st.secrets["gdrive_folder_id"]
    gfile = drive.CreateFile({
        'parents': [{'id': folder_id}],
        'title': filename
    })
    gfile.SetContentFile(file)
    gfile.Upload()
    return gfile['id']
