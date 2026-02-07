import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- SİSTEM AYARLARI VE VERİ ---
DB_FILE = "lgs_final_db.json"
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

# --- PDF OLUŞTURMA MOTORU (GÜNCELLENDİ) ---
def generate_pdf(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, f"LGS PERFORMANS KARNESI: {user_name.upper()}", ln=True, align='C')
    
    # Soru İstatistikleri
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "1. Soru Cozum Verileri", ln=True)
    pdf.set_font("Helvetica", '', 10)
    total_q = sum(int(s["do"]) + int(s["ya"]) for s in user_data["sorular"])
    pdf.cell(190, 8, f"Toplam Cozulen Soru: {total_q}", ln=True)
    
    # Deneme Verileri
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "2. Deneme Net Analizleri", ln=True)
    pdf.set_font("Helvetica", '', 10)
    for d in user_data["denemeler"][-5:]:
        pdf.cell(190, 8, f"Tarih: {d['t']} | Yayini: {d['y']} | Toplam Net: {d['top']}", ln=True)
    
    # Kitap Verileri
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "3. Okunan Kitaplar", ln=True)
    pdf.set_font("Helvetica", '', 10)
    for k in user_data["kitaplar"]:
        pdf.cell(190, 8, f"{k['ad']} - {k['yz']} ({k['s']} sayfa)", ln=True)
        
    return pdf.output().encode('latin-1', 'replace')

# --- OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🏆 LGS Master Koçluk Sistemi")
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
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    # --- ORTAK VERİ GİRİŞ MODÜLÜ ---
    def render_data_entry(target_user):
        u_v = db["users"][target_user]
        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Girişi", "📚 Kitap Takibi"])
        
        with tab1:
            st.subheader("Günlük Soru Takibi")
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{target_user}")
            drs = st.selectbox("Ders Seç", list(DERSLER_KONULAR.keys()), key=f"d_{target_user}")
            kn = st.selectbox("Konu Seç", DERSLER_KONULAR[drs], key=f"k_{target_user}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{target_user}")
            ya = c2.number_input("Y", 0, key=f"ya_{target_user}")
            bo = c3.number_input("B", 0, key=f"bo_{target_user}")
            if st.button("Kaydet", key=f"s_btn_{target_user}"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Veri Kaydedildi!")

        with tab2:
            st.subheader("Ders Bazlı Deneme Girişi")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{target_user}")
            yay = st.text_input("Yayın Adı", key=f"y_{target_user}")
            deneme_res = {}; t_net = 0
            for d in DERSLER_KONULAR.keys():
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                dd = col1.number_input("D", 0, key=f"{d}d_{target_user}")
                dy = col2.number_input("Y", 0, key=f"{d}y_{target_user}")
                db_ = col3.number_input("B", 0, key=f"{d}b_{target_user}")
                net = round(dd - (dy / 3), 2)
                t_net += net
                deneme_res[d] = {"d": dd, "y": dy, "b": db_, "net": net}
            st.divider()
            st.metric("Hesaplanan Toplam Net", round(t_net, 2))
            if st.button("Denemeyi Kaydet", key=f"d_btn_{target_user}"):
                u_v["denemeler"].append({"t": str(dt), "y": yay, "detay": deneme_res, "top": round(t_net, 2)})
                veri_kaydet(db); st.success("Deneme eklendi!")

        with tab3:
            st.subheader("Kitap Okuma")
            kad = st.text_input("Kitap Adı", key=f"kad_{target_user}")
            yzr = st.text_input("Yazar", key=f"yzr_{target_user}")
            syf = st.number_input("Sayfa Sayısı", 0, key=f"syf_{target_user}")
            c1, c2 = st.columns(2)
            bt = c1.date_input("Baslama Tarihi", key=f"bt_{target_user}")
            bitt = c2.date_input("Bitis Tarihi", key=f"bitt_{target_user}")
            if st.button("Kitabı Kaydet", key=f"k_btn_{target_user}"):
                u_v["kitaplar"].append({"ad": kad, "yz": yzr, "s": syf, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(db); st.success("Kitap eklendi!")

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        m = st.sidebar.selectbox("Menü", ["Veri Girişi", "Gelişim Analizim"])
        if m == "Veri Girişi": render_data_entry(st.session_state.user)
        else:
            st.header("📈 Gelişim Grafiklerim")
            v = db["users"][st.session_state.user]
            if v["denemeler"]:
                df = pd.DataFrame(v["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Net Gelişimi"))

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kayıt", "Veri Girişleri", "Kaynak Hazırlama", "Raporlar & Analiz"])
        
        if menu == "Öğrenci Kayıt":
            nu = st.text_input("Yeni Öğrenci Adı"); np = st.text_input("Şifre")
            if st.button("Öğrenciyi Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci başarıyla eklendi.")

        elif menu == "Veri Girişleri":
            sec = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec: render_data_entry(sec)

        elif menu == "Kaynak Hazırlama":
            st.header("📚 Kaynak Takibi")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            drs_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[drs_k])
            kay_ad = st.text_input("Kaynak Kitap Adı")
            if st.button("Kaynağı Tanımla"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak başarıyla eklendi.")

        elif menu == "Raporlar & Analiz":
            sec_r = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec_r:
                vr = db["users"][sec_r]
                st.subheader(f"📊 {sec_r} Genel Durumu")
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Okunan Kitap", len(vr["kitaplar"]))
                col3.metric("Kaynak Sayısı", len(vr["kaynaklar"]))
                
                pdf_bytes = generate_pdf(sec_r, vr)
                st.download_button(label="📄 Profesyonel PDF Raporu İndir", 
                                   data=pdf_bytes, 
                                   file_name=f"{sec_r}_Rapor.pdf", 
                                   mime="application/pdf")
