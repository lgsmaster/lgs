import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px

# --- VERİ YÖNETİMİ ---
DB_FILE = "lgs_master_v3.json"

def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = veri_yukle()

# --- OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# --- GİRİŞ EKRANI ---
if st.session_state.user is None:
    st.title("🛡️ LGS Master Pro - Güvenli Giriş")
    t1, t2, t3 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi", "Yeni Kayıt"])
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u1")
        p = st.text_input("Şifre", type="password", key="p1")
        if st.button("Giriş Yap", key="b1"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
            else: st.error("Kullanıcı adı veya şifre hatalı!")

    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password", key="p2")
        if st.button("Yönetici Girişi", key="b2"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
            else: st.error("Yetkisiz şifre!")

    with t3:
        nu = st.text_input("Kullanıcı Adı Belirle", key="u3")
        np = st.text_input("Şifre Belirle", type="password", key="p3")
        if st.button("Kayıt Ol", key="b3"):
            if nu and np and nu not in db["users"]:
                db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "odevler": []}
                veri_kaydet(db); st.success("Kaydınız oluşturuldu! Giriş yapabilirsiniz.")

# --- SİSTEM İÇERİĞİ ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        u_data = db["users"][st.session_state.user]
        menu = st.sidebar.selectbox("İşlem Menüsü", ["Soru Girişi", "Deneme Takibi", "Kitap Takibi", "Gelişimim & Ödevler"])

        if menu == "Soru Girişi":
            st.header("📝 Günlük Soru Takibi")
            drs = st.selectbox("Ders", ["Matematik", "Türkçe", "Fen Bilimleri", "İnkılap Tarihi", "İngilizce", "Din Kültürü"])
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("Doğru", 0); ya = c2.number_input("Yanlış", 0); bo = c3.number_input("Boş", 0)
            if st.button("Kaydet"):
                u_data["sorular"].append({"t": str(datetime.date.today()), "d": drs, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Soru verisi kaydedildi!")

        elif menu == "Deneme Takibi":
            st.header("📊 Deneme Analizi")
            yay = st.text_input("Yayın/Sınav Adı")
            c1, c2 = st.columns(2)
            d_do = c1.number_input("Toplam Doğru", 0); d_ya = c2.number_input("Toplam Yanlış", 0)
            net = d_do - (d_ya / 3) # 3 Yanlış 1 Doğruyu Götürür
            st.metric("Hesaplanan Net", round(net, 2))
            if st.button("Denemeyi Kaydet"):
                u_data["denemeler"].append({"t": str(datetime.date.today()), "y": yay, "net": round(net, 2)})
                veri_kaydet(db); st.success("Deneme kaydedildi!")

        elif menu == "Kitap Takibi":
            st.header("📚 Kitap Okuma Listesi")
            kad = st.text_input("Kitap Adı"); yzr = st.text_input("Yazar"); syf = st.number_input("Sayfa Sayısı", 0)
            if st.button("Kitabı Listeme Ekle"):
                u_data["kitaplar"].append({"ad": kad, "yzr": yzr, "s": syf, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kitap eklendi!")

        elif menu == "Gelişimim & Ödevler":
            st.header("📈 Gelişim Analizi")
            if u_data["odevler"]:
                st.warning(f"🔔 Öğretmeninden Mesaj/Ödev var: {u_data['odevler'][-1]}")
            
            if u_data["denemeler"]:
                df = pd.DataFrame(u_data["denemeler"])
                fig = px.line(df, x="t", y="net", title="Deneme Net Gelişimi")
                st.plotly_chart(fig)

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        st.header("👨‍🏫 Öğretmen Yönetim Paneli")
        ogrenci_listesi = list(db["users"].keys())
        secilen = st.selectbox("Öğrenci Seçin", ogrenci_listesi)
        
        if secilen:
            o_veri = db["users"][secilen]
            st.subheader(f"🔍 {secilen.upper()} - Analiz")
            
            # Son 24 Saat Aktivitesi
            bugun = str(datetime.date.today())
            bugunku_sorular = sum(s["do"] + s["ya"] for s in o_veri["sorular"] if s["t"] == bugun)
            st.info(f"📅 Bugün çözülen toplam soru: {bugunku_sorular}")
            
            # Ödev/Hedef Belirleme
            hedef = st.text_area("Öğrenciye Ödev/Hedef/Mesaj Yaz")
            if st.button("Ödevi/Mesajı Gönder"):
                o_veri["odevler"].append(hedef)
                veri_kaydet(db); st.success("Ödev başarıyla iletildi!")
            
            # PDF Rapor Butonu (Taslak)
            if st.button("📄 Profesyonel PDF Karne Oluştur"):
                st.download_button("PDF Dosyasını İndir", "Rapor içeriği hazırlanıyor...", "rapor.pdf")
