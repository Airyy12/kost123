import streamlit as st
from sheets import connect_gsheet
from drive import upload_to_drive
import re

st.set_page_config(page_title="Kost123 - Booking", layout="wide")
st.title("🏠 Kost123 – Info & Booking Kamar")

# --- Fungsi ---
def load_kamar():
    sheet = connect_gsheet()
    kamar_ws = sheet.worksheet("Kamar")
    return kamar_ws.get_all_records()

def validasi_hp(nohp):
    return re.match(r"^08[0-9]{8,11}$", nohp)

def tampilkan_kamar(kamar_list):
    st.subheader("Daftar Kamar Tersedia")
    if not kamar_list:
        st.info("Saat ini semua kamar sudah terisi.")
        return

    for kamar in kamar_list:
        st.markdown(f"### Kamar {kamar['Nama']} - Rp {kamar['Harga']}/bulan")
        st.image(kamar['Foto'], width=300)
        st.text(kamar['Deskripsi'])
        st.markdown("---")

def form_booking(kamar_kosong):
    st.subheader("Form Booking Kamar")
    with st.form("booking_form"):
        nama = st.text_input("Nama Lengkap")
        nohp = st.text_input("No HP (Format: 08...)")
        kamar_dipilih = st.selectbox("Pilih Kamar", [k["Nama"] for k in kamar_kosong])
        foto_ktp = st.file_uploader("Upload Foto KTP", type=["jpg", "jpeg", "png"])
        submit = st.form_submit_button("Kirim Booking")

        if submit:
            if not nama or not nohp or not foto_ktp:
                st.warning("Semua field wajib diisi.")
                return

            if not validasi_hp(nohp):
                st.error("Nomor HP tidak valid. Gunakan format 08xxx")
                return

            # Simpan ke Google Sheet dan Drive
            try:
                with st.spinner("Menyimpan booking..."):
                    link_ktp = upload_to_drive(foto_ktp, f"KTP_{re.sub(r'[^a-zA-Z0-9_\-]', '_', nama)}.jpg")
                    sheet = connect_gsheet()
                    booking_ws = sheet.worksheet("Booking")
                    booking_ws.append_row([nama, nohp, kamar_dipilih, link_ktp])
                st.success("Booking berhasil dikirim! Admin akan menghubungi Anda.")
            except Exception as e:
                st.error(f"Gagal booking: {e}")

# --- Main ---
data_kamar = load_kamar()
kamar_kosong = [k for k in data_kamar if k['Status'].lower() == 'kosong']

tampilkan_kamar(kamar_kosong)
if kamar_kosong:
    form_booking(kamar_kosong)
