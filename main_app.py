import streamlit as st
import bcrypt
from sheets import connect_gsheet
from app_admin import run_admin
from app_penyewa import run_penyewa

st.set_page_config(page_title="Kost123 Dashboard", layout="wide")

# ---------- Global CSS ----------
st.markdown("""
<style>
body { background-color: #1e1e1e; color: #f0f0f0; font-family: 'Segoe UI', sans-serif; }
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(145deg, #2c2c2c, #3a3a3a); padding: 25px; border-radius: 12px;
}
.sidebar-title { font-size: 26px; font-weight: bold; color: #FFFFFF; margin-bottom: 30px; text-align: center; }
.menu-item { color: #E0E0E0; padding: 14px 25px; margin-bottom: 12px; border-radius: 10px; transition: all 0.3s ease; font-size: 18px; }
.menu-item:hover { background-color: #5a5a5a; cursor: pointer; }
.menu-selected { background-color: #6d6d6d; font-weight: bold; box-shadow: inset 0 0 5px #00000055; }
.info-card { background: rgba(60,60,60,0.5); padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
</style>
""", unsafe_allow_html=True)

# ---------- Session State Initialization ----------
if 'login_status' not in st.session_state:
    st.session_state.login_status = False
    st.session_state.role = None
    st.session_state.username = ""
    st.session_state.menu = None

# ---------- Sidebar Menu ----------
def sidebar_menu():
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🏠 Kost123 Panel</div>', unsafe_allow_html=True)

        if st.session_state.role == "admin":
            menu_options = [
                ("Dashboard Admin", "📊 Dashboard Admin"),
                ("Kelola Kamar", "🛠️ Kelola Kamar"),
                ("Manajemen", "🗂️ Manajemen"),
                ("Verifikasi Booking", "✅ Verifikasi Booking"),
                ("Profil Saya", "👤 Profil Saya"),
                ("Logout", "🚪 Logout")
            ]
        else:
            menu_options = [
                ("Dashboard", "📊 Dashboard"),
                ("Pembayaran", "💸 Pembayaran"),
                ("Komplain", "📢 Komplain"),
                ("Profil Saya", "👤 Profil Saya"),
                ("Logout", "🚪 Logout")
            ]

        for value, label in menu_options:
            is_selected = st.session_state.menu == value
            button_style = "menu-item"
            if is_selected:
                button_style += " menu-selected"
            if st.button(label, key=f"menu_{value}"):
                st.session_state.menu = value

# ---------- Login ----------
def login_page():
    st.title("🔐 Login Kost123")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user_ws = connect_gsheet().worksheet("User")
        users = user_ws.get_all_records()
        for u in users:
            if u['username'] == username and bcrypt.checkpw(password.encode(), u['password_hash'].encode()):
                st.session_state.login_status = True
                st.session_state.username = username
                st.session_state.role = u['role']
                # Set menu awal saat login
                st.session_state.menu = "Dashboard Admin" if u['role'] == 'admin' else "Dashboard"
                st.experimental_rerun()
        st.error("Username atau Password salah.")

# ---------- Routing ----------
if not st.session_state.login_status:
    login_page()
else:
    # Pastikan menu tidak None
    if st.session_state.menu is None:
        st.session_state.menu = "Dashboard Admin" if st.session_state.role == "admin" else "Dashboard"

    sidebar_menu()

    if st.session_state.role == "admin":
        run_admin(st.session_state.menu)
    else:
        run_penyewa(st.session_state.menu)
