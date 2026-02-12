import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
from github import Github

# --- 1. SAYFA AYARLARI ---
st.set_page_config(page_title="LGS Master Pro", page_icon="🏆", layout="wide")

# --- 2. AYARLAR ---
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
        if "general" in st.secrets:
            token = st.secrets["general"]["GITHUB_TOKEN"]
            repo_name = st.secrets["general"]["REPO_NAME"]
            g = Github(token)
            repo = g.get_repo(repo_name)
            try:
                contents = repo.get_contents(DB_FILE)
                repo.update_file(contents.path, "Oto-Yedek", json.dumps(data, indent=4), contents.sha)
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
            if "users" not in data: data["users"] = {}
            if "admin_sifre" not in data: data["admin_sifre"] = "admin123"
            return data
        except:
            pass
    return {"users": {}, "admin_sifre": "admin123"}

def veri_kaydet(data):
    # Yerel Kayıt
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state.db = data
    
    # Bulut Kayıt
    if github_yedekle(data):
        st.toast("☁️ GitHub'a yedeklendi!", icon="✅")
    else:
        st.toast("💾 Yerel kayıt yapıldı.", icon="ℹ️")

if "db" not in st.session_state: st.session_state.db = veri_yukle()
if "user" not in st.session_state: st.session_state.user = None

# --- 5. PDF MOTORU (DÜZELTİLDİ) ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf_report(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    
    # Mavi Başlık
    pdf.set_fill_color(31, 119, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS GELISIM RAPORU: {user_name.upper()}"), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    # 1. Kaynaklar
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "ATANAN KAYNAKLAR", ln=True)
    pdf.set_font("Helvetica", '', 9)
    if user_data.get("kaynaklar"):
        for k in user_data["kaynaklar"]:
            pdf.cell(190, 7, tr_fix(f"- {k['d']} | {k['k']} | {k['ad']}"), ln=True)
    else:
        pdf.cell(190, 7, "Henuz kaynak yok.", ln=True)
    pdf.ln(5)
    
    # 2. Deneme Tablosu
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME NET GELISIMI", ln=True)
    pdf.set_font("Helvetica", 'B', 9)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(35, 8, "Tarih", 1, 0, 'C', True)
    pdf.cell(65, 8, "Yayin", 1, 0, 'C', True)
    pdf.cell(45, 8, "Toplam Net", 1, 0, 'C', True)
    pdf.cell(45, 8, "Fark", 1, 1, 'C', True)
    
    pdf.set_font("Helvetica", '', 9)
    prev = None
    for d in sorted(user_data.get("denemeler", []), key=lambda x: x['t']):
        degisim = round(d['top'] - prev, 2) if prev is not None else "-"
        pdf.cell(35, 7, d['t'], 1, 0, 'C')
        pdf.cell(65, 7, tr_fix(d['y']), 1)
        pdf.cell(45, 7, str(d['top']), 1, 0, 'C')
        pdf.cell(45, 7, str(degisim), 1, 1, 'C')
        prev = d['top']

    # 3. Kitaplar
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "OKUNAN KITAPLAR", ln=True)
    pdf.set_font("Helvetica", '', 9)
    for b in user_data.get("kitaplar", []):
        pdf.cell(190, 7, tr_fix(f"- {b['ad']} ({b.get('yz','-')}) | {b.get('s','0')} Sayfa"), ln=True)

    return bytes(pdf.output())

# --- 6. ARAYÜZ ---
if st.session_state.user is None:
    st.title("🛡️ LGS Master Pro")
    t1, t2 = st.tabs(["Öğrenci Girişi", "Öğretmen Girişi"])
    with t1:
        u = st.text_input("Kullanıcı Adı", key="u_log")
        p = st.text_input("Şifre", type="password", key="p_log")
        if st.button("Giriş"):
            if u in st.session_state.db["users"] and st.session_state.db["users"][u]["password"] == p:
                st.session_state.user, st.session_state.role = u, "student"; st.rerun()
            else: st.error("Hatalı Giriş")
    with t2:
        ap = st.text_input("Yönetici Şifresi", type="password")
        if st.button("Yönetici Giriş"):
            if ap == st.session_state.db["admin_sifre"]:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
            else: st.error("Hatalı Şifre")

else:
    kalan = LGS_TARIHI - datetime.datetime.now()
    st.sidebar.markdown(f"<div style='background:#d32f2f;color:white;padding:10px;border-radius:5px;text-align:center;'><b>⏳ LGS'YE {kalan.days} GÜN</b></div>", unsafe_allow_html=True)
    st.sidebar.write(f"👤 {st.session_state.user}")
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()

    def data_hub(uid):
        uv = st.session_state.db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        
        # --- SORU GİRİŞİ ---
        with t1:
            c1, c2 = st.columns(2)
            tar = c1.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = c2.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            # Key çakışmasını önlemek için 'soru_konu_'
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"soru_konu_{uid}")
            
            x1, x2, x3 = st.columns(3)
            do = x1.number_input("D",0,key=f"do_{uid}")
            ya = x2.number_input("Y",0,key=f"ya_{uid}")
            bo = x3.number_input("B",0,key=f"bo_{uid}")
            if st.button("Soru Kaydet", key=f"btn_soru_{uid}"):
                uv["sorular"].append({"t":str(tar),"d":dr,"k":ko,"do":do,"ya":ya,"bo":bo})
                veri_kaydet(st.session_state.db)
                st.success("Soru eklendi!")

        # --- DENEME GİRİŞİ (LİSTE AÇIK + BOŞ KUTUSU) ---
        with t2:
            st.markdown("### 📊 Deneme Sınavı Girişi")
            col_ust1, col_ust2 = st.columns(2)
            yay = col_ust1.text_input("Yayın Adı", key=f"y_{uid}")
            dt = col_ust2.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            
            c_sol, c_sag = st.columns(2)
            ders_listesi = list(DERSLER_KONULAR.keys())
            
            t_net = 0
            d_detay = {}
            
            # Sol Sütun (İlk 3 Ders)
            with c_sol:
                for ds in ders_listesi[:3]:
                    st.markdown(f"**{ds}**")
                    k1, k2, k3 = st.columns(3)
                    dd = k1.number_input("D", 0, key=f"{ds}d_{uid}")
                    dy = k2.number_input("Y", 0, key=f"{ds}y_{uid}")
                    db_ = k3.number_input("B", 0, key=f"{ds}b_{uid}")
                    net = round(dd - (dy / 3), 2)
                    t_net += net
                    d_detay[ds] = {"d": dd, "y": dy, "b": db_, "net": net}
                    st.caption(f"Net: {net}")
                    st.divider()

            # Sağ Sütun (Son 3 Ders)
            with c_sag:
                for ds in ders_listesi[3:]:
                    st.markdown(f"**{ds}**")
                    k1, k2, k3 = st.columns(3)
                    dd = k1.number_input("D", 0, key=f"{ds}d_{uid}")
                    dy = k2.number_input("Y", 0, key=f"{ds}y_{uid}")
                    db_ = k3.number_input("B", 0, key=f"{ds}b_{uid}")
                    net = round(dd - (dy / 3), 2)
                    t_net += net
                    d_detay[ds] = {"d": dd, "y": dy, "b": db_, "net": net}
                    st.caption(f"Net: {net}")
                    st.divider()

            st.info(f"📌 Toplam Net: {round(t_net, 2)}")
            if st.button("Deneme Sonucunu Kaydet", key=f"btn_deneme_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2), "detay": d_detay})
                veri_kaydet(st.session_state.db)
                st.success("Deneme kaydedildi!")

        # --- KİTAP GİRİŞİ (DÜZELTİLDİ: TÜM DETAYLAR) ---
        with t3:
            st.markdown("### 📚 Kitap Okuma Takibi")
            # Key çakışmasını önlemek için 'b_' prefix
            kad = st.text_input("Kitap Adı", key=f"b_ad_{uid}")
            kyz = st.text_input("Yazar", key=f"b_yazar_{uid}")
            ksy = st.number_input("Sayfa Sayısı", 0, key=f"b_sayfa_{uid}")
            
            c_b1, c_b2 = st.columns(2)
            bt = c_b1.date_input("Başlama", key=f"b_basla_{uid}")
            bit = c_b2.date_input("Bitiş", key=f"b_bitis_{uid}")
            
            if st.button("Kitap Ekle", key=f"btn_kitap_{uid}"):
                uv["kitaplar"].append({"ad":kad, "yz":kyz, "s":ksy, "b":str(bt), "bit":str(bit)})
                veri_kaydet(st.session_state.db)
                st.success("Kitap eklendi!")

    if st.session_state.role == "student":
        st.header(f"Merhaba {st.session_state.user}")
        m = st.radio("Menü", ["Veri Girişi", "Gelişim"], horizontal=True)
        if m == "Veri Girişi": data_hub(st.session_state.user)
        else:
            uv = st.session_state.db["users"][st.session_state.user]
            if uv.get("kaynaklar"): 
                st.write("### 📚 Ödevlerim")
                st.table(pd.DataFrame(uv["kaynaklar"]))
            if uv.get("denemeler"):
                df = pd.DataFrame(uv["denemeler"])
                st.plotly_chart(px.line(df, x="t", y="top", markers=True))

    elif st.session_state.role == "teacher":
        st.header("Öğretmen Paneli")
        m = st.sidebar.radio("İşlemler", ["Öğrenci Ekle", "Veri Girişi", "Kaynak Ata", "Raporlar"])
        if m == "Öğrenci Ekle":
            nu, np = st.text_input("Ad"), st.text_input("Şifre")
            if st.button("Kaydet"):
                st.session_state.db["users"][nu] = {"password":np, "sorular":[], "denemeler":[], "kitaplar":[], "kaynaklar":[]}
                veri_kaydet(st.session_state.db); st.success("Tamam")
        elif m == "Veri Girişi":
            so = st.selectbox("Seç", list(st.session_state.db["users"].keys()))
            if so: data_hub(so)
        elif m == "Kaynak Ata":
            so = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            sd = st.selectbox("Ders", list(DERSLER_KONULAR.keys()))
            sk = st.selectbox("Konu", DERSLER_KONULAR[sd])
            r = st.text_input("Kaynak")
            if st.button("Ata"):
                st.session_state.db["users"][so]["kaynaklar"].append({"d":sd, "k":sk, "ad":r})
                veri_kaydet(st.session_state.db); st.success("Atandı")
        elif m == "Raporlar":
            sr = st.selectbox("Öğrenci", list(st.session_state.db["users"].keys()))
            if sr:
                st.download_button("PDF İndir", generate_pdf_report(sr, st.session_state.db["users"][sr]), f"{sr}.pdf")
