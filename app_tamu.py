import streamlit as st
from sheets import connect_gsheet
from drive import upload_to_drive
import re

st.title("🏠 Kost Kami – Info & Booking")

sheet = connect_gsheet()
sheet_kamar = sheet.worksheet("Kamar")
sheet_booking = sheet.worksheet("Booking")

data_kamar = sheet_kamar.get_all_records()

# --- Tampilkan kamar ---
st.subheader("Daftar Kamar Tersedia")
kamar_kosong = [k for k in data_kamar if k['Status'] == 'Kosong']
if kamar_kosong:
    for kamar in kamar_kosong:
        st.markdown(f"**Kamar {kamar['Nama']}** - Rp{kamar['Harga']}/bulan")
        st.image(kamar['Foto'], width=300)
        st.text(f"{kamar['Deskripsi']}")
        st.markdown("---")
else:
    st.info("Saat ini tidak ada kamar kosong.")

# --- Form Booking ---
st.subheader("Booking Kamar")
with st.form("booking_form"):
    nama = st.text_input("Nama Lengkap")
    nohp = st.text_input("No HP")
    kamar_dipilih = st.selectbox("Pilih Kamar", [k["Nama"] for k in kamar_kosong])
    foto_ktp = st.file_uploader("Upload Foto KTP", type=["jpg", "jpeg", "png"])
    submitted = st.form_submit_button("Kirim Booking")

    if submitted:
        if not nama or not nohp or not kamar_dipilih:
            st.warning("Semua field harus diisi.")
        elif not foto_ktp:
            st.warning("Harap upload KTP.")
        else:
            # Bersihkan nama file
            safe_nama = re.sub(r'[^a-zA-Z0-9_\-]', '_', nama)
            try:
                link_foto = upload_to_drive(foto_ktp, f"KTP_{safe_nama}.jpg")
                sheet_booking.append_row([nama, nohp, kamar_dipilih, link_foto])
                st.success("Booking berhasil dikirim!")
            except Exception as e:
                st.error(f"Terjadi error saat booking: {e}")
