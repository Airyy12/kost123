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
        user_room = next((r for r in rooms if r['Nama'] == current_user['kamar']), None)

        # Get payment data
        payment_ws = gsheet.worksheet("Pembayaran")
        payments = payment_ws.get_all_records()
        user_payments = [p for p in payments if p['username'] == current_user['username']]

        # Display info cards
        col1, col2, col3 = st.columns(3)
        
        # Card 1: Kamar Saya
        with col1:
            if user_room:
                st.markdown(f"""
                <div class="info-card">
                    <h3><i class="fas fa-door-open"></i> Kamar Saya</h3>
                    <div style="display: flex; align-items: center; margin: 15px 0;">
                        <span style="font-size: 28px; font-weight: bold; margin-right: 12px;">{current_user.get('kamar', '-')}</span>
                        <span style="padding: 4px 10px; background-color: {'#4CAF50' if user_room.get('Status') == 'Terisi' else '#F44336'}; 
                            color: white; border-radius: 15px; font-size: 14px; font-weight: 500;">
                            {user_room.get('Status', '-')}
                        </span>
                    </div>
                    <div style="border-top: 1px solid #444; padding-top: 12px;">
                        <div style="display: flex; align-items: center; margin: 8px 0;">
                            <i class="fas fa-tag" style="width: 24px; color: #FFC107;"></i>
                            <span>Rp {int(user_room.get('Harga', 0)):,}/bulan</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 8px 0;">
                            <i class="fas fa-layer-group" style="width: 24px; color: #9C27B0;"></i>
                            <span>Lantai {user_room.get('lantai', '-')}</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 8px 0;">
                            <i class="fas fa-calendar-alt" style="width: 24px; color: #2196F3;"></i>
                            <span>Kontrak sampai {datetime.now().strftime('%B %Y')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="info-card">
                    <h3><i class="fas fa-door-open"></i> Kamar Saya</h3>
                    <div style="text-align: center; padding: 20px 0;">
                        <i class="fas fa-exclamation-triangle" style="font-size: 24px; color: #FF9800;"></i>
                        <p style="margin-top: 10px;">Data kamar tidak ditemukan</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Card 2: Status Pembayaran
        with col2:
            payment_status = current_user.get('status_pembayaran', 'Belum Lunas')
            st.markdown(f"""
            <div class="info-card">
                <h3><i class="fas fa-credit-card"></i> Pembayaran</h3>
                <div style="text-align: center; margin: 20px 0;">
                    <div style="font-size: 48px; color: {'#4CAF50' if payment_status == 'Lunas' else '#F44336'}; margin: 10px 0;">
                        <i class="fas fa-{'check-circle' if payment_status == 'Lunas' else 'exclamation-circle'}"></i>
                    </div>
                    <h4 style="margin: 5px 0;">{payment_status}</h4>
                </div>
                <div style="border-top: 1px solid #444; padding-top: 12px;">
                    <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                        <span>Tagihan Bulan Ini:</span>
                        <span style="font-weight: bold;">Rp {int(user_room.get('Harga', 0)) if user_room else 0:,}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin: 8px 0;">
                        <span>Tenggat Pembayaran:</span>
                        <span style="font-weight: bold;">10 {datetime.now().strftime('%B %Y')}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Card 3: Kontak Admin
        with col3:
            st.markdown("""
            <div class="info-card">
                <h3><i class="fas fa-headset"></i> Kontak Admin</h3>
                <div style="padding: 15px 0;">
                    <div style="display: flex; align-items: center; margin: 12px 0;">
                        <i class="fas fa-phone-alt" style="width: 24px; color: #4CAF50;"></i>
                        <span>0812-3456-7890</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 12px 0;">
                        <i class="fas fa-envelope" style="width: 24px; color: #2196F3;"></i>
                        <span>admin@kost123.com</span>
                    </div>
                    <div style="display: flex; align-items: center; margin: 12px 0;">
                        <i class="fas fa-map-marker-alt" style="width: 24px; color: #F44336;"></i>
                        <span>Jl. Kost No.123, Jakarta</span>
                    </div>
                </div>
                <div style="border-top: 1px solid #444; padding-top: 12px; text-align: center;">
                    <button style="background-color: #4CAF50; color: white; border: none; 
                        padding: 8px 16px; border-radius: 4px; cursor: pointer;">
                        <i class="fas fa-whatsapp"></i> Hubungi via WhatsApp
                    </button>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Recent payments section
        st.markdown("""
        <div style="margin-top: 30px;">
            <h3><i class="fas fa-history"></i> Riwayat Pembayaran Terakhir</h3>
        </div>
        """, unsafe_allow_html=True)
        
        if user_payments:
            # Prepare payment history data
            payment_history = []
            for payment in sorted(user_payments, key=lambda x: x['waktu'], reverse=True)[:5]:
                payment_history.append({
                    'Bulan/Tahun': f"{payment['bulan']} {payment['tahun']}",
                    'Nominal': f"Rp {int(payment['nominal']):,}",
                    'Metode': payment.get('metode', 'Transfer Bank'),
                    'Status': payment.get('status', 'Menunggu Verifikasi'),
                    'Tanggal': payment['waktu'].split()[0],
                    'Bukti': f"[Lihat]({payment['bukti']})" if payment.get('bukti') else '-'
                })
            
            # Display as styled table
            st.markdown("""
            <style>
                .payment-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .payment-table th {
                    background-color: #333;
                    color: white;
                    padding: 12px;
                    text-align: left;
                }
                .payment-table td {
                    padding: 10px;
                    border-bottom: 1px solid #444;
                }
                .payment-table tr:nth-child(even) {
                    background-color: rgba(255,255,255,0.05);
                }
                .status-pending { color: #FFC107; }
                .status-verified { color: #4CAF50; }
                .status-rejected { color: #F44336; }
            </style>
            """, unsafe_allow_html=True)
            
            # Convert to HTML table
            table_html = """
            <table class="payment-table">
                <thead>
                    <tr>
                        <th>Bulan/Tahun</th>
                        <th>Nominal</th>
                        <th>Metode</th>
                        <th>Status</th>
                        <th>Tanggal</th>
                        <th>Bukti</th>
                    </tr>
                </thead>
                <tbody>
            """
            
            for payment in payment_history:
                status_class = ""
                if 'Menunggu' in payment['Status']:
                    status_class = "status-pending"
                elif 'Lunas' in payment['Status']:
                    status_class = "status-verified"
                elif 'Ditolak' in payment['Status']:
                    status_class = "status-rejected"
                    
                table_html += f"""
                <tr>
                    <td>{payment['Bulan/Tahun']}</td>
                    <td>{payment['Nominal']}</td>
                    <td>{payment['Metode']}</td>
                    <td class="{status_class}">{payment['Status']}</td>
                    <td>{payment['Tanggal']}</td>
                    <td>{payment['Bukti']}</td>
                </tr>
                """
            
            table_html += "</tbody></table>"
            st.markdown(table_html, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: rgba(33, 150, 243, 0.1); padding: 20px; border-radius: 8px; text-align: center;">
                <i class="fas fa-info-circle" style="font-size: 24px; color: #2196F3;"></i>
                <p style="margin-top: 10px;">Belum ada riwayat pembayaran</p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat dashboard: {str(e)}")
        
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
