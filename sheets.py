import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
    client = gspread.authorize(creds)
    sheet = client.open("kost-db")  # Nama Google Sheet Anda
    return sheet
