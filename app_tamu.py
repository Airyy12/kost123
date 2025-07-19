import streamlit as st
from sheets import connect_gsheet
from drive import upload_to_drive

st.title("🏠 Kost Kami – Info & Booking")

sheet = connect_gsheet()
sheet_kamar = sheet.worksheet("Kamar")
sheet_booking = sheet.worksheet("Booking")

data_kamar = sheet_kamar.get_all_records()

# --- Tampilkan kamar ---
st.subheader("Daftar Kamar Tersedia")
for kamar in data_kamar:
    if kamar['Status'] == 'Kosong':
        st.markdown(f"**Kamar {kamar['Nama']}** - Rp{kamar['Harga']}/bulan")
        st.image(kamar['Foto'], width=300)
        st.text(f"{kamar['Deskripsi']}")
        st.markdown("---")

# --- Form Booking ---
st.subheader("Booking Kamar")
with st.form("booking_form"):
    nama = st.text_input("Nama Lengkap")
    nohp = st.text_input("No HP")
    kamar_dipilih = st.selectbox("Pilih Kamar", [k["Nama"] for k in data_kamar if k["Status"] == "Kosong"])
    foto_ktp = st.file_uploader("Upload Foto KTP", type=["jpg", "jpeg", "png"])
    submitted = st.form_submit_button("Kirim Booking")

    if submitted:
        if foto_ktp:
            link_foto = upload_to_drive(foto_ktp, f"KTP_{nama}.jpg")
            sheet_booking.append_row([nama, nohp, kamar_dipilih, link_foto])
            st.success("Booking berhasil dikirim!")
        else:
            st.warning("Harap upload KTP.")
