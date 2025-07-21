import streamlit as st
import pandas as pd
from datetime import datetime
from sheets import connect_gsheet

def run_penyewa(menu):
    st.title(f"👋 Selamat datang, {st.session_state.username}!")
    
    # Connect to Google Sheets
    gsheet = connect_gsheet()
    
    if menu == "Dashboard":
        show_dashboard(gsheet)
    elif menu == "Pembayaran":
        show_payment(gsheet)
    elif menu == "Komplain":
        show_complaint(gsheet)
    elif menu == "Profil Saya":
        show_profile(gsheet)
    elif menu == "Logout":
        logout()

def show_dashboard(gsheet):
    st.header("📊 Dashboard Penyewa")
    
    try:
        # Get user data
        user_ws = gsheet.worksheet("User")
        user_data = user_ws.get_all_records()
        current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
        
        if not current_user:
            st.error("Data pengguna tidak ditemukan")
            return
            
        # Get room data - handle case where kamar_id might not exist
        room_ws = gsheet.worksheet("Kamar")
        rooms = room_ws.get_all_records()
        
        user_room = None
        if 'kamar_id' in current_user and current_user['kamar_id']:
            try:
                user_room = next((r for r in rooms if str(r['id']) == str(current_user['kamar_id'])), None)
            except (KeyError, StopIteration):
                user_room = None
        
        # Get payment data
        payment_ws = gsheet.worksheet("Pembayaran")
        payments = payment_ws.get_all_records()
        user_payments = [p for p in payments if str(p['user_id']) == str(current_user['id'])] if current_user else []
        
        # Display info cards
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="info-card">
                <h3>Kamar Saya</h3>
                <p style="font-size:24px; margin:10px 0;">{user_room['nama'] if user_room else '-'}</p>
                <p>Lantai: {user_room['lantai'] if user_room else '-'}</p>
                <p>Harga: Rp {int(user_room['harga']):,}/bulan</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            payment_status = "Lunas" if user_payments and user_payments[-1]['status'] == 'lunas' else "Belum Lunas"
            st.markdown(f"""
            <div class="info-card">
                <h3>Status Pembayaran</h3>
                <p style="font-size:24px; margin:10px 0;">{payment_status}</p>
                <p>Tagihan bulan ini: Rp {int(user_room['harga']):, if user_room else 0:,}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="info-card">
                <h3>Kontak Admin</h3>
                <p style="margin:10px 0;">📞 08123456789</p>
                <p>📧 admin@kost123.com</p>
                <p>🏢 Jl. Kost No.123</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Recent payments
        st.subheader("Riwayat Pembayaran Terakhir")
        if user_payments:
            df = pd.DataFrame(user_payments[-5:])
            st.dataframe(df[['bulan', 'tanggal_bayar', 'jumlah', 'status']])
        else:
            st.info("Belum ada riwayat pembayaran")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {str(e)}")
        
def show_payment(gsheet):
    st.header("💸 Pembayaran")
    
    # Get user data
    user_ws = gsheet.worksheet("User")
    user_data = user_ws.get_all_records()
    current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
    
    # Get room data
    room_ws = gsheet.worksheet("Kamar")
    rooms = room_ws.get_all_records()
    user_room = next((r for r in rooms if r['id'] == current_user['kamar_id']), None) if current_user else None
    
    # Get payment data
    payment_ws = gsheet.worksheet("Pembayaran")
    payments = payment_ws.get_all_records()
    user_payments = [p for p in payments if p['user_id'] == current_user['id']] if current_user else []
    
    # Current month bill
    current_month = datetime.now().strftime("%Y-%m")
    st.markdown(f"### Tagihan Bulan Ini ({current_month})")
    st.markdown(f"**Jumlah:** Rp {user_room['harga']:,}" if user_room else "Tidak ada kamar terdaftar")
    
    # Payment form
    with st.form("payment_form"):
        st.markdown("### Bayar Sekarang")
        amount = st.number_input("Jumlah Pembayaran", 
                               min_value=0, 
                               max_value=int(user_room['harga']) if user_room else 0,
                               value=int(user_room['harga']) if user_room else 0)
        payment_method = st.selectbox("Metode Pembayaran", ["Transfer Bank", "E-Wallet", "Tunai"])
        payment_proof = st.file_uploader("Upload Bukti Pembayaran", type=["jpg", "png", "pdf"])
        
        if st.form_submit_button("Kirim Pembayaran"):
            if amount > 0:
                new_payment = {
                    'id': len(payments) + 1,
                    'user_id': current_user['id'],
                    'kamar_id': current_user['kamar_id'],
                    'bulan': current_month,
                    'tanggal_bayar': datetime.now().strftime("%Y-%m-%d"),
                    'jumlah': amount,
                    'metode': payment_method,
                    'status': 'menunggu verifikasi',
                    'bukti': payment_proof.name if payment_proof else ""
                }
                
                # Save to Google Sheets
                payment_ws.append_row(list(new_payment.values()))
                st.success("Pembayaran berhasil dikirim! Menunggu verifikasi admin.")
                st.rerun()
            else:
                st.error("Jumlah pembayaran tidak valid")

def show_complaint(gsheet):
    st.header("📢 Komplain")
    
    # Get user data
    user_ws = gsheet.worksheet("User")
    user_data = user_ws.get_all_records()
    current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
    
    # Get complaints data
    complaint_ws = gsheet.worksheet("Komplain")
    complaints = complaint_ws.get_all_records()
    user_complaints = [c for c in complaints if c['user_id'] == current_user['id']] if current_user else []
    
    # Complaint form
    with st.form("complaint_form"):
        st.markdown("### Buat Komplain Baru")
        complaint_type = st.selectbox("Jenis Komplain", [
            "Kebersihan", 
            "Fasilitas", 
            "Kenyamanan", 
            "Lainnya"
        ])
        complaint_desc = st.text_area("Deskripsi Komplain")
        complaint_photo = st.file_uploader("Upload Foto (opsional)", type=["jpg", "png"])
        
        if st.form_submit_button("Kirim Komplain"):
            if complaint_desc:
                new_complaint = {
                    'id': len(complaints) + 1,
                    'user_id': current_user['id'],
                    'kamar_id': current_user['kamar_id'],
                    'tanggal': datetime.now().strftime("%Y-%m-%d"),
                    'jenis': complaint_type,
                    'deskripsi': complaint_desc,
                    'status': 'menunggu',
                    'foto': complaint_photo.name if complaint_photo else ""
                }
                
                # Save to Google Sheets
                complaint_ws.append_row(list(new_complaint.values()))
                st.success("Komplain berhasil dikirim! Admin akan segera menindaklanjuti.")
                st.rerun()
            else:
                st.error("Deskripsi komplain tidak boleh kosong")
    
    # Complaint history
    st.markdown("### Riwayat Komplain")
    if user_complaints:
        df = pd.DataFrame(user_complaints)
        st.dataframe(df[['tanggal', 'jenis', 'deskripsi', 'status']])
    else:
        st.info("Belum ada komplain")

def show_profile(gsheet):
    st.header("👤 Profil Saya")
    
    # Get user data
    user_ws = gsheet.worksheet("User")
    user_data = user_ws.get_all_records()
    current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
    
    # Get room data
    room_ws = gsheet.worksheet("Kamar")
    rooms = room_ws.get_all_records()
    user_room = next((r for r in rooms if r['id'] == current_user['kamar_id']), None) if current_user else None
    
    if current_user:
        with st.form("profile_form"):
            st.markdown("### Informasi Pribadi")
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Lengkap", value=current_user.get('nama', ''))
                email = st.text_input("Email", value=current_user.get('email', ''))
            with col2:
                no_hp = st.text_input("No. HP", value=current_user.get('no_hp', ''))
                nik = st.text_input("NIK", value=current_user.get('nik', ''))
            
            st.markdown("### Informasi Kamar")
            st.text_input("Nomor Kamar", value=user_room['nama'] if user_room else "-", disabled=True)
            st.text_input("Lantai", value=user_room['lantai'] if user_room else "-", disabled=True)
            
            if st.form_submit_button("Simpan Perubahan"):
                # Update user data
                for i, user in enumerate(user_data):
                    if user['username'] == st.session_state.username:
                        user_data[i]['nama'] = nama
                        user_data[i]['email'] = email
                        user_data[i]['no_hp'] = no_hp
                        user_data[i]['nik'] = nik
                        break
                
                # Update Google Sheets
                user_ws.update([list(user_data[0].keys())] + [list(u.values()) for u in user_data])
                st.success("Profil berhasil diperbarui!")
                st.rerun()

def logout():
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu = None
    st.rerun()
