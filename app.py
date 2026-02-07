import streamlit as st
import pandas as pd
import json
import os
import datetime

# --- VERİ YÖNETİMİ ---
DB_FILE = "lgs_master_v4.json"

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
    st.title("🚀 LGS Master Web Pro")
    t1, t2, t3 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi", "Yeni Kayıt"])
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_login")
        p = st.text_input("Şifre", type="password", key="p_login")
        if st.button("Giriş Yap"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
            else: st.error("Hatalı bilgiler!")

    with t2:
        ap = st.text_input("Öğretmen Şifresi", type="password", key="admin_p")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
            else: st.error("Şifre Yanlış!")

    with t3:
        nu = st.text_input("Yeni Kullanıcı Adı")
        np = st.text_input("Şifre Belirle", type="password")
        if st.button("Kayıt Ol"):
            if nu and np and nu not in db["users"]:
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "odevler": []}
                veri_kaydet(db); st.success("Kayıt Başarılı!")

# --- SİSTEM İÇERİĞİ ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    if st.session_state.role == "student":
        u_data = db["users"][st.session_state.user]
        m = st.sidebar.radio("Menü", ["Soru Girişi", "Deneme Sınavı", "Kitap Okuma", "Gelişim & Ödev"])

        if m == "Soru Girişi":
            st.header("📝 Günlük Soru Takibi")
            drs = st.selectbox("Ders", ["Matematik", "Türkçe", "Fen", "İnkılap", "İngilizce", "Din"])
            kn = st.text_input("Konu Adı")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("Doğru", 0); ya = c2.number_input("Yanlış", 0); bo = c3.number_input("Boş", 0)
            if st.button("Kaydet"):
                u_data["sorular"].append({"t": str(datetime.date.today()), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Soru Kaydedildi!")

        elif m == "Deneme Sınavı":
            st.header("📊 Deneme Sonuç Girişi")
            yay = st.text_input("Yayın Adı")
            st.write("---")
            deneme_verisi = {}
            toplam_net = 0
            
            dersler = ["Türkçe", "Matematik", "Fen", "İnkılap", "Din", "İngilizce"]
            for d in dersler:
                st.write(f"**{d}**")
                c1, c2 = st.columns(2)
                d_do = c1.number_input(f"{d} Doğru", 0, key=f"{d}d")
                d_ya = c2.number_input(f"{d} Yanlış", 0, key=f"{d}y")
                d_net = d_do - (d_ya / 3)
                toplam_net += d_net
                deneme_verisi[d] = {"d": d_do, "y": d_ya, "net": round(d_net, 2)}
            
            st.metric("Toplam Hesaplanan Net", round(toplam_net, 2))
            if st.button("Tüm Denemeyi Kaydet"):
                u_data["denemeler"].append({"t": str(datetime.date.today()), "y": yay, "detay": deneme_verisi, "toplam": round(toplam_net, 2)})
                veri_kaydet(db); st.success("Deneme Başarıyla Kaydedildi!")

        elif m == "Kitap Okuma":
            st.header("📚 Kitap Takibi")
            kad = st.text_input("Kitap Adı"); yz = st.text_input("Yazar"); sy = st.number_input("Sayfa Sayısı", 0)
            bt = st.date_input("Başlangıç"); bitt = st.date_input("Bitiş")
            if st.button("Kitabı Ekle"):
                u_data["kitaplar"].append({"ad": kad, "yz": yz, "s": sy, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(db); st.success("Kitap Kaydedildi!")

    elif st.session_state.role == "teacher":
        st.header("👨‍🏫 Öğretmen Paneli")
        # Tüm öğrencileri listele ve takip et
        ogrenciler = list(db["users"].keys())
        secilen = st.selectbox("Öğrenci Seçin", ogrenciler)
        if secilen:
            st.subheader(f"{secilen} Performansı")
            # Burada ödev verme ve analiz kısımları yer alacak
            odev = st.text_area("Ödev/Hedef Belirle")
            if st.button("Gönder"):
                db["users"][secilen]["odevler"].append(odev)
                veri_kaydet(db); st.success("Ödev Gönderildi!")
