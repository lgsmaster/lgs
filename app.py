import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_master_final_v14.json"
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

def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

# --- GELİŞMİŞ PDF MOTORU ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, tr_fix(f"LGS GELISIM KARNESI: {user_name.upper()}"), ln=True, align='C')
    pdf.ln(5)

    # 1. Deneme Gelişim Tablosu
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME SINAVLARI KIYAS ANALIZI", ln=True)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(220, 230, 240)
    pdf.cell(30, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(60, 8, "Yayinevi", 1, 0, 'C', True)
    pdf.cell(30, 8, "Net", 1, 0, 'C', True)
    pdf.cell(30, 8, "Artis/Azalis", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in user_data["denemeler"]:
        fark = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(30, 7, d['t'], 1, 0, 'C')
        pdf.cell(60, 7, tr_fix(d['y']), 1)
        pdf.cell(30, 7, str(d['top']), 1, 0, 'C')
        pdf.cell(30, 7, str(fark), 1, 1, 'C')
        prev = d['top']

    # 2. Soru Takip Tablosu
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "GÜNLÜK COZULEN SORU TABLOSU", ln=True)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    cols = [("Tarih",25), ("Brans",30), ("Konu",65), ("D",12), ("Y",12), ("B",12), ("Top",34)]
    for c in cols: pdf.cell(c[1], 8, c[0], 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 7)
    for s in user_data["sorular"][-15:]:
        pdf.cell(25, 6, s['t'], 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(65, 6, tr_fix(s['k'][:35]), 1)
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(34, 6, str(int(s['do'])+int(s['ya'])+int(s['bo'])), 1, 1, 'C')

    return bytes(pdf.output())

# --- GİRİŞ VE SİSTEM ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🏆 LGS Master Yönetim Paneli")
    t1, t2 = st.tabs(["Öğrenci", "Öğretmen"])
    with t1:
        u, p = st.text_input("Kullanıcı"), st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
    with t2:
        ap = st.text_input("Admin Şifre", type="password")
        if st.button("Admin Giriş"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
else:
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.error(f"⏳ LGS'ye {kalan.days} GÜN KALDI")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    def main_form(uid):
        uv = db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        with t1:
            tar = st.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            c1,c2,c3 = st.columns(3)
            do, ya, bo = c1.number_input("D",0,key=f"do_{uid}"), c2.number_input("Y",0,key=f"ya_{uid}"), c3.number_input("B",0,key=f"bo_{uid}")
            if st.button("Soru Kaydet", key=f"s_{uid}"):
                uv["sorular"].append({"t": str(tar), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")
        with t2:
            st.subheader("Deneme Net Hesaplama (3Y 1D'yi Götürür)")
            yay = st.text_input("Yayın", key=f"y_{uid}")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            d_res, t_net = {}, 0
            for ds in DERSLER_KONULAR.keys():
                st.write(f"**{ds}**")
                col1, col2, col3 = st.columns(3)
                d_do, d_ya, d_bo = col1.number_input("D",0,key=f"{ds}d_{uid}"), col2.number_input("Y",0,key=f"{ds}y_{uid}"), col3.number_input("B",0,key=f"{ds}b_{uid}")
                n = round(d_do - (d_ya * 0.33), 2)
                t_net += n
                d_res[ds] = {"d": d_do, "y": d_ya, "b": d_bo, "net": n}
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2), "detay": d_res})
                uv["denemeler"] = sorted(uv["denemeler"], key=lambda x: x["t"])
                veri_kaydet(db); st.success("Deneme eklendi!")
        with t3:
            kad, kyz = st.text_input("Kitap", key=f"ka_{uid}"), st.text_input("Yazar", key=f"ky_{uid}")
            ksy = st.number_input("Sayfa Sayısı", 0, key=f"ks_{uid}")
            b, bit = st.date_input("Başlama", key=f"b_{uid}"), st.date_input("Bitiş", key=f"bit_{uid}")
            if st.button("Kitap Kaydet", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": kad, "yz": kyz, "s": ksy, "b": str(b), "bit": str(bit)})
                veri_kaydet(db); st.success("Kitap eklendi!")

    if st.session_state.role == "student":
        m = st.sidebar.radio("Menü", ["Veri Girişi", "Gelişimim"])
        if m == "Veri Girişi": main_form(st.session_state.user)
        else:
            uv = db["users"][st.session_state.user]
            if uv["denemeler"]:
                st.plotly_chart(px.line(pd.DataFrame(uv["denemeler"]), x="t", y="top", title="Net Gelişimi"))

    elif st.session_state.role == "teacher":
        m = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Veri Girişleri", "Kaynak-Konu Atama", "Raporlar & Analiz"])
        if m == "Öğrenci Kaydı":
            nu, np = st.text_input("Kullanıcı"), st.text_input("Şifre")
            if st.button("Öğrenciyi Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Eklendi.")
        elif m == "Veri Girişleri":
            so = st.selectbox("Öğrenci", list(db["users"].keys()))
            if so: main_form(so)
        elif m == "Kaynak-Konu Atama":
            so, dr_k = st.selectbox("Öğrenci", list(db["users"].keys())), st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k, kay = st.selectbox("Konu", DERSLER_KONULAR[dr_k]), st.text_input("Kaynak Adı")
            if st.button("Ata"):
                db["users"][so]["kaynaklar"].append({"d": dr_k, "k": kn_k, "ad": kay})
                veri_kaydet(db); st.success("Atandı.")
        elif m == "Raporlar & Analiz":
            sr = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sr:
                p_bytes = generate_pdf_bytes(sr, db["users"][sr])
                st.download_button("📄 Gelişim Analizli PDF Raporu İndir", p_bytes, f"{sr}_Karne.pdf", "application/pdf")
