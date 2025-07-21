import streamlit as st
import bcrypt
from datetime import datetime
from sheets import connect_gsheet
from app_admin import run_admin
from app_penyewa import run_penyewa

# ---------- Page Config ----------
st.set_page_config(
    page_title="Kost123 Dashboard",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------- Global CSS ----------
st.markdown("""
<style>
    :root {
        --primary-color: #42A5F5;
        --secondary-color: #66BB6A;
        --danger-color: #EF5350;
        --bg-dark: #1e1e1e;
        --bg-card: rgba(60,60,60,0.5);
    }
    
    body { 
        background-color: var(--bg-dark); 
        color: #f0f0f0; 
        font-family: 'Segoe UI', sans-serif; 
    }
    
    [data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(145deg, #2c2c2c, #3a3a3a); 
        padding: 25px; 
        border-radius: 12px;
    }
    
    .sidebar-title { 
        font-size: 26px; 
        font-weight: bold; 
        color: #FFFFFF; 
        margin-bottom: 30px; 
        text-align: center; 
    }
    
    .menu-item { 
        color: #E0E0E0; 
        padding: 14px 25px; 
        margin-bottom: 12px; 
        border-radius: 10px; 
        transition: all 0.3s ease; 
        font-size: 18px; 
        width: 100%;
        text-align: left;
    }
    
    .menu-item:hover { 
        background-color: #5a5a5a; 
        cursor: pointer; 
    }
    
    .menu-selected { 
        background-color: #6d6d6d; 
        font-weight: bold; 
        box-shadow: inset 0 0 5px #00000055; 
    }
    
    .info-card { 
        background: var(--bg-card); 
        padding: 20px; 
        border-radius: 12px; 
        margin-bottom: 20px; 
        box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
    }
    
    /* Login page styling */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 30px;
        border-radius: 12px;
        background: var(--bg-card);
    }
    
    /* Notification styles */
    .stNotification {
        border-radius: 12px !important;
    }
</style>
""", unsafe_allow_html=True)


# ---------- Session State Initialization ----------
def init_session_state():
    """Initialize all required session state variables with default values"""
    required_keys = {
        'login_status': False,
        'role': None,
        'username': "",
        'menu': None,
        'last_activity': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    for key, default_value in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# ---------- Sidebar Menu ----------
def sidebar_menu():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)
        
        # User info
        if st.session_state.login_status:
            user_ws = connect_gsheet().worksheet("User")
            users = user_ws.get_all_records()
            user_data = next((u for u in users if u['username'] == st.session_state.username), None)
            
            if user_data:
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.image(user_data.get('foto_profil', "https://via.placeholder.com/50"), width=50)
                with col2:
                    st.markdown(f"""
                    <div style="margin-top: 10px;">
                        <strong>{user_data.get('nama_lengkap', st.session_state.username)}</strong><br>
                        <small>{st.session_state.role.capitalize()}</small>
                    </div>
                    """, unsafe_allow_html=True)
                st.markdown("---")

        # Menu options
        if st.session_state.role == "admin":
            menu_options = [
                ("Dashboard Admin", "📊 Dashboard"),
                ("Kelola Kamar", "🛏️ Kelola Kamar"),
                ("Manajemen", "👥 Manajemen"),
                ("Verifikasi Booking", "✅ Verifikasi"),
                ("Profil", "👤 Profil"),
                ("Logout", "🚪 Logout")
            ]
        else:
            menu_options = [
                ("Dashboard", "📊 Beranda"),
                ("Pembayaran", "💸 Pembayaran"),
                ("Komplain", "📢 Komplain"),
                ("Fasilitas", "🏊 Fasilitas"),
                ("Profil", "👤 Profil"),
                ("Logout", "🚪 Logout")
            ]

        for value, label in menu_options:
            is_selected = st.session_state.menu == value
            button_style = "menu-item"
            if is_selected:
                button_style += " menu-selected"
            if st.button(label, key=f"menu_{value}"):
                st.session_state.menu = value
                st.session_state.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ---------- Login ----------
def login_page():
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.title("🔐 Login Kost123")
        
        with st.form(key='login_form'):
            username = st.text_input("Username", placeholder="Masukkan username Anda")
            password = st.text_input("Password", type="password", placeholder="Masukkan password Anda")
            
            if st.form_submit_button("Login", use_container_width=True):
                if not username or not password:
                    st.error("Username dan password harus diisi!")
                else:
                    try:
                        user_ws = connect_gsheet().worksheet("User")
                        users = user_ws.get_all_records()
                        user = next((u for u in users if u['username'] == username), None)
                        
                        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
                            # Update last login
                            all_users = user_ws.get_all_values()
                            row_num = next((i+1 for i, row in enumerate(all_users) if row[0] == username), None)
                            if row_num:
                                user_ws.update_cell(row_num, 9, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))  # last_login
                            
                            # Set session state
                            st.session_state.login_status = True
                            st.session_state.username = username
                            st.session_state.role = user['role']
                            st.session_state.menu = "Dashboard Admin" if user['role'] == 'admin' else "Dashboard"
                            st.session_state.last_activity = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            st.rerun()
                        else:
                            st.error("Username atau password salah!")
                    except Exception as e:
                        st.error(f"Terjadi kesalahan saat login: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- Auto Logout ----------
def check_inactivity():
    if st.session_state.login_status:
        last_activity = datetime.strptime(st.session_state.last_activity, "%Y-%m-%d %H:%M:%S")
        inactive_duration = datetime.now() - last_activity
        
        if inactive_duration.total_seconds() > 1800:  # 30 menit
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

# ---------- Main App ----------
def main():
    init_session_state()  # Initialize session state first
    check_inactivity()
    
    if not st.session_state.login_status:
        login_page()
    else:
        if st.session_state.menu is None:
            st.session_state.menu = "Dashboard Admin" if st.session_state.role == "admin" else "Dashboard"
        
        sidebar_menu()
        
        try:
            if st.session_state.role == "admin":
                run_admin(st.session_state.menu)
            else:
                run_penyewa(st.session_state.menu)
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
            st.button("Refresh Halaman", on_click=lambda: st.rerun())

if __name__ == "__main__":
    main()
