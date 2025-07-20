import cloudinary
import cloudinary.uploader
import streamlit as st
import tempfile

# Konfigurasi Cloudinary dari streamlit secrets
cloudinary.config(
    cloud_name=st.secrets["cloudinary"]["cloud_name"],
    api_key=st.secrets["cloudinary"]["api_key"],
    api_secret=st.secrets["cloudinary"]["api_secret"]
)

def upload_to_cloudinary(file, filename):
    if file is None:
        return ""

    # Simpan sementara file upload
    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file.getbuffer())
    temp_file.close()

    # Upload ke Cloudinary
    response = cloudinary.uploader.upload(temp_file.name, public_id=filename, overwrite=True)

    return response.get("secure_url", "")
