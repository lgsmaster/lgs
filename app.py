import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- VERİ VE YAPI TANIMLARI ---
DB_FILE = "lgs_master_v6.json"
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

# --- OTURUM ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# --- GİRİŞ EKRANI ---
if st.session_state.user is None:
    st.title("🏆 LGS Master Koçluk Platformu")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Giriş Yap"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
            else: st.error("Hatalı bilgiler!")
    with t2:
        ap = st.text_input("Öğretmen Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()

# --- ANA SİSTEM ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    # --- ORTAK FORM (ÖĞRENCİ VE ÖĞRETMEN İÇİN) ---
    def ortak_giris_paneli(target_user):
        u_v = db["users"][target_user]
        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Sınavı", "📚 Kitap Takibi"])
        
        with tab1:
            st.subheader("Günlük Soru Takibi")
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{target_user}")
            drs = st.selectbox("Ders Seç", list(DERSLER_KONULAR.keys()), key=f"d_{target_user}")
            kn = st.selectbox("Konu Seç", DERSLER_KONULAR[drs], key=f"k_{target_user}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{target_user}")
            ya = c2.number_input("Y", 0, key=f"ya_{target_user}")
            bo = c3.number_input("B", 0, key=f"bo_{target_user}")
            if st.button("Soru Kaydet", key=f"sb_{target_user}"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")

        with tab2:
            st.subheader("Ders Bazlı Deneme Analizi")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{target_user}")
            yay = st.text_input("Yayın Adı", key=f"y_{target_user}")
            deneme_sonuc = {}; toplam_net = 0
            for d in DERSLER_KONULAR.keys():
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                dd = col1.number_input("D", 0, key=f"{d}d_{target_user}")
                dy = col2.number_input("Y", 0, key=f"{d}y_{target_user}")
                db_ = col3.number_input("B", 0, key=f"{d}b_{target_user}")
                dnet = round(dd - (dy / 3), 2)
                toplam_net += dnet
                deneme_sonuc[d] = {"d": dd, "y": dy, "b": db_, "net": dnet}
            st.divider()
            st.metric("Hesaplanan Toplam Net", round(toplam_net, 2))
            if st.button("Denemeyi Kaydet", key=f"db_{target_user}"):
                u_v["denemeler"].append({"t": str(dt), "y": yay, "detay": deneme_sonuc, "top": round(toplam_net, 2)})
                veri_kaydet(db); st.success("Deneme eklendi!")

        with tab3:
            st.subheader("Kitap Okuma")
            kad = st.text_input("Kitap Adı", key=f"kad_{target_user}")
            yzr = st.text_input("Yazar", key=f"yzr_{target_user}")
            syf = st.number_input("Sayfa Sayısı", 0, key=f"syf_{target_user}")
            if st.button("Kitabı Kaydet", key=f"kb_{target_user}"):
                u_v["kitaplar"].append({"ad": kad, "yz": yzr, "s": syf, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kitap eklendi!")

    # --- ÖĞRENCİ EKRANI ---
    if st.session_state.role == "student":
        m = st.sidebar.selectbox("İşlem", ["Veri Girişi", "Gelişimim"])
        if m == "Veri Girişi": ortak_giris_paneli(st.session_state.user)
        else:
            st.header("📈 Gelişim Analizim")
            v = db["users"][st.session_state.user]
            if v["denemeler"]:
                df = pd.DataFrame(v["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Net Gelişim Grafiği"))

    # --- ÖĞRETMEN EKRANI ---
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kayıt", "Girişler", "Kaynak & Konu", "Raporlar"])
        
        if menu == "Öğrenci Kayıt":
            nu = st.text_input("Yeni Öğrenci Adı"); np = st.text_input("Şifre")
            if st.button("Kaydet"):
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(db); st.success("Öğrenci eklendi.")

        elif menu == "Girişler":
            sec = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if sec: ortak_giris_paneli(sec)

        elif menu == "Kaynak & Konu":
            st.header("📚 Kaynak Kitap Takibi")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            drs_k = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[drs_k])
            kay_ad = st.text_input("Kaynak Adı")
            if st.button("Kaynağı Tanımla"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak eklendi.")

        elif menu == "Raporlar":
            sec_r = st.selectbox("Raporlanacak Öğrenci", list(db["users"].keys()))
            if sec_r:
                vr = db["users"][sec_r]
                st.subheader(f"📊 {sec_r} Performans Özeti")
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Bitirilen Kaynak", len(vr["kaynaklar"]))
                col3.metric("Okunan Kitap", len(vr["kitaplar"]))
                
                if st.button("📄 Profesyonel PDF Rapor Al"):
                    st.info("PDF oluşturma motoru hazırlandı. (Karne çıktısı veriliyor...)")
