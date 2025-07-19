from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import streamlit as st

def upload_file(file, folder_id):
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")  # atau via service account
    drive = GoogleDrive(gauth)
    f = drive.CreateFile({'parents': [{'id': folder_id}]})
    f.SetContentFile(file.name)
    f.Upload()
    return f['alternateLink']
