import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import json
import datetime
import plotly.express as px
from fpdf import FPDF

# --- GOOGLE SHEETS AYARI ---
# Kendi tablo linkinizi buraya yapıştırın
TABLO_URL = "https://docs.google.com/spreadsheets/d/1VazM80hR0TkXq7rhwvUCU_1eMwAj8qrOixp1kioLGTc/edit?usp=sharing"

# --- SISTEM AYARLARI ---
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Milli Destan"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen"]
}

# --- VERI YONETIMI (BULUT) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_yukle():
    try:
        df = conn.read(spreadsheet=TABLO_URL, worksheet="Veritabani")
        if not df.empty:
            # Tablodaki JSON verisini çek
            data_str = df.iloc[0]['deger']
            return json.loads(data_str)
    except:
        pass
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    data_str = json.dumps(data, ensure_ascii=False)
    new_df = pd.DataFrame([{"anahtar": "ana_veri", "deger": data_str}])
    conn.update(spreadsheet=TABLO_URL, worksheet="Veritabani", data=new_df)
    st.cache_data.clear()

db = verileri_yukle()

# --- TURKCE KARAKTER VE PDF MOTORU ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, tr_fix(f"LGS GELISIM RAPORU: {user_name.upper()}"), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "1. DENEME ANALIZLERI", ln=True)
    pdf.set_font("Helvetica", '', 9)
    for d in user_data["denemeler"][-5:]:
        pdf.cell(190, 8, f"- Tarih: {d['t']} | Yayin: {tr_fix(d['y'])} | Net: {d['top']}", ln=True)
    return bytes(pdf.output())

# --- PROGRAM ARAYÜZÜ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ LGS Master - Bulut Korumalı")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u, p = st.text_input("Kullanıcı Adı"), st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
else:
    # Sidebar Sayaç
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.error(f"⏳ LGS'ye {kalan.days} GÜN KALDI")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    def forms(uid):
        uv = db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        with t1:
            tar = st.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            c1,c2,c3 = st.columns(3)
            do, ya, bo = c1.number_input("D",0,key=f"do_{uid}"), c2.number_input("Y",0,key=f"ya_{uid}"), c3.number_input("B",0,key=f"bo_{uid}")
            if st.button("Kaydet", key=f"s_{uid}"):
                uv["sorular"].append({"t": str(tar), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Buluta Kaydedildi!")
        with t2:
            yay = st.text_input("Yayın", key=f"y_{uid}")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            t_net = 0
            for ds in DERSLER_KONULAR.keys():
                st.write(f"**{ds}**")
                col1, col2 = st.columns(2)
                dd, dy = col1.number_input("D",0,key=f"{ds}d_{uid}"), col2.number_input("Y",0,key=f"{ds}y_{uid}")
                t_net += round(dd - (dy * 0.33), 2)
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2)})
                veri_kaydet(db); st.success("Buluta Kaydedildi!")
        with t3:
            kad = st.text_input("Kitap", key=f"ka_{uid}")
            ksy = st.number_input("Sayfa Sayısı", 0, key=f"ks_{uid}")
            if st.button("Kitabı Kaydet", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": kad, "s": ksy, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kitap Kaydedildi!")

    if st.session_state.role == "student":
        forms(st.session_state.user)
    else:
        m = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Veri Girişi", "Raporlar"])
        if m == "Öğrenci Kaydı":
            nu, np = st.text_input("Kullanıcı"), st.text_input("Şifre")
            if st.button("Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": []}
                veri_kaydet(db); st.success("Eklendi.")
        elif m == "Veri Girişi":
            so = st.selectbox("Öğrenci", list(db["users"].keys()))
            if so: forms(so)
        elif m == "Raporlar":
            sr = st.selectbox("Öğrenci", list(db["users"].keys()))
            if sr:
                pdf_out = generate_pdf(sr, db["users"][sr])
                st.download_button("📄 PDF Raporu İndir", pdf_out, f"{sr}_Rapor.pdf", "application/pdf")
