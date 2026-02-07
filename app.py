import streamlit as st
import pandas as pd
import json
import os
import datetime

# --- VERİ YÖNETİMİ ---
DB_FILE = "lgs_master_v5.json"

def veri_yukle():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {"users": {}, "admin_sifre": "admin123", "kaynaklar": []}

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

db = veri_yukle()

# --- OTURUM YÖNETİMİ ---
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# --- GİRİŞ EKRANI ---
if st.session_state.user is None:
    st.title("🚀 LGS Master Koçluk Sistemi")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Öğrenci Girişi"):
            if u in db["users"] and db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"
                st.rerun()
            else: st.error("Hatalı bilgiler!")

    with t2:
        ap = st.text_input("Öğretmen Şifresi", type="password", key="adm_p")
        if st.button("Yönetici Girişi"):
            if ap == db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"
                st.rerun()
            else: st.error("Geçersiz Şifre!")

# --- ANA SİSTEM ---
else:
    st.sidebar.title(f"👤 {st.session_state.user}")
    if st.sidebar.button("Güvenli Çıkış"):
        st.session_state.user = None; st.rerun()

    dersler = ["Türkçe", "Matematik", "Fen", "İnkılap", "Din", "İngilizce"]

    # --- ORTAK FONKSİYONLAR (SORU, DENEME, KİTAP GİRİŞİ) ---
    def veri_giris_formu(user_target):
        m = st.tabs(["📝 Soru Girişi", "📊 Deneme Sınavı", "📚 Kitap Okuma"])
        u_data = db["users"][user_target]

        with m[0]:
            st.subheader("Günlük Soru Takibi")
            t = st.date_input("Soru Çözüm Tarihi", datetime.date.today(), key=f"t_{user_target}")
            drs = st.selectbox("Ders", dersler, key=f"d_{user_target}")
            kn = st.text_input("Konu", key=f"k_{user_target}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{user_target}")
            ya = c2.number_input("Y", 0, key=f"ya_{user_target}")
            bo = c3.number_input("B", 0, key=f"bo_{user_target}")
            if st.button("Soru Kaydet", key=f"btn_s_{user_target}"):
                u_data["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Soru Kaydedildi!")

        with m[1]:
            st.subheader("Deneme Analizi (Ders Bazlı Net)")
            dt = st.date_input("Deneme Tarihi", datetime.date.today(), key=f"dt_{user_target}")
            yay = st.text_input("Yayın Adı", key=f"yay_{user_target}")
            st.write("---")
            deneme_verisi = {}; toplam_net = 0
            for d in dersler:
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                d_do = col1.number_input("D", 0, key=f"{d}d_{user_target}")
                d_ya = col2.number_input("Y", 0, key=f"{d}y_{user_target}")
                d_bo = col3.number_input("B", 0, key=f"{d}b_{user_target}")
                # Net: 3 Yanlış 1 Doğruyu Götürür
                d_net = round(d_do - (d_ya / 3), 2)
                toplam_net += d_net
                deneme_verisi[d] = {"d": d_do, "y": d_ya, "b": d_bo, "net": d_net}
            
            st.divider()
            st.metric("Toplam Net", round(toplam_net, 2))
            if st.button("Denemeyi Kaydet", key=f"btn_d_{user_target}"):
                u_data["denemeler"].append({"t": str(dt), "y": yay, "detay": deneme_verisi, "toplam": round(toplam_net, 2)})
                veri_kaydet(db); st.success("Deneme Analizi Kaydedildi!")

        with m[2]:
            st.subheader("Kitap Takibi")
            kad = st.text_input("Kitap Adı", key=f"ka_{user_target}")
            sy = st.number_input("Sayfa Sayısı", 0, key=f"sy_{user_target}")
            bt = st.date_input("Başlangıç", datetime.date.today(), key=f"bt_{user_target}")
            bitt = st.date_input("Bitiş", datetime.date.today(), key=f"bitt_{user_target}")
            if st.button("Kitabı Kaydet", key=f"btn_k_{user_target}"):
                u_data["kitaplar"].append({"ad": kad, "s": sy, "b": str(bt), "bit": str(bitt)})
                veri_kaydet(db); st.success("Kitap Eklendi!")

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        veri_giris_formu(st.session_state.user)

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Yönetim", ["Öğrenci Kaydı", "Öğrenci Girişleri", "Konu & Kaynak Yönetimi", "Analiz & Rapor"])

        if menu == "Öğrenci Kaydı":
            st.header("👤 Yeni Öğrenci Tanımla")
            nu = st.text_input("Kullanıcı Adı")
            np = st.text_input("Şifre")
            if st.button("Öğrenciyi Kaydet"):
                if nu not in db["users"]:
                    db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "hedefler": [], "kaynaklar": []}
                    veri_kaydet(db); st.success(f"{nu} başarıyla kaydedildi.")
                else: st.warning("Bu kullanıcı zaten var.")

        elif menu == "Öğrenci Girişleri":
            st.header("✍️ Öğrenci Adına Veri Girişi")
            secilen = st.selectbox("Öğrenci Seç", list(db["users"].keys()))
            if secilen:
                veri_giris_formu(secilen)

        elif menu == "Konu & Kaynak Yönetimi":
            st.header("📚 Konu & Kaynak Takibi")
            st.info("Bu bölüm sadece öğretmen kontrolündedir.")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()), key="src_o")
            k_ad = st.text_input("Kaynak Kitap Adı")
            k_durum = st.select_slider("Tamamlanma Oranı %", options=[0, 25, 50, 75, 100])
            if st.button("Kaynağı Güncelle"):
                db["users"][sec_o]["kaynaklar"].append({"k": k_ad, "p": k_durum, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak takibi güncellendi.")

        elif menu == "Analiz & Rapor":
            st.header("📊 Detaylı Analizler")
            st.write("Buradan tüm öğrencilerin verilerini pırıl pırıl (kodsuz) görebilirsiniz.")
            for ad, v in db["users"].items():
                with st.expander(f"{ad.upper()} Raporu"):
                    if v["denemeler"]:
                        df = pd.DataFrame(v["denemeler"])
                        st.line_chart(df.set_index("t")["toplam"])
                    else: st.write("Henüz deneme verisi yok.")
