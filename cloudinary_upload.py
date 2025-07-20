import cloudinary
import cloudinary.uploader
import streamlit as st

cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

def upload_image(file, folder="kost123"):
    result = cloudinary.uploader.upload(file, folder=folder)
    return result['secure_url']
