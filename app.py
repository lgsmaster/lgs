import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF

# --- AYARLAR ---
DB_FILE = "lgs_master_final_v9.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)
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

# --- PDF MOTORU (Tablolu ve Profesyonel) ---
def generate_pdf_bytes(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 10, f"LGS PERFORMANS RAPORU: {user_name.upper()}", ln=True, align='C')
    pdf.ln(5)

    # 1. Özet Bilgiler
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "GENEL OZET", ln=True)
    pdf.set_font("Helvetica", '', 10)
    sq = sum(int(s["do"]) + int(s["ya"]) for s in user_data["sorular"])
    pdf.cell(190, 7, f"- Toplam Cozulen Soru Sayisi: {sq}", ln=True)
    pdf.cell(190, 7, f"- Kayitli Deneme Sayisi: {len(user_data['denemeler'])}", ln=True)
    pdf.cell(190, 7, f"- Kitap Okuma Sayisi: {len(user_data['kitaplar'])}", ln=True)
    pdf.ln(5)

    # 2. Soru Analiz Tablosu
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "BRANS BAZLI SORU DETAYLARI", ln=True)
    
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(25, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(30, 8, "Brans", 1, 0, 'C', True)
    pdf.cell(65, 8, "Konu", 1, 0, 'C', True)
    pdf.cell(12, 8, "D", 1, 0, 'C', True)
    pdf.cell(12, 8, "Y", 1, 0, 'C', True)
    pdf.cell(12, 8, "B", 1, 0, 'C', True)
    pdf.cell(34, 8, "Toplam", 1, 1, 'C', True)

    pdf.set_font("Helvetica", '', 8)
    for s in user_data["sorular"][-25:]: # Son 25 kayıt
        pdf.cell(25, 7, str(s['t']), 1)
        pdf.cell(30, 7, str(s['d']), 1)
        pdf.cell(65, 7, str(s['k'][:30]), 1)
        pdf.cell(12, 7, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 7, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 7, str(s['bo']), 1, 0, 'C')
        total = int(s['do']) + int(s['ya']) + int(s['bo'])
        pdf.cell(34, 7, str(total), 1, 1, 'C')

    return bytes(pdf.output())

# --- GİRİŞ KONTROLÜ ---
if "user" not in st.session_state: st.session_state.user = None

if st.session_state.user is None:
    st.title("🏆 LGS Master Yönetim Paneli")
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
    # Sidebar - Geri Sayım ve Çıkış
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"<h3 style='color:red;'>⏳ LGS'ye {kalan.days} Gün</h3>", unsafe_allow_html=True)
    if st.sidebar.button("Çıkış Yap"):
        st.session_state.user = None; st.rerun()

    # --- TÜM VERİ GİRİŞLERİ (FONKSİYON) ---
    def verileri_yonet(user_key):
        u_v = db["users"][user_key]
        tab1, tab2, tab3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Sınavı", "📚 Kitap Okuma"])
        
        with tab1:
            st.subheader("Günlük Soru Takibi")
            t = st.date_input("Tarih", datetime.date.today(), key=f"t_{user_key}")
            drs = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{user_key}")
            kn = st.selectbox("Konu", DERSLER_KONULAR[drs], key=f"k_{user_key}")
            c1, c2, c3 = st.columns(3)
            do = c1.number_input("D", 0, key=f"do_{user_key}")
            ya = c2.number_input("Y", 0, key=f"ya_{user_key}")
            bo = c3.number_input("B", 0, key=f"bo_{user_key}")
            if st.button("Soru Kaydet", key=f"btn_s_{user_key}"):
                u_v["sorular"].append({"t": str(t), "d": drs, "k": kn, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(db); st.success("Kaydedildi!")

        with tab2:
            st.subheader("Ders Bazlı Deneme Girişi")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{user_key}")
            yay = st.text_input("Yayın Adı", key=f"yay_{user_key}")
            deneme_detay = {}; toplam_net = 0
            for d in DERSLER_KONULAR.keys():
                st.write(f"**{d}**")
                col1, col2, col3 = st.columns(3)
                d_d = col1.number_input("D", 0, key=f"{d}d_{user_key}")
                d_y = col2.number_input("Y", 0, key=f"{d}y_{user_key}")
                d_b = col3.number_input("B", 0, key=f"{d}b_{user_key}")
                d_net = round(d_d - (d_y / 3), 2)
                toplam_net += d_net
                deneme_detay[d] = {"d": d_d, "y": d_y, "b": d_b, "net": d_net}
            st.divider()
            st.metric("Toplam Hesaplanan Net", round(toplam_net, 2))
            if st.button("Denemeyi Kaydet", key=f"btn_d_{user_key}"):
                u_v["denemeler"].append({"t": str(dt), "y": yay, "detay": deneme_detay, "top": round(toplam_net, 2)})
                veri_kaydet(db); st.success("Deneme Analizi Eklendi!")

        with tab3:
            st.subheader("Kitap Okuma Takibi")
            k_ad = st.text_input("Kitap Adı", key=f"kad_{user_key}")
            k_yz = st.text_input("Yazar", key=f"kyz_{user_key}")
            k_sy = st.number_input("Sayfa Sayısı", 0, key=f"ksy_{user_key}")
            col1, col2 = st.columns(2)
            b_t = col1.date_input("Baslama Tarihi", key=f"bt_{user_key}")
            bit_t = col2.date_input("Bitis Tarihi", key=f"bitt_{user_key}")
            if st.button("Kitabı Kaydet", key=f"btn_k_{user_key}"):
                u_v["kitaplar"].append({"ad": k_ad, "yz": k_yz, "s": k_sy, "b": str(b_t), "bit": str(bit_t)})
                veri_kaydet(db); st.success("Kitap Kaydedildi!")

    # --- ROLLER ---
    if st.session_state.role == "student":
        menu = st.sidebar.radio("Menü", ["Veri Girişi", "Gelişimim"])
        if menu == "Veri Girişi":
            verileri_yonet(st.session_state.user)
        else:
            st.header("📈 Net Gelişim Grafiğim")
            if db["users"][st.session_state.user]["denemeler"]:
                df = pd.DataFrame(db["users"][st.session_state.user]["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Deneme Netleri (Toplam)"))

    elif st.session_state.role == "teacher":
        menu = st.sidebar.radio("Öğretmen Menüsü", ["Öğrenci Kaydı", "Öğrenci Veri Girişleri", "Kaynak & Konu Hazırlama", "Raporlar & PDF"])
        
        if menu == "Öğrenci Kaydı":
            st.header("👤 Yeni Öğrenci Tanımla")
            nu = st.text_input("Yeni Öğrenci Kullanıcı Adı")
            np = st.text_input("Şifre Belirle")
            if st.button("Öğrenciyi Kaydet"):
                if nu and np and nu not in db["users"]:
                    db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                    veri_kaydet(db); st.success(f"{nu} başarıyla sisteme eklendi.")

        elif menu == "Öğrenci Veri Girişleri":
            st.header("✍️ Öğrenci Adına Veri Gir")
            sec = st.selectbox("İşlem Yapılacak Öğrenci", list(db["users"].keys()))
            if sec: verileri_yonet(sec)

        elif menu == "Kaynak & Konu Hazırlama":
            st.header("📚 Konu-Kaynak Ataması")
            sec_o = st.selectbox("Öğrenci Seç", list(db["users"].keys()), key="src_o")
            drs_k = st.selectbox("Branş", list(DERSLER_KONULAR.keys()), key="src_d")
            kn_k = st.selectbox("Konu", DERSLER_KONULAR[drs_k], key="src_k")
            kay_ad = st.text_input("Kaynak Kitap Adı", key="src_a")
            if st.button("Kaynağı Öğrenciye Ata"):
                db["users"][sec_o]["kaynaklar"].append({"d": drs_k, "k": kn_k, "ad": kay_ad, "t": str(datetime.date.today())})
                veri_kaydet(db); st.success("Kaynak başarıyla atandı.")

        elif menu == "Raporlar & PDF":
            st.header("📊 Analiz ve PDF Karne")
            sec_r = st.selectbox("Raporlanacak Öğrenci", list(db["users"].keys()), key="rep_o")
            if sec_r:
                vr = db["users"][sec_r]
                col1, col2, col3 = st.columns(3)
                col1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in vr["sorular"]))
                col2.metric("Kaynak", len(vr["kaynaklar"]))
                col3.metric("Deneme", len(vr["denemeler"]))
                
                pdf_bytes = generate_pdf_bytes(sec_r, vr)
                st.download_button(label="📄 Tablolu PDF Raporu İndir", 
                                   data=pdf_bytes, 
                                   file_name=f"{sec_r}_LGS_Analiz.pdf", 
                                   mime="application/pdf")
