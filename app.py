import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- KONFİGÜRASYON ---
DB_FILE = "lgs_master_final_v15.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Milli Destan"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen"]
}

# --- VERİ FONKSİYONLARI ---
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

# --- PDF KARNE MOTORU ---
def generate_pdf_report(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(31, 119, 180) # Lacivert başlık
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS STRATEJI VE ANALIZ RAPORU: {user_name.upper()}"), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # Deneme Analizi
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "1. DENEME GELISIM ANALIZI", ln=True)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(35, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(65, 8, "Yayin", 1, 0, 'C', True)
    pdf.cell(45, 8, "Net", 1, 0, 'C', True)
    pdf.cell(45, 8, "Degisim", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in user_data["denemeler"]:
        degisim = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(35, 7, d['t'], 1, 0, 'C')
        pdf.cell(65, 7, tr_fix(d['y']), 1)
        pdf.cell(45, 7, str(d['top']), 1, 0, 'C')
        pdf.cell(45, 7, str(degisim), 1, 1, 'C')
        prev = d['top']

    # Soru Tablosu
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "2. SORU COZUM DETAYLARI (SON 20)", ln=True)
    heads = [("Tarih",25), ("Ders",30), ("Konu",65), ("D",12), ("Y",12), ("B",12), ("Top",34)]
    pdf.set_font("Helvetica", 'B', 8)
    for h in heads: pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 7)
    for s in user_data["sorular"][-20:]:
        pdf.cell(25, 6, s['t'], 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(65, 6, tr_fix(s['k'][:35]), 1)
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(34, 6, str(int(s['do'])+int(s['ya'])+int(s['bo'])), 1, 1, 'C')

    return bytes(pdf.output())

# --- PROGRAM ---
st.set_page_config(page_title="LGS Master Pro", layout="wide")

if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🚀 LGS Master Strateji Portalı")
    col1, col2 = st.tabs(["🔐 Öğrenci Girişi", "👨‍🏫 Öğretmen Girişi"])
    with col1:
        u, p = st.text_input("Kullanıcı Adı"), st.text_input("Şifre", type="password")
        if st.button("Sisteme Gir"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
    with col2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()

else:
    # Sidebar Analizleri
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.success(f"🎯 LGS Hedefine: {kalan.days} GÜN")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    def data_hub(uid):
        uv = db["users"][uid]
        c1, c2, c3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Girişi", "📚 Kitap Takibi"])
        
        with c1:
            tar = st.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            cl1, cl2, cl3 = st.columns(3)
            do, ya, bo = cl1.number_input("D",0,key=f"do_{uid}"), cl2.number_input("Y",0,key=f"ya_{uid}"), cl3.number_input("B",0,key=f"bo_{uid}")
            if st.button("Veriyi Kaydet", key=f"s_{uid}"):
                uv["sorular"].append({"t": str(tar), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Soru verisi işlendi!")

        with c2:
            st.subheader("3 Yanlış 1 Doğruyu Götürür Net Hesabı")
            yay = st.text_input("Yayın Adı", key=f"y_{uid}")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            res, top_net = {}, 0
            for ds in DERSLER_KONULAR.keys():
                st.write(f"**{ds}**")
                x1, x2, x3 = st.columns(3)
                d_do, d_ya, d_bo = x1.number_input("D",0,key=f"{ds}d_{uid}"), x2.number_input("Y",0,key=f"{ds}y_{uid}"), x3.number_input("B",0,key=f"{ds}b_{uid}")
                n = round(d_do - (d_ya * 0.33), 2)
                top_net += n
                res[ds] = {"d": d_do, "y": d_ya, "b": d_bo, "net": n}
            st.metric("Hesaplanan Toplam Net", round(top_net, 2))
            if st.button("Denemeyi Arşive Ekle", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(top_net, 2), "detay": res})
                uv["denemeler"] = sorted(uv["denemeler"], key=lambda x: x["t"])
                veri_kaydet(db); st.success("Deneme analizi kaydedildi!")

        with c3:
            kad, kyz = st.text_input("Kitap", key=f"ka_{uid}"), st.text_input("Yazar", key=f"ky_{uid}")
            ksy = st.number_input("Sayfa Sayısı", 0, key=f"ks_{uid}")
            b1, b2 = st.columns(2)
            bt, bitt = b1.date_input("Başlama", key=f"b_{uid}"), b2.date_input("Bitiş", key=f"bit_{uid}")
            if st.button("Kitabı Kaydet", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": kad, "yz": kyz, "s": ksy, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(db); st.success("Kitap listeye eklendi!")

    if st.session_state.role == "student":
        st.header(f"👋 Hoş Geldin, {st.session_state.user}")
        m = st.sidebar.radio("İşlem Menüsü", ["Veri Girişi", "Gelişim Grafiklerim"])
        if m == "Veri Girişi": data_hub(st.session_state.user)
        else:
            uv = db["users"][st.session_state.user]
            if uv["denemeler"]:
                df = pd.DataFrame(uv["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Deneme Gelişim Trendi", markers=True))
                st.table(df[["t", "y", "top"]])

    elif st.session_state.role == "teacher":
        st.header("👨‍🏫 Öğretmen Yönetim Merkezi")
        m = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Öğrenci Veri Girişleri", "Kaynak & Ödev Atama", "Analitik Raporlar"])
        
        if m == "Öğrenci Kaydı":
            nu, np = st.text_input("Yeni Kullanıcı"), st.text_input("Şifre")
            if st.button("Öğrenciyi Sisteme Ekle"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci kaydedildi.")

        elif m == "Öğrenci Veri Girişleri":
            so = st.selectbox("Veri Girişi Yapılacak Öğrenci", list(db["users"].keys()))
            if so: data_hub(so)

        elif m == "Kaynak & Ödev Atama":
            so = st.selectbox("Öğrenci", list(db["users"].keys()))
            dk = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kk = st.selectbox("Konu", DERSLER_KONULAR[dk])
            kay = st.text_input("Kaynak/Ödev Adı")
            if st.button("Atamayı Yap"):
                db["users"][so]["kaynaklar"].append({"d": dk, "k": kk, "ad": kay, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak öğrenciye iletildi.")

        elif m == "Analitik Raporlar":
            sr = st.selectbox("Analiz Edilecek Öğrenci", list(db["users"].keys()))
            if sr:
                vr = db["users"][sr]
                st.write(f"### {sr} İçin Canlı Özet")
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Okunan Sayfa", sum(int(k["s"]) for k in vr["kitaplar"]))
                col3.metric("Deneme Sayısı", len(vr["denemeler"]))
                
                pdf_bytes = generate_pdf_report(sr, vr)
                st.download_button("📄 Profesyonel PDF Raporu İndir", pdf_bytes, f"{sr}_Analiz.pdf", "application/pdf")
