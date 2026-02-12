import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
from github import Github # GitHub kütüphanesi

# --- AYARLAR ---
DB_FILE = "lgs_database.json" # Bu dosya GitHub reponda yaratılmış olmalı
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)

DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri", "Yazim Kurallari"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik", "Cebirsel Ifadeler"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Ya Istiklal Ya Olum"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone"]
}

# --- GITHUB OTOMATİK YEDEKLEME FONKSİYONU ---
def github_yedekle(data):
    try:
        # Streamlit Secrets'tan bilgileri al
        token = st.secrets["general"]["GITHUB_TOKEN"]
        repo_name = st.secrets["general"]["REPO_NAME"]
        
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        # Dosyayı bul ve güncelle
        contents = repo.get_contents(DB_FILE)
        repo.update_file(contents.path, "Otomatik Yedekleme (Streamlit)", json.dumps(data, indent=4), contents.sha)
        return True
    except Exception as e:
        st.error(f"GitHub Yedekleme Hatası: {e}")
        return False

# --- VERİ YÖNETİMİ ---
def veri_yukle():
    # Önce yerel dosyaya bak, yoksa boş başlat
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    # 1. Yerel (Hızlı) Kayıt
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state.db = data
    
    # 2. GitHub (Bulut) Kayıt
    if github_yedekle(data):
        st.toast("✅ Veriler GitHub'a güvenle kaydedildi!", icon="☁️")
    else:
        st.toast("⚠️ Sadece yerel kayıt yapıldı.", icon="hdd")

if "db" not in st.session_state:
    st.session_state.db = veri_yukle()

# --- YARDIMCI FONKSİYONLAR ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS RAPORU: {user_name.upper()}"), ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "ATANAN KAYNAKLAR", ln=True)
    pdf.set_font("Helvetica", '', 9)
    for k in user_data.get("kaynaklar", []):
        pdf.cell(190, 7, tr_fix(f"- {k['d']} | {k['k']} | {k['ad']}"), ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME ANALIZI", ln=True)
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in sorted(user_data.get("denemeler", []), key=lambda x: x['t']):
        fark = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(190, 7, tr_fix(f"{d['t']} | {d['y']} | Net: {d['top']} | Degisim: {fark}"), ln=True)
        prev = d['top']
        
    return bytes(pdf.output())

# --- ARAYÜZ ---
st.set_page_config(page_title="LGS Master Pro", page_icon="🏆", layout="wide")

if st.session_state.user is None:
    st.title("🛡️ LGS Master - Otomatik Bulut Yedekli")
    t1, t2 = st.tabs(["Öğrenci", "Öğretmen"])
    with t1:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
            else: st.error("Hatalı Giriş")
    with t2:
        ap = st.text_input("Yönetici Şifre", type="password")
        if st.button("Admin Giriş"):
            if ap == st.session_state.db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()

else:
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.info(f"⏳ LGS'ye {kalan.days} Gün Kaldı")
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()

    def forms(uid):
        uv = st.session_state.db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        
        with t1:
            col1, col2 = st.columns(2)
            tar = col1.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = col2.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            c1,c2,c3 = st.columns(3)
            do, ya, bo = c1.number_input("D",0,key=f"do_{uid}"), c2.number_input("Y",0,key=f"ya_{uid}"), c3.number_input("B",0,key=f"bo_{uid}")
            if st.button("Kaydet", key=f"s_{uid}"):
                uv["sorular"].append({"t": str(tar), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(st.session_state.db)

        with t2:
            yay = st.text_input("Yayın", key=f"y_{uid}")
            dt = st.date_input("Tarih", datetime.date.today(), key=f"dt_{uid}")
            t_net = 0
            den_detay = {}
            for ds in DERSLER_KONULAR.keys():
                with st.expander(ds):
                    x1, x2 = st.columns(2)
                    d_d, d_y = x1.number_input("D",0,key=f"{ds}d_{uid}"), x2.number_input("Y",0,key=f"{ds}y_{uid}")
                    n = round(d_d - (d_y * 0.33), 2)
                    t_net += n
                    den_detay[ds] = {"d":d_d, "y":d_y, "net":n}
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Deneme Kaydet", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2), "detay": den_detay})
                veri_kaydet(st.session_state.db)

        with t3:
            ka = st.text_input("Kitap Adı", key=f"k_{uid}")
            if st.button("Kitap Ekle", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": ka, "t": str(datetime.date.today())})
                veri_kaydet(st.session_state.db)

    if st.session_state.role == "student":
        forms(st.session_state.user)
    elif st.session_state.role == "teacher":
        m = st.sidebar.radio("Menü", ["Öğrenci Ekle", "Veri Girişi", "Kaynak Ata", "Raporlar"])
        if m == "Öğrenci Ekle":
            nu, np = st.text_input("Kullanıcı"), st.text_input("Şifre")
            if st.button("Ekle"):
                st.session_state.db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(st.session_state.db); st.success("Eklendi")
        elif m == "Veri Girişi":
            so = st.selectbox("Seç", list(st.session_state.db["users"].keys()))
            if so: forms(so)
        elif m == "Kaynak Ata":
            so = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            sd = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            sk = st.selectbox("Konu", DERSLER_KONULAR[sd])
            r_ad = st.text_input("Kaynak Adı")
            if st.button("Ata"):
                st.session_state.db["users"][so]["kaynaklar"].append({"d": sd, "k": sk, "ad": r_ad})
                veri_kaydet(st.session_state.db); st.success("Atandı")
        elif m == "Raporlar":
            sr = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            if sr:
                st.download_button("PDF İndir", generate_pdf(sr, st.session_state.db["users"][sr]), f"{sr}.pdf")
