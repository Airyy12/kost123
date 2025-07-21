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
    </style>
    """, unsafe_allow_html=True)

    st.header("📊 Dashboard Penyewa")

    try:
        # ==================== LOAD DATA ====================
        try:
            user_ws = gsheet.worksheet("User")
            user_data = user_ws.get_all_records()
            current_user = next((u for u in user_data if u['username'] == st.session_state.username), None)
            
            if not current_user:
                st.error("🔴 Data pengguna tidak ditemukan")
                st.stop()
                
            room_ws = gsheet.worksheet("Kamar")
            rooms = room_ws.get_all_records()
            user_room = next((r for r in rooms if r['Nama'] == current_user.get('kamar', '')), None)
            
            payment_ws = gsheet.worksheet("Pembayaran")
            payments = payment_ws.get_all_records()
            user_payments = [p for p in payments if str(p.get('username', '')).strip() == str(current_user['username']).strip()]
            
        except Exception as load_error:
            st.error(f"🔴 Gagal memuat data: {str(load_error)}")
            st.stop()

        # ==================== INFO CARDS ====================
        col1, col2, col3 = st.columns(3)
        
        # Card 1: Kamar Saya
        with col1:
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

        # Card 2: Status Pembayaran
        with col2:
            payment_status = current_user.get('status_pembayaran', 'Belum Dibayar')
            status_config = {
                'Lunas': {'icon': 'check-circle', 'color': '#4CAF50'},
                'Belum Dibayar': {'icon': 'exclamation-circle', 'color': '#F44336'},
                'Menunggu Verifikasi': {'icon': 'hourglass-half', 'color': '#FFC107'},
                'Ditolak': {'icon': 'times-circle', 'color': '#E91E63'}
            }
            config = status_config.get(payment_status, {'icon': 'question-circle', 'color': '#9E9E9E'})
            
            st.markdown(f"""
            <div class="info-card">
                <h3><i class="fas fa-credit-card"></i> Pembayaran</h3>
                <div style="text-align: center; margin: 20px 0;">
                    <i class="fas fa-{config['icon']}" 
                       style="font-size: 42px; color: {config['color']}; margin-bottom: 10px;"></i>
                    <h4 style="color: {config['color']}; margin: 5px 0;">{payment_status}</h4>
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

        # Card 3: Kontak Admin
        with col3:
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

        # ==================== RIWAYAT PEMBAYARAN ====================
        st.markdown("""
        <div style="margin: 30px 0 15px; border-bottom: 1px solid #444; padding-bottom: 10px;">
            <h3><i class="fas fa-history"></i> Riwayat Pembayaran Terakhir</h3>
        </div>
        """, unsafe_allow_html=True)

        if user_payments:
            def format_status(status):
                status = status.lower()
                if status in ['lunas', 'diverifikasi']:
                    return ('Lunas', 'check-circle', 'status-lunas')
                elif status in ['menunggu verifikasi', 'proses verifikasi']:
                    return ('Menunggu Verifikasi', 'hourglass-half', 'status-menunggu')
                elif status in ['ditolak', 'gagal']:
                    return ('Ditolak', 'times-circle', 'status-belum')
                return ('Belum Dibayar', 'exclamation-circle', 'status-belum')

            latest_payments = sorted(
                user_payments,
                key=lambda x: x.get('waktu', '1970-01-01'),
                reverse=True
            )[:5]

            table_html = """
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

            for pay in latest_payments:
                bulan = pay.get('bulan', '-')
                tahun = pay.get('tahun', '-')
                periode = f"{bulan} {tahun}" if bulan != '-' and tahun != '-' else '-'

                try:
                    nominal = int(pay.get('nominal', 0))
                    nominal_str = f"Rp {nominal:,}"
                except:
                    nominal_str = "-"

                metode = pay.get('metode', 'Transfer Bank')

                status_raw = pay.get('status', '')
                status_label, icon, css_class = format_status(status_raw)

                tanggal = "-"
                if pay.get('waktu'):
                    tanggal = pay['waktu'].split()[0]

                bukti_url = pay.get('bukti', '')
                bukti_html = f"""
                <a href="{bukti_url}" target="_blank" class="payment-link">
                    <i class="fas fa-file-invoice"></i> Lihat
                </a>
                """ if bukti_url else "-"

                table_html += f"""
                <tr>
                    <td>{periode}</td>
                    <td>{nominal_str}</td>
                    <td>{metode}</td>
                    <td class="{css_class}">
                        <i class="fas fa-{icon}"></i> {status_label}
                    </td>
                    <td>{tanggal}</td>
                    <td>{bukti_html}</td>
                </tr>
                """

            table_html += """
                </tbody>
            </table>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)

        else:
            st.markdown("""
            <div style="background-color: rgba(52, 152, 219, 0.1); 
                padding: 25px; border-radius: 8px; text-align: center;
                margin: 20px 0;">
                <i class="fas fa-info-circle" style="font-size: 28px; color: #3498db;"></i>
                <p style="margin-top: 15px; font-size: 16px; color: #7f8c8d;">
                    Belum ada riwayat pembayaran
                </p>
            </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"🔴 Terjadi kesalahan sistem: {str(e)}")

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
