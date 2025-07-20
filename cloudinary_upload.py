import cloudinary
import cloudinary.uploader
import streamlit as st

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name = st.secrets["cloudinary"]["dhjw0n163"],
    api_key = st.secrets["cloudinary"]["325875229438527"],
    api_secret = st.secrets["cloudinary"]["L0lX5djSMjalU09ZQp7czlLmxU8"]
)

def upload_file_to_cloudinary(file, filename):
    result = cloudinary.uploader.upload(file, public_id=filename, overwrite=True)
    return result['secure_url']
