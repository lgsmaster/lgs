import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
from github import Github

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="LGS Master Pro", page_icon="🏆", layout="wide")

# --- 2. AYARLAR ---
DB_FILE = "lgs_platinum_db.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)

DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri", "Yazim Kurallari"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik", "Cebirsel Ifadeler"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Ya Istiklal Ya Olum"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone"]
}

# --- 3. GITHUB OTOMATİK YEDEKLEME ---
def github_yedekle(data):
    try:
        if "general" in st.secrets:
            token = st.secrets["general"]["GITHUB_TOKEN"]
            repo_name = st.secrets["general"]["REPO_NAME"]
            g = Github(token)
            repo = g.get_repo(repo_name)
            try:
                contents = repo.get_contents(DB_FILE)
                repo.update_file(contents.path, "Oto-Yedek", json.dumps(data, indent=4), contents.sha)
            except:
                repo.create_file(DB_FILE, "İlk Kurulum", json.dumps(data, indent=4))
            return True
        return False
    except Exception as e:
        print(f"Yedekleme Hatası: {e}")
        return False

# --- 4. VERİ YÖNETİMİ ---
def veri_yukle():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "admin_sifre" not in data: data["admin_sifre"] = "admin123"
            return data
        except:
            pass
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    # Yerel Kayıt
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state.db = data
    
    # Bulut Kayıt
    if github_yedekle(data):
        st.toast("☁️ GitHub'a yedeklendi!", icon="✅")
    else:
        st.toast("💾 Yerel kayıt yapıldı.", icon="ℹ️")

if "db" not in st.session_state: st.session_state.db = veri_yukle()
if "user" not in st.session_state: st.session_state.user = None

# --- 5. PDF MOTORU (DÜZELTİLDİ: TAM İSTEDİĞİN GİBİ) ---
def tr_fix(text):
    # Türkçe karakterleri PDF uyumlu hale getirir
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf_report(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. MAVİ BAŞLIK
    pdf.set_fill_color(31, 119, 180) # Lacivert
    pdf.set_text_color(255, 255, 255) # Beyaz Yazı
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS PERFORMANS KARNESI: {user_name.upper()}"), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0) # Siyah yazıya dön
    pdf.ln(5)

    # 2. ÖZET BİLGİLER
    pdf.set_font("Helvetica", 'B', 10)
    top_soru = sum(int(s['do'])+int(s['ya'])+int(s['bo']) for s in user_data.get("sorular", []))
    pdf.cell(190, 6, f"Toplam Cozulen Soru: {top_soru} | Girilen Deneme: {len(user_data.get('denemeler', []))}", ln=True)
    pdf.ln(5)

    # 3. DENEME ANALİZ TABLOSU
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME SINAVLARI NET GELISIMI", ln=True)
    
    # Tablo Başlıkları
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230) # Gri arka plan
    pdf.cell(35, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(65, 8, "Yayin", 1, 0, 'C', True)
    pdf.cell(45, 8, "Toplam Net", 1, 0, 'C', True)
    pdf.cell(45, 8, "Degisim", 1, 1, 'C', True)
    
    # Tablo Verileri
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in sorted(user_data.get("denemeler", []), key=lambda x: x['t']):
        degisim = round(d['top'] - prev, 2) if prev is not None else "-"
        # Pozitif değişime + işareti
        if isinstance(degisim, float) and degisim > 0: degisim = f"+{degisim}"
        
        pdf.cell(35, 7, d['t'], 1, 0, 'C')
        pdf.cell(65, 7, tr_fix(d['y']), 1)
        pdf.cell(45, 7, str(d['top']), 1, 0, 'C')
        pdf.cell(45, 7, str(degisim), 1, 1, 'C')
        prev = d['top']

    pdf.ln(10)

    # 4. SORU ÇÖZÜM TABLOSU (DETAYLI)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "SON COZULEN SORULAR (DETAYLI DOKUM)", ln=True)
    
    # Başlıklar
    pdf.set_font("Helvetica", 'B', 8)
    # Sütun Genişlikleri: Tarih(25), Ders(30), Konu(60), D(12), Y(12), B(12), Top(39)
    headers = [("Tarih",25), ("Ders",30), ("Konu",60), ("D",12), ("Y",12), ("B",12), ("Toplam",39)]
    for h in headers:
        pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    
    # Veriler (Son 25 kayıt)
    pdf.set_font("Helvetica", '', 7)
    for s in user_data.get("sorular", [])[-25:]:
        total = int(s['do']) + int(s['ya']) + int(s['bo'])
        pdf.cell(25, 6, s['t'], 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(60, 6, tr_fix(s['k'][:32]), 1) # Uzun konuları kes
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(39, 6, str(total), 1, 1, 'C')

    # 5. KAYNAKLAR
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "ATANAN KAYNAKLAR", ln=True)
    pdf.set_font("Helvetica", '', 9)
    if user_data.get("kaynaklar"):
        for k in user_data["kaynaklar"]:
            pdf.cell(190, 7, tr_fix(f"- {k['d']} | {k['k']} | {k['ad']}"), ln=True)
    else:
        pdf.cell(190, 7, "Kayitli kaynak bulunamadi.", ln=True)

    return bytes(pdf.output())

# --- 6. ARAYÜZ ---
if st.session_state.user is None:
    st.title("🛡️ LGS Master Pro")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Giriş"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
            else: st.error("Hatalı Giriş")
    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Giriş"):
            if ap == st.session_state.db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
            else: st.error("Hatalı Şifre")

else:
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"<div style='background:#d32f2f;color:white;padding:10px;border-radius:5px;text-align:center;'><b>⏳ LGS'YE {kalan.days} GÜN</b></div>", unsafe_allow_html=True)
    st.sidebar.write(f"👤 {st.session_state.user}")
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()

    def data_hub(uid):
        uv = st.session_state.db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        
        # --- SORU GİRİŞİ ---
        with t1:
            c1, c2 = st.columns(2)
            tar = c1.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = c2.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            # Key çakışmasını önlemek için 'soru_konu_'
            ko =
