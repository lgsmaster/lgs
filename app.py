import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_master_v12.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Milli Destan"],
    "Din": ["Kader İnancı", "Zekat ve Sadaka", "Din ve Hayat"],
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

def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

# --- GELİŞMİŞ PDF MOTORU ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, tr_fix(f"LGS DENEME VE PERFORMANS KARNESI: {user_name.upper()}"), ln=True, align='C')
    pdf.ln(5)

    # 1. DENEME ANALİZ BÖLÜMÜ (YENİ)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(255, 0, 0)
    pdf.cell(190, 10, "AYRINTILI DENEME ANALIZI", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    if user_data["denemeler"]:
        last_d = user_data["denemeler"][-1]
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(190, 8, tr_fix(f"Son Sınav: {last_d['y']} ({last_d['t']}) | Toplam Net: {last_d['top']}"), ln=True)
        
        # Deneme Tablosu
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(45, 8, "Ders Adi", 1, 0, 'C', True)
        pdf.cell(25, 8, "Dogru", 1, 0, 'C', True)
        pdf.cell(25, 8, "Yanlis", 1, 0, 'C', True)
        pdf.cell(25, 8, "Bos", 1, 0, 'C', True)
        pdf.cell(25, 8, "Net", 1, 1, 'C', True)
        
        pdf.set_font("Helvetica", '', 9)
        for ders, skor in last_d["detay"].items():
            pdf.cell(45, 7, tr_fix(ders), 1)
            pdf.cell(25, 7, str(skor['d']), 1, 0, 'C')
            pdf.cell(25, 7, str(skor['y']), 1, 0, 'C')
            pdf.cell(25, 7, str(skor['b']), 1, 0, 'C')
            pdf.cell(25, 7, str(skor['net']), 1, 1, 'C')
    else:
        pdf.cell(190, 10, "Henuz deneme verisi girilmemis.", ln=True)

    # 2. SORU TAKİP TABLOSU
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "GÜNLÜK SORU COZUM DETAYLARI", ln=True)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(200, 220, 255)
    heads = [("Tarih",25), ("Brans",30), ("Konu",65), ("D",12), ("Y",12), ("B",12), ("Toplam",34)]
    for h in heads: pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", '', 7)
    for s in user_data["sorular"][-15:]:
        pdf.cell(25, 6, str(s['t']), 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(65, 6, tr_fix(s['k'][:35]), 1)
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(34, 6, str(int(s['do'])+int(s['ya'])+int(s['bo'])), 1, 1, 'C')

    return bytes(pdf.output())

# --- PROGRAM ARAYÜZÜ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ LGS Master Pro")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u, p = st.text_input("Kullanıcı Adı", key="u"), st.text_input("Şifre", type="password", key="p")
        if st.button("Giriş"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
    with t2:
        ap = st.text_input("Admin Şifre", type="password")
        if st.button("Admin Giriş"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
else:
    # Sidebar - Geri Sayım
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.error(f"⏳ LGS'ye {kalan.days} Gün Kaldı")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    def data_entry(user_id):
        uv = db["users"][user_id]
        tab1, tab2, tab3 = st.tabs(["Soru Girişi", "Deneme Girişi", "Kitap Takibi"])
        with tab1:
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{user_id}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{user_id}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{user_id}")
            c1,c2,c3 = st.columns(3)
            do, ya, bo = c1.number_input("D",0,key=f"do_{user_id}"), c2.number_input("Y",0,key=f"ya_{user_id}"), c3.number_input("B",0,key=f"bo_{user_id}")
            if st.button("Kaydet", key=f"s_{user_id}"):
                uv["sorular"].append({"t": str(t), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")
        with tab2:
            st.write("### Deneme Analiz Formu")
            yay = st.text_input("Yayın/Deneme Adı", key=f"y_{user_id}")
            d_tarih = st.date_input("Deneme Tarihi", datetime.date.today(), key=f"dt_{user_id}")
            d_sonuc = {}; top_net = 0
            for ds in DERSLER_KONULAR.keys():
                st.write(f"**{ds}**")
                col1, col2, col3 = st.columns(3)
                dd = col1.number_input("Doğru", 0, key=f"{ds}d_{user_id}")
                dy = col2.number_input("Yanlış", 0, key=f"{ds}y_{user_id}")
                db_ = col3.number_input("Boş", 0, key=f"{ds}b_{user_id}")
                n = round(dd - (dy * 0.33), 2)
                top_net += n
                d_sonuc[ds] = {"d": dd, "y": dy, "b": db_, "net": n}
            st.metric("Toplam Net", round(top_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{user_id}"):
                uv["denemeler"].append({"t": str(d_tarih), "y": yay, "top": round(top_net, 2), "detay": d_sonuc})
                veri_kaydet(db); st.success("Deneme sisteme işlendi!")
        with tab3:
            st.write("### Kitap Okuma")
            kad = st.text_input("Kitap", key=f"ka_{user_id}")
            yz = st.text_input("Yazar", key=f"yz_{user_id}")
            c1,c2 = st.columns(2)
            bt, bit = c1.date_input("Başlama", key=f"bt_{user_id}"), c2.date_input("Bitiş", key=f"bit_{user_id}")
            if st.button("Kitap Kaydet", key=f"kb_{user_id}"):
                uv["kitaplar"].append({"ad": kad, "yz": yz, "b": str(bt), "bit": str(bit)})
                veri_kaydet(db); st.success("Kitap eklendi!")

    if st.session_state.role == "student":
        data_entry(st.session_state.user)
    else:
        m = st.sidebar.radio("Menü", ["Kayıt", "Veri Girişi", "Kaynak Atama", "Analiz & PDF"])
        if m == "Kayıt":
            nu, np = st.text_input("Kullanıcı"), st.text_input("Şifre")
            if st.button("Öğrenciyi Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci tanımlandı.")
        elif m == "Veri Girişi":
            s_o = st.selectbox("Öğrenci", list(db["users"].keys()))
            if s_o: data_entry(s_o)
        elif m == "Kaynak Atama":
            s_k = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            d_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[d_k])
            kay = st.text_input("Kaynak Adı")
            if st.button("Ata"):
                db["users"][s_k]["kaynaklar"].append({"d": d_k, "k": kn_k, "ad": kay})
                veri_kaydet(db); st.success("Kaynak atandı.")
        elif m == "Analiz & PDF":
            s_r = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if s_r:
                p_bytes = generate_pdf_bytes(s_r, db["users"][s_r])
                st.download_button("📄 Detaylı Analiz PDF'ini İndir", p_bytes, f"{s_r}_Karne.pdf", "application/pdf")
