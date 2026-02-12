import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_database.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Milli Destan"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen"]
}

# --- VERİ YÖNETİMİ (ZIRHLI SİSTEM) ---
def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    # Yerel dosyaya yaz
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    # Veriyi session state'de güncelle
    st.session_state.db = data

if "db" not in st.session_state:
    st.session_state.db = veri_yukle()

# --- TÜRKÇE KARAKTER VE PDF ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, tr_fix(f"LGS GELISIM RAPORU: {user_name.upper()}"), ln=True, align='C')
    
    # Deneme Analizi
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME SINAVLARI KIYAS ANALIZI", ln=True)
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in user_data.get("denemeler", []):
        fark = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(190, 8, tr_fix(f"- {d['t']} | {d['y']} | Net: {d['top']} | Artis: {fark}"), ln=True)
        prev = d['top']
    
    return bytes(pdf.output())

# --- GİRİŞ KONTROLÜ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🛡️ LGS Master Pro - Zırhlı Sistem")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Giriş Yap"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == st.session_state.db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
else:
    # Sidebar
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.error(f"⏳ LGS'ye {kalan.days} GÜN KALDI")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    def full_forms(uid):
        uv = st.session_state.db["users"][uid]
        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Sınavı", "📚 Kitap Takibi"])
        
        with tab1:
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            c1,c2,c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{uid}")
            ya = c2.number_input("Y", 0, key=f"ya_{uid}")
            bo = c3.number_input("B", 0, key=f"bo_{uid}")
            if st.button("Soru Kaydet", key=f"sb_{uid}"):
                uv["sorular"].append({"t": str(t), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(st.session_state.db); st.success("Kaydedildi!")

        with tab2:
            yay = st.text_input("Yayın Adı", key=f"y_{uid}")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            t_net = 0
            for ds in DERSLER_KONULAR.keys():
                st.write(f"**{ds}**")
                col1, col2 = st.columns(2)
                dd = col1.number_input("D", 0, key=f"{ds}d_{uid}")
                dy = col2.number_input("Y", 0, key=f"{ds}y_{uid}")
                t_net += round(dd - (dy * 0.33), 2)
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2)})
                uv["denemeler"] = sorted(uv["denemeler"], key=lambda x: x["t"])
                veri_kaydet(st.session_state.db); st.success("Deneme Eklendi!")

        with tab3:
            kad = st.text_input("Kitap", key=f"ka_{uid}")
            kyz = st.text_input("Yazar", key=f"ky_{uid}")
            ksy = st.number_input("Sayfa", 0, key=f"ks_{uid}")
            c1, c2 = st.columns(2)
            bt, bitt = c1.date_input("Baslama", key=f"bt_{uid}"), c2.date_input("Bitis", key=f"bitt_{uid}")
            if st.button("Kitabı Kaydet", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": kad, "yz": kyz, "s": ksy, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(st.session_state.db); st.success("Kitap Eklendi!")

    if st.session_state.role == "student":
        full_forms(st.session_state.user)
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Öğrenci Veri Girişleri", "Raporlar"])
        if menu == "Öğrenci Kaydı":
            nu = st.text_input("Kullanıcı Adı")
            np = st.text_input("Şifre")
            if st.button("Kaydet"):
                st.session_state.db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": []}
                veri_kaydet(st.session_state.db); st.success("Öğrenci tanımlandı.")
        elif menu == "Öğrenci Veri Girişleri":
            sec = st.selectbox("Öğrenci Seç", list(st.session_state.db["users"].keys()))
            if sec: full_forms(sec)
        elif menu == "Raporlar":
            sr = st.selectbox("Öğrenci Seç", list(st.session_state.db["users"].keys()))
            if sr:
                pdf_out = generate_pdf(sr, st.session_state.db["users"][sr])
                st.download_button("📄 Gelişim Analizli PDF İndir", pdf_out, f"{sr}_Rapor.pdf", "application/pdf")
