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
            
        # Get room data
        room_ws = gsheet.worksheet("Kamar")
        rooms = room_ws.get_all_records()
        user_room = next((r for r in rooms if r['Nama'] == current_user['kamar']), None) if current_user.get('kamar') else None
        
        # Get payment data
        payment_ws = gsheet.worksheet("Pembayaran")
        payments = payment_ws.get_all_records()
        user_payments = [p for p in payments if p['username'] == current_user['username']]

        # Display info cards
        col1, col2, col3 = st.columns(3)
        with col1:
            room_info = f"""
            <div class="info-card">
                <h3>Kamar Saya</h3>
                <p style="font-size:24px; margin:10px 0;">{current_user.get('kamar', '-')}</p>
            """
            if user_room:
                room_info += f"""
                <p>Status: {user_room.get('Status', '-')}</p>
                <p>Harga: Rp {int(user_room.get('Harga', 0)):,}/bulan</p>
                """
            else:
                room_info += "<p style='color:red;'>Data kamar tidak ditemukan</p>"
            room_info += "</div>"
            st.markdown(room_info, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="info-card">
                <h3>Status Pembayaran</h3>
                <p style="font-size:24px; margin:10px 0;">{current_user.get('status_pembayaran', 'Belum Lunas')}</p>
                <p>Tagihan bulan ini: Rp {int(user_room.get('Harga', 0)) if user_room else 0:,}</p>
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
        st.subheader("💸 Riwayat Pembayaran Terakhir")
        if user_payments:
            # Process payment data
            payment_data = []
            for payment in user_payments[-5:]:  # Ambil 5 terakhir
                payment_data.append({
                    'Periode': f"{payment['bulan']} {payment['tahun']}",
                    'Nominal': f"Rp {int(payment['nominal']):,}",
                    'Status': payment.get('status', 'Menunggu Verifikasi'),
                    'Waktu': payment['waktu'].split()[0]  # Ambil tanggal saja
                })
            
            # Display as table
            st.table(payment_data)
        else:
            st.info("Belum ada riwayat pembayaran")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data: {e}")
        
def show_payment(gsheet):
    st.header("💸 Pembayaran")
    
    try:
        # Get user data
        user_ws = gsheet.worksheet("User")
        user_data = user_ws.get_all_records()
        current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
        
        if not current_user:
            st.error("Data pengguna tidak ditemukan")
            return
            
        # Get room data
        room_ws = gsheet.worksheet("Kamar")
        rooms = room_ws.get_all_records()
        user_room = next((r for r in rooms if r['Nama'] == current_user['kamar']), None) if current_user.get('kamar') else None
        
        if not user_room:
            st.error("Anda belum memiliki kamar yang dipesan")
            return
        
        # Current month and year
        current_month = datetime.now().strftime("%B")
        current_year = datetime.now().strftime("%Y")
        
        st.markdown(f"### Tagihan Bulan Ini ({current_month} {current_year})")
        st.markdown(f"**Jumlah:** Rp {int(user_room['Harga']):,}")
        
        # Payment form
        with st.form("payment_form"):
            st.markdown("### Bayar Sekarang")
            
            # Auto-fill bulan dan tahun
            bulan = st.selectbox("Bulan", [current_month], disabled=True)
            tahun = st.selectbox("Tahun", [current_year], disabled=True)
            
            amount = st.number_input("Jumlah Pembayaran", 
                                   min_value=0, 
                                   max_value=int(user_room['Harga']),
                                   value=int(user_room['Harga']))
            payment_proof = st.file_uploader("Upload Bukti Pembayaran (foto/PDF)", type=["jpg", "jpeg", "png", "pdf"])
            
            if st.form_submit_button("Kirim Pembayaran"):
                if amount > 0 and payment_proof:
                    payment_ws = gsheet.worksheet("Pembayaran")
                    new_payment = {
                        'username': current_user['username'],
                        'bukti': payment_proof.name,
                        'bulan': current_month,
                        'tahun': current_year,
                        'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'nominal': amount,
                        'status': 'Menunggu Verifikasi'
                    }
                    
                    # Save to Google Sheets
                    payment_ws.append_row(list(new_payment.values()))
                    st.success("Pembayaran berhasil dikirim! Menunggu verifikasi admin.")
                    st.rerun()
                else:
                    st.error("Harap isi semua field dan upload bukti pembayaran")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def show_complaint(gsheet):
    st.header("📢 Komplain")
    
    try:
        # Get user data
        user_ws = gsheet.worksheet("User")
        user_data = user_ws.get_all_records()
        current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
        
        if not current_user:
            st.error("Data pengguna tidak ditemukan")
            return
            
        # Get complaint data
        complaint_ws = gsheet.worksheet("Komplain")
        complaints = complaint_ws.get_all_records()
        user_complaints = [c for c in complaints if c['username'] == current_user['username']]
        
        # Complaint form
        with st.form("complaint_form"):
            st.markdown("### Buat Komplain Baru")
            complaint_desc = st.text_area("Isi Komplain", placeholder="Jelaskan keluhan Anda...")
            complaint_photo = st.file_uploader("Upload Foto Pendukung (opsional)", type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button("Kirim Komplain"):
                if complaint_desc:
                    new_complaint = {
                        'username': current_user['username'],
                        'isi_komplain': complaint_desc,
                        'link_foto': complaint_photo.name if complaint_photo else "",
                        'waktu': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Menunggu'
                    }
                    
                    # Save to Google Sheets
                    complaint_ws.append_row(list(new_complaint.values()))
                    st.success("Komplain berhasil dikirim! Admin akan segera menindaklanjuti.")
                    st.rerun()
                else:
                    st.error("Isi komplain tidak boleh kosong")
        
        # Complaint history
        st.markdown("### Riwayat Komplain")
        if user_complaints:
            df = pd.DataFrame(user_complaints)
            st.dataframe(df[['waktu', 'isi_komplain', 'status']].rename(columns={
                'waktu': 'Waktu',
                'isi_komplain': 'Komplain',
                'status': 'Status'
            }))
        else:
            st.info("Belum ada komplain")
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def show_profile(gsheet):
    st.header("👤 Profil Saya")
    
    try:
        # Get user data
        user_ws = gsheet.worksheet("User")
        user_data = user_ws.get_all_records()
        current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
        
        if not current_user:
            st.error("Data pengguna tidak ditemukan")
            return
            
        # Get room data
        room_ws = gsheet.worksheet("Kamar")
        rooms = room_ws.get_all_records()
        user_room = next((r for r in rooms if r['Nama'] == current_user['kamar']), None) if current_user.get('kamar') else None
        
        with st.form("profile_form"):
            st.markdown("### Informasi Pribadi")
            col1, col2 = st.columns(2)
            with col1:
                nama = st.text_input("Nama Lengkap", value=current_user.get('nama_lengkap', ''))
                email = st.text_input("No. HP", value=current_user.get('no_hp', ''))
            with col2:
                kamar = st.text_input("Kamar", value=current_user.get('kamar', ''), disabled=True)
                status = st.text_input("Status Pembayaran", value=current_user.get('status_pembayaran', ''), disabled=True)
            
            st.markdown("### Foto Profil")
            st.image(current_user.get('foto_profil', ''), width=150) if current_user.get('foto_profil') else st.warning("Tidak ada foto profil")
            
            if st.form_submit_button("Simpan Perubahan"):
                # Update user data
                for i, user in enumerate(user_data):
                    if user['username'] == st.session_state.username:
                        user_data[i]['nama_lengkap'] = nama
                        user_data[i]['no_hp'] = email  # Note: ini seharusnya no_hp
                        break
                
                # Update Google Sheets
                user_ws.update([list(user_data[0].keys())] + [list(u.values()) for u in user_data])
                st.success("Profil berhasil diperbarui!")
                st.rerun()
    
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")

def logout():
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu = None
    st.rerun()
