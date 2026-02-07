import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- SİSTEM AYARLARI ---
DB_FILE = "lgs_ultra_db.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30) # LGS 2026 Tahmini Tarih
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

# --- PDF MOTORU (Türkçe Karakter Destekli Taslak) ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, f"LGS PERFORMANS RAPORU: {user_name.upper()}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "1. Genel Istatistikler", ln=True)
    pdf.set_font("Helvetica", '', 11)
    sq = sum(int(s["do"]) + int(s["ya"]) for s in user_data["sorular"])
    pdf.cell(190, 8, f"- Toplam Soru Cozumu: {sq}", ln=True)
    pdf.cell(190, 8, f"- Kayitli Deneme Sayisi: {len(user_data['denemeler'])}", ln=True)
    pdf.cell(190, 8, f"- Okunan Kitap Sayisi: {len(user_data['kitaplar'])}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "2. Son Deneme Netleri", ln=True)
    pdf.set_font("Helvetica", '', 10)
    for d in user_data["denemeler"][-3:]:
        pdf.cell(190, 8, f"- Tarih: {d['t']} | Yayini: {d['y']} | Toplam Net: {d['top']}", ln=True)
    
    return bytes(pdf.output())

# --- OTURUM ---
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
    # --- GERİ SAYIM SAYACI (Sidebar) ---
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"""
    <div style="background-color:#ff4b4b; padding:10px; border-radius:10px; text-align:center; color:white;">
        <h3 style="margin:0;">⏳ LGS'ye Kalan</h3>
        <p style="font-size:20px; font-weight:bold; margin:0;">{kalan.days} Gün {kalan.seconds // 3600} Saat</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    # --- VERİ GİRİŞ FORMU ---
    def data_form(target_user):
        u_v = db["users"][target_user]
        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Sınavı", "📚 Kitap Takibi"])
        
        with tab1:
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{target_user}")
            drs = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{target_user}")
            kn = st.selectbox("Konu", DERSLER_KONULAR[drs], key=f"k_{target_user}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{target_user}")
            ya = c2.number_input("Y", 0, key=f"ya_{target_user}")
            bo = c3.number_input("B", 0, key=f"bo_{target_user}")
            if st.button("Soru Kaydet", key=f"sb_{target_user}"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")

        with tab2:
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{target_user}")
            yay = st.text_input("Yayın Adı", key=f"y_{target_user}")
            res = {}; t_net = 0
            for d in DERSLER_KONULAR.keys():
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                dd = col1.number_input("D", 0, key=f"{d}d_{target_user}")
                dy = col2.number_input("Y", 0, key=f"{d}y_{target_user}")
                db_ = col3.number_input("B", 0, key=f"{d}b_{target_user}")
                net = round(dd - (dy / 3), 2)
                t_net += net
                res[d] = {"d": dd, "y": dy, "b": db_, "net": net}
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{target_user}"):
                u_v["denemeler"].append({"t": str(dt), "y": yay, "detay": res, "top": round(t_net, 2)})
                veri_kaydet(db); st.success("Deneme eklendi!")

        with tab3:
            kad = st.text_input("Kitap Adı", key=f"ka_{target_user}")
            yzr = st.text_input("Yazar", key=f"yz_{target_user}")
            syf = st.number_input("Sayfa Sayısı", 0, key=f"sy_{target_user}")
            c1, c2 = st.columns(2)
            bt = c1.date_input("Baslama Tarihi", key=f"bt_{target_user}")
            bitt = c2.date_input("Bitis Tarihi", key=f"bitt_{target_user}")
            if st.button("Kitabı Kaydet", key=f"kb_{target_user}"):
                u_v["kitaplar"].append({"ad": kad, "yz": yzr, "s": syf, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(db); st.success("Kitap eklendi!")

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        m = st.sidebar.selectbox("Menü", ["Veri Girişi", "Gelişimim"])
        if m == "Veri Girişi": data_form(st.session_state.user)
        else:
            v = db["users"][st.session_state.user]
            if v["denemeler"]:
                st.plotly_chart(px.line(pd.DataFrame(v["denemeler"]), x="t", y="top", title="Net Gelişimi"))

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kayıt", "Veri Girişleri", "Kaynak Hazırlama", "Rapor & PDF"])
        
        if menu == "Öğrenci Kayıt":
            nu = st.text_input("Yeni Öğrenci Adı"); np = st.text_input("Şifre")
            if st.button("Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci eklendi.")

        elif menu == "Veri Girişleri":
            sec = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec: data_form(sec)

        elif menu == "Kaynak Hazırlama":
            st.header("📚 Kaynak Hazırlama (Ders-Konu-Kaynak)")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            drs_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[drs_k])
            kay_ad = st.text_input("Kaynak Kitap Adı")
            if st.button("Kaynağı Tanımla"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak öğrenciye başarıyla atandı.")

        elif menu == "Rapor & PDF":
            sec_r = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec_r:
                vr = db["users"][sec_r]
                st.subheader(f"📊 {sec_r} Özeti")
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Kaynak", len(vr["kaynaklar"]))
                col3.metric("Kitap", len(vr["kitaplar"]))
                
                pdf_output = generate_pdf_bytes(sec_r, vr)
                st.download_button(label="📄 Profesyonel PDF Karne İndir", 
                                   data=pdf_output, 
                                   file_name=f"{sec_r}_LGS_Analiz.pdf", 
                                   mime="application/pdf")
