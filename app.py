import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_master_final_v10.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Milli Destan"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen"]
}

def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = veri_yukle()

# --- TURKCE KARAKTER TEMIZLEME ---
def tr_fix(text):
    # PDF'deki UnicodeEncodingException hatasını onler (image_473f40.png)
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items():
        text = text.replace(old, new)
    return text

# --- PDF MOTORU ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, tr_fix(f"LGS PERFORMANS RAPORU: {user_name.upper()}"), ln=True, align='C')
    pdf.ln(5)

    # 1. Ozet Bilgiler
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "GENEL OZET", ln=True)
    pdf.set_font("Helvetica", '', 10)
    sq = sum(int(s["do"]) + int(s["ya"]) for s in user_data["sorular"])
    pdf.cell(190, 7, f"- Toplam Soru Sayisi: {sq}", ln=True)
    pdf.cell(190, 7, f"- Kayitli Deneme: {len(user_data['denemeler'])}", ln=True)
    pdf.ln(5)

    # 2. Soru Analiz Tablosu
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "SORU COZUM DETAYLARI", ln=True)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(25, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(30, 8, "Brans", 1, 0, 'C', True)
    pdf.cell(65, 8, "Konu", 1, 0, 'C', True)
    pdf.cell(12, 8, "D", 1, 0, 'C', True)
    pdf.cell(12, 8, "Y", 1, 0, 'C', True)
    pdf.cell(12, 8, "B", 1, 0, 'C', True)
    pdf.cell(34, 8, "Toplam", 1, 1, 'C', True)

    pdf.set_font("Helvetica", '', 8)
    for s in user_data["sorular"][-20:]: # Son 20 kayit
        pdf.cell(25, 7, tr_fix(str(s['t'])), 1)
        pdf.cell(30, 7, tr_fix(str(s['d'])), 1)
        pdf.cell(65, 7, tr_fix(str(s['k'][:30])), 1)
        pdf.cell(12, 7, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 7, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 7, str(s['bo']), 1, 0, 'C')
        pdf.cell(34, 7, str(int(s['do'])+int(s['ya'])+int(s['bo'])), 1, 1, 'C')

    return bytes(pdf.output())

# --- LOGIN SİSTEMİ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ LGS Master Yönetim Sistemi")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_in")
        p = st.text_input("Şifre", type="password", key="p_in")
        if st.button("Giriş Yap"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
    with t2:
        ap = st.text_input("Öğretmen Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
else:
    # Sidebar
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"### ⏳ LGS'ye {kalan.days} Gün")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None; st.rerun()

    # --- VERİ GİRİŞ FONKSİYONU ---
    def forms(ukey):
        uv = db["users"][ukey]
        tabs = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        with tabs[0]:
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{ukey}")
            d = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{ukey}")
            k = st.selectbox("Konu", DERSLER_KONULAR[d], key=f"k_{ukey}")
            c1,c2,c3 = st.columns(3)
            do, ya, bo = c1.number_input("D",0,key=f"do_{ukey}"), c2.number_input("Y",0,key=f"ya_{ukey}"), c3.number_input("B",0,key=f"bo_{ukey}")
            if st.button("Kaydet", key=f"sb_{ukey}"):
                uv["sorular"].append({"t": str(t), "d": d, "k": k, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")
        with tabs[1]:
            yay = st.text_input("Yayın", key=f"y_{ukey}")
            st.info("Netler otomatik hesaplanır (3Y 1D'yi götürür).")
            # ... Deneme detayları ...
            if st.button("Deneme Kaydet", key=f"db_{ukey}"):
                uv["denemeler"].append({"t": str(datetime.date.today()), "y": yay, "top": 0})
                veri_kaydet(db); st.success("Eklendi!")
        with tabs[2]:
            k_ad = st.text_input("Kitap", key=f"ka_{ukey}")
            c1,c2 = st.columns(2)
            b_t, bit_t = c1.date_input("Baslangıc", key=f"bt_{ukey}"), c2.date_input("Bitis", key=f"bit_{ukey}")
            if st.button("Kitap Kaydet", key=f"kb_{ukey}"):
                uv["kitaplar"].append({"ad": k_ad, "b": str(b_t), "bit": str(bit_t)})
                veri_kaydet(db); st.success("Kitap Eklendi!")

    # --- ROLLER ---
    if st.session_state.role == "student":
        forms(st.session_state.user)
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Öğrenci Veri Girişi", "Kaynak-Konu Atama", "Raporlar"])
        if menu == "Öğrenci Kaydı":
            nu = st.text_input("Kullanıcı Adı"); np = st.text_input("Şifre")
            if st.button("Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci eklendi.")
        elif menu == "Öğrenci Veri Girişi":
            sec = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec: forms(sec)
        elif menu == "Kaynak-Konu Atama":
            sec_o = st.selectbox("Öğrenci", list(db["users"].keys()))
            d_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[d_k])
            kay_ad = st.text_input("Kaynak Kitap Adı")
            if st.button("Kaynağı Ata"):
                db["users"][sec_o]["kaynaklar"].append({"d": d_k, "k": kn_k, "ad": kay_ad})
                veri_kaydet(db); st.success("Kaynak atandı.")
        elif menu == "Raporlar":
            sec_r = st.selectbox("Öğrenci", list(db["users"].keys()))
            if sec_r:
                p_out = generate_pdf_bytes(sec_r, db["users"][sec_r])
                st.download_button("📄 Tablolu PDF Karne İndir", p_out, f"{sec_r}_Karne.pdf", "application/pdf")
