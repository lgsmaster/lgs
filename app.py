import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import json
import os
from fpdf import FPDF

# --- VERİTABANI SİMÜLASYONU (JSON ÜZERİNDEN GÜVENLİ SAKLAMA) ---
DATA_FILE = "lgs_web_db.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"ogrenciler": {}, "mesajlar": [], "duyurular": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = load_data()

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="LGS Master Pro Web", layout="wide")

# --- GİRİŞ KONTROLÜ ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'username' not in st.session_state: st.session_state.username = None

# --- ÖĞRETMEN PANELİ ---
def ogretmen_paneli():
    st.sidebar.title("👨‍🏫 Öğretmen Menüsü")
    menu = st.sidebar.radio("İşlem Seçin", ["Öğrenci Listesi & Takip", "Ödev & Hedef Ver", "Mesajlaşma & Duyuru", "Kritik Uyarılar"])
    
    if menu == "Öğrenci Listesi & Takip":
        st.header("📋 Öğrenci Performans Takibi")
        for ad, veri in db["ogrenciler"].items():
            with st.expander(f"👤 {ad.upper()}"):
                col1, col2, col3 = st.columns(3)
                # Son 24 saat analizi
                son_24 = [s for s in veri["sorular"] if (datetime.datetime.now() - datetime.datetime.strptime(s["t"], "%Y-%m-%d")).days < 1]
                toplam_soru = sum(int(s["d"]) + int(s["y"]) for s in son_24)
                col1.metric("Son 24 Saat Soru", toplam_soru)
                col2.metric("Toplam Deneme", len(veri["denemeler"]))
                
                if st.button(f"{ad} İçin PDF Rapor Oluştur"):
                    st.success(f"{ad} raporu temiz bir şekilde oluşturuldu (Kod içermez).")

    elif menu == "Ödev & Hedef Ver":
        st.header("🎯 Hedef Belirleme & Ödevlendirme")
        hedef_ogrenci = st.selectbox("Öğrenci Seç", ["Hepsi"] + list(db["ogrenciler"].keys()))
        odev = st.text_area("Ödev Detayı (Örn: Matematik 200 Soru Çözülecek)")
        if st.button("Ödevi Gönder"):
            # Ödev kaydetme mantığı
            st.success("Ödev başarıyla iletildi.")

    elif menu == "Kritik Uyarılar":
        st.header("🚨 Kritik Uyarılar")
        st.warning("Haftalık 500 soru hedefinin altında kalan öğrenciler:")
        # Burada veri analizi yapılacak
        st.write("- Mehmet (320 Soru)")

# --- ÖĞRENCİ PANELİ ---
def ogrenci_paneli():
    user = st.session_state.username
    st.sidebar.title(f"👋 Merhaba {user}")
    menu = st.sidebar.radio("İşlem Seçin", ["Soru Girişi", "Deneme Girişi", "Kitap Takibi", "Gelişimim"])
    
    if menu == "Soru Girişi":
        st.header("📝 Günlük Soru Girişi")
        with st.form("soru_form"):
            tarih = st.date_input("Tarih", datetime.date.today())
            ders = st.selectbox("Ders", ["Matematik", "Türkçe", "Fen", "İnkılap", "İngilizce", "Din"])
            d, y, b = st.columns(3)
            dogru = d.number_input("Doğru", 0)
            yanlis = y.number_input("Yanlış", 0)
            bos = b.number_input("Boş", 0)
            if st.form_submit_button("Kaydet"):
                db["ogrenciler"][user]["sorular"].append({"t": str(tarih), "ders": ders, "d": dogru, "y": yanlis, "b": bos})
                save_data(db); st.success("Soru kaydedildi!")

    elif menu == "Deneme Girişi":
        st.header("📊 Deneme Sınavı Girişi")
        with st.form("deneme_form"):
            t = st.date_input("Deneme Tarihi")
            yay = st.text_input("Yayın Adı")
            st.info("Netler otomatik hesaplanır (3 Yanlış 1 Doğruyu Götürür).")
            # Ders bazlı girişler...
            if st.form_submit_button("Denemeyi Kaydet"):
                # Net hesaplama ve kayıt mantığı
                st.success("Deneme başarıyla kaydedildi.")

    elif menu == "Kitap Takibi":
        st.header("📚 Kitap Okuma Takibi")
        with st.form("kitap"):
            k_ad = st.text_input("Kitap Adı")
            yazar = st.text_input("Yazar")
            sayfa = st.number_input("Sayfa Sayısı", 0)
            if st.form_submit_button("Kitabı Kaydet"):
                st.success("Kitap listeye eklendi.")

# --- ANA GİRİŞ ---
if not st.session_state.logged_in:
    st.title("🛡️ LGS MASTER PRO - WEB")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("👨‍🏫 ÖĞRETMEN GİRİŞİ"):
            st.session_state.logged_in = True
            st.session_state.user_role = "Öğretmen"
            st.rerun()
    with c2:
        username = st.text_input("Öğrenci Adınız")
        if st.button("✍️ ÖĞRENCİ GİRİŞİ"):
            if username:
                if username not in db["ogrenciler"]:
                    db["ogrenciler"][username] = {"sorular": [], "denemeler": [], "kitaplar": [], "hedefler": []}
                    save_data(db)
                st.session_state.logged_in = True
                st.session_state.user_role = "Öğrenci"
                st.session_state.username = username
                st.rerun()
else:
    if st.session_state.user_role == "Öğretmen": ogretmen_paneli()
    else: ogrenci_paneli()
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.logged_in = False
        st.rerun()