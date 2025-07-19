import streamlit as st
from supabase import create_client
import os

# Koneksi ke Supabase
@st.cache_resource
def init_db():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)

db = init_db()

# Tampilan
st.title("🏠 Aplikasi Manajemen Kost")

tab1, tab2 = st.tabs(["Daftar Kamar", "Tambah Penyewa"])

with tab1:
    st.write("### Kamar Tersedia")
    data = db.table("kamar").select("*").eq("status", "tersedia").execute()
    st.dataframe(data.data)

with tab2:
    with st.form("form_penyewa"):
        nama = st.text_input("Nama Penyewa")
        no_hp = st.text_input("No HP")
        kamar = st.selectbox("Pilih Kamar", ["A101", "B202", "C303"])
        
        if st.form_submit_button("Simpan"):
            db.table("penyewa").insert({
                "nama": nama,
                "no_hp": no_hp,
                "kamar": kamar
            }).execute()
            st.success("Data tersimpan!")
