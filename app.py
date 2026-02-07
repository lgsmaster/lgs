import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_pro_v8.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Türkçe": ["Paragraf", "Sözcükte Anlam", "Cümlede Anlam", "Fiilimsiler", "Cümlenin Öğeleri"],
    "Matematik": ["Çarpanlar ve Katlar", "Üslü İfadeler", "Kareköklü İfadeler", "Veri Analizi", "Olasılık"],
    "Fen": ["Mevsimler ve İklim", "DNA ve Genetik Kod", "Basınç", "Madde ve Endüstri"],
    "İnkılap": ["Bir Kahraman Doğuyor", "Milli Uyanış", "Milli Destan"],
    "Din": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat"],
    "İngilizce": ["Friendship", "Teen Life", "In The Kitchen"]
}

def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = veri_yukle()

# --- GELİŞMİŞ PDF MOTORU (TABLO DESTEKLİ) ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, f"LGS PERFORMANS RAPORU: {user_name.upper()}", ln=True, align='C')
    pdf.ln(5)

    # 1. ÖZET METRİKLER
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "GENEL OZET", ln=True)
    pdf.set_font("Helvetica", '', 10)
    total_q = sum(int(s["do"]) + int(s["ya"]) for s in user_data["sorular"])
    pdf.cell(190, 7, f"- Toplam Cozulen Soru Sayisi: {total_q}", ln=True)
    pdf.cell(190, 7, f"- Kayitli Deneme Sayisi: {len(user_data['denemeler'])}", ln=True)
    pdf.cell(190, 7, f"- Tamamlanan Kaynak Sayisi: {len(user_data['kaynaklar'])}", ln=True)
    pdf.ln(5)

    # 2. SORU ANALİZ TABLOSU
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "SORU COZUM DETAYLARI (TABLO)", ln=True)
    
    # Tablo Başlıkları
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(25, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(35, 8, "Brans", 1, 0, 'C', True)
    pdf.cell(60, 8, "Konu", 1, 0, 'C', True)
    pdf.cell(15, 8, "D", 1, 0, 'C', True)
    pdf.cell(15, 8, "Y", 1, 0, 'C', True)
    pdf.cell(15, 8, "B", 1, 0, 'C', True)
    pdf.cell(25, 8, "Toplam", 1, 1, 'C', True)

    # Tablo Verileri
    pdf.set_font("Helvetica", '', 8)
    for s in user_data["sorular"][-20:]: # Son 20 girişi listele
        total = int(s['do']) + int(s['ya']) + int(s['bo'])
        pdf.cell(25, 7, s['t'], 1)
        pdf.cell(35, 7, s['d'], 1)
        pdf.cell(60, 7, s['k'][:30], 1) # Uzun konuları keser
        pdf.cell(15, 7, str(s['do']), 1, 0, 'C')
        pdf.cell(15, 7, str(s['ya']), 1, 0, 'C')
        pdf.cell(15, 7, str(s['bo']), 1, 0, 'C')
        pdf.cell(25, 7, str(total), 1, 1, 'C')

    return bytes(pdf.output())

# --- LOGIN ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🚀 LGS Master Koçluk Sistemi")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="ulog")
        p = st.text_input("Şifre", type="password", key="plog")
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
    # Sidebar Sayaç
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.info(f"⏳ LGS'ye: {kalan.days} Gün Kaldı")
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None; st.rerun()

    def data_form(target_user):
        u_v = db["users"][target_user]
        tab1, tab2, tab3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        with tab1:
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{target_user}")
            drs = st.selectbox("Branş", list(DERSLER_KONULAR.keys()), key=f"d_{target_user}")
            kn = st.selectbox("Konu", DERSLER_KONULAR[drs], key=f"k_{target_user}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{target_user}")
            ya = c2.number_input("Y", 0, key=f"ya_{target_user}")
            bo = c3.number_input("B", 0, key=f"bo_{target_user}")
            if st.button("Kaydet", key=f"sb_{target_user}"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")
        # ... (Deneme ve Kitap Girişleri Aynı Kalacak) ...

    if st.session_state.role == "student":
        data_form(st.session_state.user)

    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Menü", ["Öğrenci Kayıt", "Veri Girişleri", "Kaynak Yönetimi", "Raporlar"])
        
        if menu == "Kaynak Yönetimi":
            st.header("📚 Kaynak-Konu Atama")
            sec_o = st.selectbox("Öğrenci", list(db["users"].keys()))
            drs_k = st.selectbox("Branş", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("İlgili Konu", DERSLER_KONULAR[drs_k])
            kay_ad = st.text_input("Kitap/Kaynak Adı")
            if st.button("Kaynağı Tanımla"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak öğrenci listesine eklendi.")

        elif menu == "Raporlar":
            sec_r = st.selectbox("Öğrenci", list(db["users"].keys()))
            if sec_r:
                pdf_out = generate_pdf_bytes(sec_r, db["users"][sec_r])
                st.download_button("📄 PDF Tablolu Raporu İndir", pdf_out, f"{sec_r}_Analiz.pdf", "application/pdf")
