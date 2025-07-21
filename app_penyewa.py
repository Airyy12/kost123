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

# Tambahkan import berikut di awal file
from datetime import datetime
import streamlit as st

def show_dashboard(gsheet):
    # Tambahkan CSS dan Font Awesome
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
    <style>
        .info-card {
            background-color: #2c3e50;
            border-radius: 10px;
            padding: 20px;
            color: white;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            height: 100%;
        }
        .info-card h3 {
            margin-top: 0;
            color: #ecf0f1;
            font-size: 18px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("📊 Dashboard Penyewa")
    
    try:
        # ==================== LOAD DATA ====================
        try:
            # Load user data
            user_ws = gsheet.worksheet("User")
            user_data = user_ws.get_all_records()
            current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
            
            if not current_user:
                st.error("🔴 Data pengguna tidak ditemukan")
                st.stop()
                
            # Load room data
            room_ws = gsheet.worksheet("Kamar")
            rooms = room_ws.get_all_records()
            user_room = next((r for r in rooms if r['Nama'] == current_user.get('kamar', '')), None)
            
            # Load payment data
            payment_ws = gsheet.worksheet("Pembayaran")
            payments = payment_ws.get_all_records()
            user_payments = [p for p in payments if str(p.get('username', '')).strip() == str(current_user['username']).strip()]
            
        except Exception as load_error:
            st.error(f"🔴 Gagal memuat data: {str(load_error)}")
            st.error("Pastikan semua worksheet (User, Kamar, Pembayaran) tersedia dan format data benar")
            st.stop()

        # ==================== INFO CARDS ====================
        col1, col2, col3 = st.columns(3)
        
        # Card 1: Kamar Saya - Perbaikan untuk handle None
        with col1:
            try:
                room_name = current_user.get('kamar', 'Belum Ada')
                room_status = user_room.get('Status', 'Tidak Diketahui') if user_room else 'Tidak Diketahui'
                room_price = int(user_room.get('Harga', 0)) if user_room else 0
                room_floor = user_room.get('lantai', '-') if user_room else '-'
                
                status_color = {
                    'Terisi': '#4CAF50',
                    'Tersedia': '#2196F3',
                    'Perbaikan': '#FF9800'
                }.get(room_status, '#9E9E9E')
                
                st.markdown(f"""
                <div class="info-card">
                    <h3><i class="fas fa-door-open"></i> Kamar Saya</h3>
                    <div style="display: flex; align-items: center; margin: 15px 0 20px;">
                        <span style="font-size: 28px; font-weight: bold; margin-right: 15px;">
                            {room_name}
                        </span>
                        <span style="padding: 5px 12px; background-color: {status_color}; 
                              color: white; border-radius: 15px; font-size: 14px;">
                            {room_status}
                        </span>
                    </div>
                    <div style="border-top: 1px solid #444; padding-top: 15px;">
                        <div style="display: flex; justify-content: space-between; margin: 12px 0;">
                            <span><i class="fas fa-tag"></i> Harga:</span>
                            <span style="font-weight: 500;">Rp {room_price:,}/bulan</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 12px 0;">
                            <span><i class="fas fa-layer-group"></i> Lantai:</span>
                            <span>{room_floor}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as card_error:
                st.error(f"Gagal menampilkan info kamar: {str(card_error)}")

        # ... (bagian lainnya tetap sama)
        # Card 2: Status Pembayaran - Perbaikan untuk handle None
        with col2:
            try:
                payment_status = current_user.get('status_pembayaran', 'Belum Dibayar')
                status_icon = {
                    'Lunas': 'check-circle',
                    'Belum Dibayar': 'exclamation-circle',
                    'Menunggu Verifikasi': 'clock',
                    'Ditolak': 'times-circle'
                }.get(payment_status, 'question-circle')
                
                status_color = {
                    'Lunas': '#4CAF50',
                    'Belum Dibayar': '#F44336',
                    'Menunggu Verifikasi': '#FFC107',
                    'Ditolak': '#E91E63'
                }.get(payment_status, '#9E9E9E')
                
                # Handle jika user_room None
                room_price = int(user_room.get('Harga', 0)) if user_room else 0
                
                st.markdown(f"""
                <div class="info-card">
                    <h3><i class="fas fa-credit-card"></i> Pembayaran</h3>
                    <div style="text-align: center; margin: 20px 0;">
                        <i class="fas fa-{status_icon}" 
                           style="font-size: 42px; color: {status_color}; margin-bottom: 10px;"></i>
                        <h4 style="color: {status_color}; margin: 5px 0;">{payment_status}</h4>
                    </div>
                    <div style="border-top: 1px solid #444; padding-top: 15px;">
                        <div style="display: flex; justify-content: space-between; margin: 12px 0;">
                            <span>Tagihan:</span>
                            <span>Rp {room_price:,}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin: 12px 0;">
                            <span>Tenggat:</span>
                            <span>10 {datetime.now().strftime('%B %Y')}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as card_error:
                st.error(f"Gagal menampilkan info pembayaran: {str(card_error)}")

        # Card 3: Kontak Admin - Tidak banyak perubahan diperlukan
        with col3:
            try:
                st.markdown("""
                <div class="info-card">
                    <h3><i class="fas fa-headset"></i> Kontak Admin</h3>
                    <div style="padding: 15px 0;">
                        <div style="display: flex; align-items: center; margin: 15px 0;">
                            <i class="fas fa-phone-alt" style="width: 30px; color: #4CAF50;"></i>
                            <span>0812-3456-7890</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 15px 0;">
                            <i class="fas fa-envelope" style="width: 30px; color: #2196F3;"></i>
                            <span>admin@kost123.com</span>
                        </div>
                        <div style="display: flex; align-items: center; margin: 15px 0;">
                            <i class="fas fa-map-marker-alt" style="width: 30px; color: #F44336;"></i>
                            <span>Jl. Kost No.123, Jakarta</span>
                        </div>
                    </div>
                    <div style="border-top: 1px solid #444; padding-top: 15px; text-align: center;">
                        <a href="https://wa.me/6281234567890" target="_blank" 
                           style="background-color: #25D366; color: white; padding: 8px 16px; 
                                  border-radius: 4px; text-decoration: none; display: inline-block;">
                            <i class="fab fa-whatsapp"></i> Hubungi via WhatsApp
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as card_error:
                st.error(f"Gagal menampilkan info kontak: {str(card_error)}")

        # ==================== RIWAYAT PEMBAYARAN ====================
        st.markdown("""
        <div style="margin: 30px 0 15px; border-bottom: 1px solid #444; padding-bottom: 10px;">
            <h3><i class="fas fa-history"></i> Riwayat Pembayaran Terakhir</h3>
        </div>
        """, unsafe_allow_html=True)

        try:
            if user_payments:
                # Fungsi untuk menentukan status dengan error handling
                def determine_payment_status(payment):
                    try:
                        # Jika status sudah diisi di sheet, gunakan itu
                        if payment.get('status'):
                            return payment['status']
                        
                        # Jika ada bukti pembayaran
                        if payment.get('bukti'):
                            if payment.get('waktu'):
                                try:
                                    payment_date = datetime.strptime(payment['waktu'].split()[0], "%Y-%m-%d")
                                    if (datetime.now() - payment_date).days > 3:
                                        return "Belum Diverifikasi"
                                    return "Menunggu Verifikasi"
                                except ValueError:
                                    return "Menunggu Verifikasi"
                            return "Menunggu Verifikasi"
                        
                        return "Belum Dibayar"
                    except Exception:
                        return "Status Tidak Diketahui"

                # Proses data pembayaran dengan error handling lebih robust
                processed_payments = []
                for payment in sorted(user_payments, 
                                   key=lambda x: x.get('waktu', '') or '1970-01-01', 
                                   reverse=True)[:5]:
                    try:
                        status = determine_payment_status(payment)
                        
                        # Handle periode
                        bulan = payment.get('bulan', '')
                        tahun = payment.get('tahun', '')
                        periode = f"{bulan} {tahun}" if bulan and tahun else "-"
                        
                        # Handle nominal
                        try:
                            nominal = f"Rp {int(payment.get('nominal', 0)):,}"
                        except (ValueError, TypeError):
                            nominal = "Rp 0"
                            
                        # Handle tanggal
                        tanggal = payment.get('waktu', '').split()[0] if payment.get('waktu') else '-'
                        
                        processed_payments.append({
                            'periode': periode,
                            'nominal': nominal,
                            'metode': payment.get('metode', 'Transfer Bank'),
                            'status': status,
                            'tanggal': tanggal,
                            'bukti': payment.get('bukti', '')
                        })
                    except Exception as e:
                        print(f"Error processing payment: {e}")
                        continue

                # Buat tabel HTML dengan style yang lebih baik
                table_html = """
                <style>
                    .payment-table {
                        width: 100%;
                        border-collapse: collapse;
                        margin: 15px 0;
                        font-size: 15px;
                        background-color: #2c3e50;
                        color: white;
                    }
                    .payment-table th {
                        background-color: #34495e;
                        color: white;
                        padding: 12px 15px;
                        text-align: left;
                        position: sticky;
                        top: 0;
                    }
                    .payment-table td {
                        padding: 12px 15px;
                        border-bottom: 1px solid #3d5166;
                    }
                    .payment-table tr:hover {
                        background-color: rgba(52, 152, 219, 0.2);
                    }
                    .status-lunas {
                        color: #2ecc71;
                        font-weight: 500;
                    }
                    .status-menunggu {
                        color: #f39c12;
                        font-weight: 500;
                    }
                    .status-belum {
                        color: #e74c3c;
                        font-weight: 500;
                    }
                    .payment-link {
                        color: #3498db;
                        text-decoration: none;
                        font-weight: 500;
                    }
                    .payment-link:hover {
                        text-decoration: underline;
                    }
                    .table-responsive {
                        overflow-x: auto;
                        margin-bottom: 20px;
                    }
                </style>
                <div class="table-responsive">
                <table class="payment-table">
                    <thead>
                        <tr>
                            <th>Periode</th>
                            <th>Nominal</th>
                            <th>Metode</th>
                            <th>Status</th>
                            <th>Tanggal</th>
                            <th>Bukti</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                for payment in processed_payments:
                    # Tentukan class dan ikon status
                    status_lower = payment['status'].lower()
                    if 'lunas' in status_lower or 'verifikasi' in status_lower:
                        status_class = "status-lunas"
                        status_icon = "check-circle"
                    elif 'menunggu' in status_lower or 'proses' in status_lower:
                        status_class = "status-menunggu"
                        status_icon = "hourglass-half"
                    elif 'belum' in status_lower or 'ditolak' in status_lower:
                        status_class = "status-belum"
                        status_icon = "times-circle"
                    else:
                        status_class = "status-menunggu"
                        status_icon = "clock"
                    
                    # Format link bukti dengan validasi URL
                    bukti = payment['bukti']
                    if bukti and (bukti.startswith('http://') or bukti.startswith('https://')):
                        bukti_link = f"""
                        <a href="{bukti}" target="_blank" class="payment-link">
                            <i class="fas fa-file-invoice"></i> Lihat
                        </a>
                        """
                    else:
                        bukti_link = "-"

                    table_html += f"""
                    <tr>
                        <td>{payment['periode']}</td>
                        <td>{payment['nominal']}</td>
                        <td>{payment['metode']}</td>
                        <td class="{status_class}">
                            <i class="fas fa-{status_icon}"></i> {payment['status']}
                        </td>
                        <td>{payment['tanggal']}</td>
                        <td>{bukti_link}</td>
                    </tr>
                    """

                table_html += """
                    </tbody>
                </table>
                </div>
                """
                st.markdown(table_html, unsafe_allow_html=True)
                
                # Tambahkan catatan dan tombol untuk melihat semua riwayat
                st.markdown("""
                <div style="margin-top: 10px; font-size: 14px; color: #95a5a6; display: flex; justify-content: space-between;">
                    <span><i class="fas fa-info-circle"></i> Status akan diperbarui setelah admin memverifikasi pembayaran</span>
                    <a href="#" style="color: #3498db; text-decoration: none;">
                        <i class="fas fa-list"></i> Lihat Semua Riwayat
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.markdown("""
                <div style="background-color: rgba(52, 152, 219, 0.1); 
                    padding: 25px; border-radius: 8px; text-align: center;
                    margin: 20px 0;">
                    <i class="fas fa-info-circle" style="font-size: 28px; color: #3498db;"></i>
                    <p style="margin-top: 15px; font-size: 16px; color: #7f8c8d;">
                        Belum ada riwayat pembayaran
                    </p>
                    <button style="background-color: #3498db; color: white; border: none; 
                            padding: 8px 16px; border-radius: 4px; margin-top: 10px;
                            cursor: pointer;">
                        <i class="fas fa-plus"></i> Lakukan Pembayaran
                    </button>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as payment_error:
            st.error(f"🔴 Gagal memuat riwayat pembayaran: {str(payment_error)}")
            st.error("Silakan refresh halaman atau hubungi admin")

    except Exception as e:
        st.error(f"🔴 Terjadi kesalahan sistem: {str(e)}")
        st.error("Silakan coba lagi nanti atau hubungi admin jika masalah berlanjut")
        
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
