import streamlit as st
from sheets import connect_gsheet
from datetime import datetime
import pandas as pd
from cloudinary_upload import upload_to_cloudinary

def run_penyewa(menu):
    st.title(f"👋 Selamat datang, {st.session_state.username}")
    
    # Dapatkan data user
    user_ws = connect_gsheet().worksheet("User")
    user_data = user_ws.get_all_records()
    current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
    
    if menu == "Dashboard":
        dashboard_penyewa(current_user)
    elif menu == "Pembayaran":
        pembayaran_penyewa(current_user)
    elif menu == "Komplain":
        komplain_penyewa(current_user)
    elif menu == "Profil Saya":
        profil_penyewa(current_user)
    elif menu == "Logout":
        st.session_state.login_status = False
        st.session_state.role = None
        st.session_state.username = ""
        st.rerun()

def dashboard_penyewa(current_user):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 Informasi Kamar Anda")
        if current_user and current_user['kamar']:
            kamar_ws = connect_gsheet().worksheet("Kamar")
            kamar_data = kamar_ws.get_all_records()
            kamar_user = next((k for k in kamar_data if k['Nama'] == current_user['kamar']), None)
            
            if kamar_user:
                st.markdown(f"""
                <div class="info-card">
                    <h3>{kamar_user['Nama']}</h3>
                    <p><b>Status:</b> {kamar_user['Status']}</p>
                    <p><b>Harga:</b> Rp {kamar_user['Harga']:,}/bulan</p>
                    <p><b>Deskripsi:</b> {kamar_user['Deskripsi']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning("Anda belum memiliki kamar yang terdaftar")
        else:
            st.warning("Anda belum memiliki kamar yang terdaftar")
    
    with col2:
        st.subheader("💳 Riwayat Pembayaran Terakhir")
        
        if current_user:
            pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
            pembayaran_data = pembayaran_ws.get_all_records()
            user_payments = [p for p in pembayaran_data if p['username'] == current_user['username']]
            
            if user_payments:
                # Ambil 3 pembayaran terakhir
                latest_payments = sorted(user_payments, key=lambda x: x['waktu'], reverse=True)[:3]
                
                for payment in latest_payments:
                    status_color = "orange" if payment['status'] == "Menunggu Verifikasi" else "green" if payment['status'] == "Lunas" else "red"
                    
                    with st.container():
                        st.markdown(f"""
                        <div class="info-card" style="margin-bottom:15px;padding:15px;">
                            <div style="display:flex;justify-content:space-between;">
                                <div>
                                    <b>{payment['bulan']} {payment['tahun']}</b>
                                    <p style="margin:5px 0;font-size:18px;">Rp {int(payment['nominal']):,}</p>
                                </div>
                                <div style="color:{status_color};align-self:center;">
                                    {payment['status']}
                                </div>
                            </div>
                            <div style="display:flex;justify-content:space-between;margin-top:10px;">
                                <small>{payment['waktu'][:10]}</small>
                                {f'<a href="{payment["bukti"]}" target="_blank" style="color:#4e8cff;text-decoration:none;">Lihat Bukti</a>' if payment.get('bukti') else ''}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Belum ada riwayat pembayaran")

def pembayaran_penyewa(current_user):
    st.subheader("💳 Pembayaran Sewa Kamar")
    
    tab1, tab2 = st.tabs(["Bayar Sekarang", "Riwayat Pembayaran"])
    
    with tab1:
        if current_user and current_user['kamar']:
            kamar_ws = connect_gsheet().worksheet("Kamar")
            kamar_data = kamar_ws.get_all_records()
            kamar_user = next((k for k in kamar_data if k['Nama'] == current_user['kamar']), None)
            
            if kamar_user:
                with st.form("form_pembayaran"):
                    bulan = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                                                "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
                    tahun = st.selectbox("Tahun", [datetime.now().year, datetime.now().year + 1])
                    nominal = st.number_input("Nominal Pembayaran", value=int(kamar_user['Harga']))
                    bukti = st.file_uploader("Upload Bukti Pembayaran", type=["jpg", "png", "jpeg"])
                    
                    if st.form_submit_button("Kirim Pembayaran"):
                        if bukti is not None:
                            # Generate unique filename
                            filename = f"pembayaran_{current_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                            
                            # Upload to Cloudinary
                            bukti_url = upload_to_cloudinary(bukti, filename)
                            
                            if bukti_url:
                                pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
                                new_payment = {
                                    'username': current_user['username'],
                                    'bukti': bukti_url,
                                    'bulan': bulan,
                                    'tahun': str(tahun),
                                    'nominal': str(nominal),
                                    'status': "Menunggu Verifikasi",
                                    'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                }
                                pembayaran_ws.append_row(list(new_payment.values()))
                                st.success("Pembayaran berhasil dikirim, menunggu verifikasi admin")
                            else:
                                st.error("Gagal mengupload bukti pembayaran")
                        else:
                            st.error("Harap upload bukti pembayaran")
            else:
                st.warning("Anda belum memiliki kamar yang terdaftar")
        else:
            st.warning("Anda belum memiliki kamar yang terdaftar")
    
    with tab2:
        pembayaran_ws = connect_gsheet().worksheet("Pembayaran")
        pembayaran_data = pembayaran_ws.get_all_records()
        user_payments = [p for p in pembayaran_data if p['username'] == current_user['username']]
        
        if user_payments:
            for payment in sorted(user_payments, key=lambda x: x['waktu'], reverse=True):
                with st.expander(f"Pembayaran {payment['bulan']} {payment['tahun']} - {payment['status']}"):
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if payment.get('bukti'):
                            st.image(payment['bukti'], caption="Bukti Pembayaran", width=200)
                        else:
                            st.warning("Tidak ada bukti pembayaran")
                    with col2:
                        st.markdown(f"""
                        **Nominal:** Rp {int(payment['nominal']):,}  
                        **Status:** {payment['status']}  
                        **Waktu:** {payment['waktu']}
                        """)
        else:
            st.info("Belum ada riwayat pembayaran")

def komplain_penyewa(current_user):
    st.subheader("📢 Buat Komplain/Pengaduan")
    
    with st.form("form_komplain"):
        isi_komplain = st.text_area("Isi Komplain/Pengaduan", height=150)
        foto_komplain = st.file_uploader("Upload Foto Pendukung (jika ada)", type=["jpg", "png", "jpeg"])
        
        if st.form_submit_button("Kirim Komplain"):
            if isi_komplain.strip():
                foto_url = ""
                if foto_komplain:
                    # Generate unique filename
                    filename = f"komplain_{current_user['username']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    foto_url = upload_to_cloudinary(foto_komplain, filename)
                
                komplain_ws = connect_gsheet().worksheet("Komplain")
                new_complaint = {
                    'username': current_user['username'],
                    'isi_komplain': isi_komplain,
                    'link_foto': foto_url,
                    'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': "Menunggu Respon"
                }
                komplain_ws.append_row(list(new_complaint.values()))
                st.success("Komplain berhasil dikirim, admin akan segera merespon")
            else:
                st.error("Isi komplain tidak boleh kosong")
    
    st.subheader("📋 Riwayat Komplain")
    komplain_ws = connect_gsheet().worksheet("Komplain")
    komplain_data = komplain_ws.get_all_records()
    user_complaints = [k for k in komplain_data if k['username'] == current_user['username']]
    
    if user_complaints:
        for complaint in sorted(user_complaints, key=lambda x: x['waktu'], reverse=True):
            with st.expander(f"Komplain - {complaint['waktu']}"):
                if complaint.get('link_foto'):
                    st.image(complaint['link_foto'], caption="Foto Pendukung", width=300)
                st.markdown(f"""
                **Status:** {complaint['status']}  
                **Isi Komplain:**  
                {complaint['isi_komplain']}
                """)
    else:
        st.info("Belum ada riwayat komplain")

def profil_penyewa(current_user):
    st.subheader("👤 Profil Saya")
    
    if current_user:
        with st.form("form_profil"):
            nama_lengkap = st.text_input("Nama Lengkap", value=current_user.get('nama_lengkap', ''))
            no_hp = st.text_input("Nomor HP", value=current_user.get('no_hp', ''))
            
            if st.form_submit_button("Update Profil"):
                user_ws = connect_gsheet().worksheet("User")
                all_users = user_ws.get_all_records()
                
                for i, user in enumerate(all_users, start=2):
                    if user['username'] == current_user['username']:
                        user_ws.update_cell(i, 4, nama_lengkap)  # Kolom nama_lengkap
                        user_ws.update_cell(i, 5, no_hp)        # Kolom no_hp
                        user_ws.update_cell(i, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # Kolom last_edit
                        st.success("Profil berhasil diperbarui")
                        st.rerun()
