import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
from github import Github

# --- 1. SAYFA AYARLARI (EN BAŞTA) ---
st.set_page_config(page_title="LGS Master Pro", page_icon="🏆", layout="wide")

# --- 2. AYARLAR VE SABİTLER ---
DB_FILE = "lgs_platinum_db.json"
LGS_TARIHI = datetime.datetime(2026, 6, 14, 9, 30)

DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri", "Yazim Kurallari"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik", "Cebirsel Ifadeler"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Ya Istiklal Ya Olum"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone"]
}

# --- 3. GITHUB OTOMATİK YEDEKLEME ---
def github_yedekle(data):
    try:
        # Secrets kontrolü
        if "general" in st.secrets:
            token = st.secrets["general"]["GITHUB_TOKEN"]
            repo_name = st.secrets["general"]["REPO_NAME"]
            
            g = Github(token)
            repo = g.get_repo(repo_name)
            
            # Dosya varsa güncelle, yoksa oluştur
            try:
                contents = repo.get_contents(DB_FILE)
                repo.update_file(contents.path, "Oto-Yedek (Streamlit)", json.dumps(data, indent=4), contents.sha)
            except:
                repo.create_file(DB_FILE, "İlk Kurulum", json.dumps(data, indent=4))
            return True
        return False
    except Exception as e:
        print(f"Yedekleme Hatası: {e}")
        return False

# --- 4. VERİ YÖNETİMİ ---
def veri_yukle():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Eksik anahtar kontrolü (Hata önleyici)
            if "users" not in data: data["users"] = {}
            if "admin_sifre" not in data: data["admin_sifre"] = "admin123"
            return data
        except:
            pass
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    # 1. Yerel Kayıt
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state.db = data
    
    # 2. Bulut Yedekleme
    if github_yedekle(data):
        st.toast("☁️ Veriler GitHub'a yedeklendi!", icon="✅")
    else:
        st.toast("💾 Yerel kayıt yapıldı (GitHub ayarı yok).", icon="ℹ️")

# Oturum Başlatma
if "db" not in st.session_state: st.session_state.db = veri_yukle()
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# --- 5. PDF MOTORU (MAVİ BAŞLIKLI) ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf_report(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Mavi Başlık Tasarımı
    pdf.set_fill_color(31, 119, 180) # Lacivert
    pdf.set_text_color(255, 255, 255) # Beyaz yazı
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS STRATEJI VE ANALIZ RAPORU: {user_name.upper()}"), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)
    
    # 1. Deneme Gelişim Analizi
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "1. DENEME SINAVLARI PERFORMANSI", ln=True)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230) # Gri başlıklar
    pdf.cell(35, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(65, 8, "Yayin", 1, 0, 'C', True)
    pdf.cell(45, 8, "Net", 1, 0, 'C', True)
    pdf.cell(45, 8, "Degisim", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 9)
    prev = None
    # Tarihe göre sırala
    sorted_d = sorted(user_data.get("denemeler", []), key=lambda x: x['t'])
    for d in sorted_d:
        degisim = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(35, 7, d['t'], 1, 0, 'C')
        pdf.cell(65, 7, tr_fix(d['y']), 1)
        pdf.cell(45, 7, str(d['top']), 1, 0, 'C')
        pdf.cell(45, 7, str(degisim), 1, 1, 'C')
        prev = d['top']

    # 2. Soru Tablosu
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "2. SON COZULEN SORULAR", ln=True)
    heads = [("Tarih",25), ("Ders",30), ("Konu",65), ("D",12), ("Y",12), ("B",12), ("Top",34)]
    pdf.set_font("Helvetica", 'B', 8)
    for h in heads: pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 7)
    for s in user_data.get("sorular", [])[-20:]:
        pdf.cell(25, 6, s['t'], 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(65, 6, tr_fix(s['k'][:35]), 1)
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(34, 6, str(int(s['do'])+int(s['ya'])+int(s['bo'])), 1, 1, 'C')

    return bytes(pdf.output())

# --- 6. ARAYÜZ VE SİSTEM ---
if st.session_state.user is None:
    st.title("🚀 LGS Master Strateji Portalı")
    t1, t2 = st.tabs(["🔐 Öğrenci Girişi", "👨‍🏫 Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Sisteme Gir"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
            else: st.error("Hatalı Giriş")
    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Girişi"):
            if ap == st.session_state.db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
            else: st.error("Şifre Yanlış")

else:
    # Sidebar
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"""
    <div style="background-color:#d32f2f; color:white; padding:10px; border-radius:5px; text-align:center;">
    <b>⏳ LGS'YE KALAN</b><br><span style="font-size:24px">{kalan.days} GÜN</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.write(f"👤 **{st.session_state.user}**")
    if st.sidebar.button("Güvenli Çıkış"): st.session_state.user = None; st.rerun()

    # Ortak Veri Giriş Formu
    def data_hub(uid):
        uv = st.session_state.db["users"][uid]
        c1, c2, c3 = st.tabs(["📝 Soru Girişi", "📊 Deneme Girişi", "📚 Kitap Takibi"])
        
        with c1:
            tar = st.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = st.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"k_{uid}")
            col1, col2, col3 = st.columns(3)
            do = col1.number_input("D", 0, key=f"do_{uid}")
            ya = col2.number_input("Y", 0, key=f"ya_{uid}")
            bo = col3.number_input("B", 0, key=f"bo_{uid}")
            if st.button("Soru Kaydet", key=f"s_{uid}"):
                uv["sorular"].append({"t": str(tar), "d": dr, "k": ko, "do": do, "ya": ya, "bo": bo})
                veri_kaydet(st.session_state.db)

        with c2:
            yay = st.text_input("Yayın Adı", key=f"y_{uid}")
            dt = st.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            t_net = 0
            d_detay = {}
            for ds in DERSLER_KONULAR.keys():
                with st.expander(ds):
                    x1, x2 = st.columns(2)
                    d_d = x1.number_input(f"{ds} D", 0, key=f"{ds}d_{uid}")
                    d_y = x2.number_input(f"{ds} Y", 0, key=f"{ds}y_{uid}")
                    n = round(d_d - (d_y * 0.33), 2)
                    t_net += n
                    d_detay[ds] = {"d":d_d, "y":d_y, "net":n}
            st.metric("Toplam Net", round(t_net, 2))
            if st.button("Deneme Kaydet", key=f"db_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2), "detay": d_detay})
                veri_kaydet(st.session_state.db)

        with c3:
            kad = st.text_input("Kitap", key=f"ka_{uid}")
            kyz = st.text_input("Yazar", key=f"ky_{uid}")
            ksy = st.number_input("Sayfa", 0, key=f"ks_{uid}")
            b1, b2 = st.columns(2)
            bt = b1.date_input("Başlama", key=f"b_{uid}")
            bit = b2.date_input("Bitiş", key=f"bit_{uid}")
            if st.button("Kitap Ekle", key=f"kb_{uid}"):
                uv["kitaplar"].append({"ad": kad, "yz": kyz, "s": ksy, "b": str(bt), "bit": str(bit)})
                veri_kaydet(st.session_state.db)

    # Rol Yönetimi
    if st.session_state.role == "student":
        st.header(f"👋 Merhaba, {st.session_state.user}")
        m = st.radio("Menü", ["Veri Girişi", "Gelişimim"], horizontal=True)
        if m == "Veri Girişi": data_hub(st.session_state.user)
        else:
            uv = st.session_state.db["users"][st.session_state.user]
            # Kaynak Tablosu
            if uv.get("kaynaklar"):
                st.write("### 📚 Ödev ve Kaynaklarım")
                st.table(pd.DataFrame(uv["kaynaklar"]))
            # Grafik
            if uv.get("denemeler"):
                df = pd.DataFrame(uv["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", title="Net Gelişimi", markers=True))

    elif st.session_state.role == "teacher":
        st.header("👨‍🏫 Öğretmen Paneli")
        m = st.sidebar.radio("Yönetim", ["Öğrenci Ekle", "Veri Girişleri", "Kaynak Atama", "Raporlar"])
        
        if m == "Öğrenci Ekle":
            nu = st.text_input("Kullanıcı Adı")
            np = st.text_input("Şifre")
            if st.button("Öğrenci Kaydet"):
                st.session_state.db["users"][nu] = {"password": np, "sorular": [], "denemeler": [], "kitaplar": [], "kaynaklar": []}
                veri_kaydet(st.session_state.db); st.success("Kaydedildi")

        elif m == "Veri Girişleri":
            so = st.selectbox("Öğrenci Seç", list(st.session_state.db["users"].keys()))
            if so: data_hub(so)

        elif m == "Kaynak Atama":
            so = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            sd = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            sk = st.selectbox("Konu", DERSLER_KONULAR[sd])
            r_ad = st.text_input("Kaynak Adı")
            if st.button("Ata"):
                st.session_state.db["users"][so]["kaynaklar"].append({"d": sd, "k": sk, "ad": r_ad})
                veri_kaydet(st.session_state.db); st.success("Atandı")

        elif m == "Raporlar":
            sr = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            if sr:
                st.write("### Canlı İstatistikler")
                uv = st.session_state.db["users"][sr]
                c1, c2 = st.columns(2)
                c1.metric("Toplam Soru", sum(int(s["do"])+int(s["ya"]) for s in uv.get("sorular", [])))
                c2.metric("Deneme Sayısı", len(uv.get("denemeler", [])))
                
                pdf_byte = generate_pdf_report(sr, uv)
                st.download_button("📄 PDF Raporu İndir", pdf_byte, f"{sr}_Karne.pdf", "application/pdf")
