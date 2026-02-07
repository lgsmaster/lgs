import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
import io

# --- VERİ YÖNETİMİ ---
DB_FILE = "lgs_pro_v7.json"
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

# --- PDF OLUŞTURMA MOTORU ---
def create_pdf(user_name, data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, f"LGS PERFORMANS RAPORU: {user_name.upper()}", ln=True, align='C')
    pdf.ln(10)
    
    # Soru Özeti
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. Soru Cozum Ozeti", ln=True)
    pdf.set_font("Arial", '', 10)
    soru_sayisi = sum(int(s["do"]) + int(s["ya"]) for s in data["sorular"])
    pdf.cell(190, 10, f"Toplam Cozulen Soru Sayisi: {soru_sayisi}", ln=True)
    
    # Deneme Özeti
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Son Deneme Netleri", ln=True)
    pdf.set_font("Arial", '', 10)
    for d in data["denemeler"][-3:]: # Son 3 deneme
        pdf.cell(190, 8, f"Tarih: {d['t']} - Yayini: {d['y']} - Toplam Net: {d['top']}", ln=True)
        
    return pdf.output()

# --- OTURUM VE GİRİŞ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🏆 LGS Master Koçluk Sistemi")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
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
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        u_v = db["users"][st.session_state.user]
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Soru Girişi", "📊 Denemeler", "📚 Kitaplarım", "📈 Gelişimim"])
        
        with tab1:
            t = st.date_input("Tarih", datetime.date.today(), key="st")
            drs = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key="sd")
            kn = st.selectbox("Konu", DERSLER_KONULAR[drs], key="sk")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0); ya = c2.number_input("Y", 0); bo = c3.number_input("B", 0)
            if st.button("Kaydet"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")

        with tab2:
            st.subheader("Deneme Analizi")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key="dt")
            yay = st.text_input("Yayın Adı")
            deneme_sonuc = {}; toplam_net = 0
            for d in DERSLER_KONULAR.keys():
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                dd = col1.number_input("D", 0, key=f"{d}d")
                dy = col2.number_input("Y", 0, key=f"{d}y")
                db_ = col3.number_input("B", 0, key=f"{d}b")
                dnet = round(dd - (dy / 3), 2)
                toplam_net += dnet
                deneme_sonuc[d] = {"d": dd, "y": dy, "b": db_, "net": dnet}
            st.metric("Toplam Net", round(toplam_net, 2))
            if st.button("Denemeyi Kaydet"):
                u_v["denemeler"].append({"t": str(dt), "y": yay, "detay": deneme_sonuc, "top": round(toplam_net, 2)})
                veri_kaydet(db); st.success("Deneme eklendi!")

        with tab3:
            st.subheader("Kitap Okuma Takibi")
            k_ad = st.text_input("Kitap Adı")
            k_yz = st.text_input("Yazar")
            k_sy = st.number_input("Sayfa Sayısı", 0)
            c1, c2 = st.columns(2)
            bas_t = c1.date_input("Başlama Tarihi", datetime.date.today())
            bit_t = c2.date_input("Bitiş Tarihi", datetime.date.today())
            if st.button("Kitabı Kaydet"):
                u_v["kitaplar"].append({"ad": k_ad, "yz": k_yz, "s": k_sy, "b": str(bas_t), "bit": str(bit_t)})
                veri_kaydet(db); st.success("Kitap eklendi!")

        with tab4:
            st.subheader("Gelişim Grafiklerim")
            if u_v["denemeler"]:
                df = pd.DataFrame(u_v["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Net Gelişimi"))

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Menü", ["Öğrenci Kayıt", "Veri Girişleri", "Kaynak Takibi", "Raporlar"])
        
        if menu == "Öğrenci Kayıt":
            nu = st.text_input("Öğrenci Adı"); np = st.text_input("Şifre")
            if st.button("Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci tanımlandı.")

        elif menu == "Kaynak Takibi":
            st.header("📚 Öğrenci Kaynak Hazırlama")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            drs_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[drs_k])
            kay_ad = st.text_input("Kaynak Kitap Adı")
            if st.button("Kaynağı Tanımla"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success(f"{sec_o} için kaynak eklendi.")

        elif menu == "Raporlar":
            sec_r = st.selectbox("Raporlanacak Öğrenci", list(db["users"].keys()))
            if sec_r:
                vr = db["users"][sec_r]
                st.subheader(f"📊 {sec_r} Özeti")
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Okunan Kitap", len(vr["kitaplar"]))
                col3.metric("Deneme Sayısı", len(vr["denemeler"]))
                
                # PDF İNDİRME BUTONU
                pdf_data = create_pdf(sec_r, vr)
                st.download_button(label="📄 Profesyonel PDF Raporu İndir", 
                                   data=pdf_data, 
                                   file_name=f"{sec_r}_LGS_Raporu.pdf", 
                                   mime="application/pdf")
