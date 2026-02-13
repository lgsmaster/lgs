import streamlit as st
import pandas as pd
import json
import os
import datetime
import plotly.express as px
from fpdf import FPDF
from github import Github

# --- 1. SAYFA VE SİSTEM AYARLARI ---
st.set_page_config(page_title="LGS Master Pro", page_icon="🏆", layout="wide")

# --- GİZLİLİK VE GÜVENLİK (CSS) ---
# Bu kısım üstteki menüyü, GitHub simgesini ve footer'ı gizler
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 2. SABİTLER ---
DB_FILE = "lgs_platinum_db.json"
VARSAYILAN_TARIH = "2026-06-14"

# ŞİFREYİ GÜVENLİ YERDEN ÇEK (SECRETS)
# Eğer Secrets ayarlanmamışsa geçici olarak 'admin123' kullanır (Güvenlik ağı)
try:
    ADMIN_SIFRESI = st.secrets["general"]["ADMIN_SIFRE"]
except:
    ADMIN_SIFRESI = "admin123"

DERSLER_KONULAR = {
    "Turkce": ["Paragraf", "Sozcukte Anlam", "Cumlede Anlam", "Fiilimsiler", "Cumlenin Ogeleri", "Yazim Kurallari", "Noktalama Isaretleri"],
    "Matematik": ["Carpanlar ve Katlar", "Uslu Ifadeler", "Karekoklu Ifadeler", "Veri Analizi", "Olasilik", "Cebirsel Ifadeler", "Dogrusal Denklemler"],
    "Fen": ["Mevsimler ve Iklim", "DNA ve Genetik Kod", "Basinc", "Madde ve Endustri", "Basit Makineler", "Enerji Donusumleri"],
    "Inkilap": ["Bir Kahraman Doguyor", "Milli Uyanis", "Ya Istiklal Ya Olum", "Ataturkculuk ve Cagdaslasma"],
    "Din": ["Kader Inanci", "Zekat ve Sadaka", "Din ve Hayat", "Hz. Muhammed'in Ornekligi"],
    "Ingilizce": ["Friendship", "Teen Life", "In The Kitchen", "On The Phone", "The Internet"]
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
                repo.update_file(contents.path, "Oto-Yedek (Streamlit)", json.dumps(data, indent=4), contents.sha)
            except:
                repo.create_file(DB_FILE, "İlk Kurulum", json.dumps(data, indent=4))
            return True
        return False
    except Exception as e:
        # Hata olsa bile kullanıcıya gösterme (Güvenlik için)
        return False

# --- 4. VERİ YÖNETİMİ ---
def veri_yukle():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "users" not in data: data["users"] = {}
            if "lgs_tarih" not in data: data["lgs_tarih"] = VARSAYILAN_TARIH
            return data
        except:
            pass
    return {"users": {}, "lgs_tarih": VARSAYILAN_TARIH}

def veri_kaydet(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.session_state.db = data
    if github_yedekle(data):
        st.toast("☁️ Veriler GitHub'a yedeklendi!", icon="✅")
    else:
        st.toast("💾 Yerel diske kaydedildi.", icon="ℹ️")

if "db" not in st.session_state: st.session_state.db = veri_yukle()
if "user" not in st.session_state: st.session_state.user = None
if "role" not in st.session_state: st.session_state.role = None

# --- 5. PDF MOTORU ---
def tr_fix(text):
    rep = {"ı":"i", "İ":"I", "ş":"s", "Ş":"S", "ğ":"g", "Ğ":"G", "ü":"u", "Ü":"U", "ö":"o", "Ö":"O", "ç":"c", "Ç":"C"}
    for old, new in rep.items(): text = text.replace(old, new)
    return text

def generate_pdf_report(user_name, user_data):
    pdf = FPDF()
    pdf.add_page()
    
    # --- A. MAVİ BAŞLIK ---
    pdf.set_fill_color(31, 119, 180) 
    pdf.set_text_color(255, 255, 255) 
    pdf.set_font("Helvetica", 'B', 16)
    pdf.cell(190, 15, tr_fix(f"LGS GELISIM RAPORU: {user_name.upper()}"), ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0) 
    pdf.ln(5)

    # --- B. ÖZET ---
    pdf.set_font("Helvetica", 'B', 10)
    top_soru = sum(int(s.get('do',0))+int(s.get('ya',0))+int(s.get('bo',0)) for s in user_data.get("sorular", []))
    pdf.cell(190, 6, f"Toplam Soru: {top_soru} | Deneme Sayisi: {len(user_data.get('denemeler', []))} | Kitap: {len(user_data.get('kitaplar', []))}", ln=True)
    pdf.ln(5)

    # --- C. DENEME ANALİZİ ---
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "DENEME SINAVLARI DETAYLI NET ANALIZI", ln=True)
    
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(230, 230, 230)
    headers = [("Tarih",20), ("Yayin",35), ("Tr",16), ("Mat",16), ("Fen",16), ("Ink",16), ("Din",16), ("Ing",16), ("Top",19)]
    for h in headers:
        pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font("Helvetica", '', 8)
    ders_keys = ["Turkce", "Matematik", "Fen", "Inkilap", "Din", "Ingilizce"]
    
    for d in sorted(user_data.get("denemeler", []), key=lambda x: x['t']):
        pdf.cell(20, 7, d['t'], 1)
        pdf.cell(35, 7, tr_fix(d['y'][:18]), 1)
        detay = d.get('detay', {})
        for key in ders_keys:
            net_val = str(detay[key]['net']) if key in detay else "-"
            pdf.cell(16, 7, net_val, 1, 0, 'C')
        pdf.cell(19, 7, str(d['top']), 1, 1, 'C')

    pdf.ln(5)

    # --- D. KİTAP LİSTESİ ---
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "OKUMA GECMISI (KITAPLAR)", ln=True)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(230, 230, 230)
    h_book = [("Kitap Adi",60), ("Yazar",40), ("Sayfa",20), ("Baslama",35), ("Bitis",35)]
    for h in h_book:
        pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 8)
    if user_data.get("kitaplar"):
        for b in user_data["kitaplar"]:
            pdf.cell(60, 7, tr_fix(b['ad'][:30]), 1)
            pdf.cell(40, 7, tr_fix(b['yz'][:20]), 1)
            pdf.cell(20, 7, str(b['s']), 1, 0, 'C')
            pdf.cell(35, 7, b['b'], 1, 0, 'C')
            pdf.cell(35, 7, b['bit'], 1, 1, 'C')
    else:
        pdf.cell(190, 7, "Henuz kitap girisi yapilmadi.", 1, 1, 'C')

    pdf.ln(5)

    # --- E. SORU ÇÖZÜM TABLOSU ---
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "SON COZULEN SORULAR", ln=True)
    pdf.set_font("Helvetica", 'B', 8)
    pdf.set_fill_color(230, 230, 230)
    headers_soru = [("Tarih",25), ("Ders",30), ("Konu",60), ("D",12), ("Y",12), ("B",12), ("Top",39)]
    for h in headers_soru:
        pdf.cell(h[1], 8, h[0], 1, 0, 'C', True)
    pdf.ln()
    pdf.set_font("Helvetica", '', 7)
    for s in user_data.get("sorular", [])[-25:]: 
        total = int(s.get('do',0)) + int(s.get('ya',0)) + int(s.get('bo',0))
        pdf.cell(25, 6, s['t'], 1)
        pdf.cell(30, 6, tr_fix(s['d']), 1)
        pdf.cell(60, 6, tr_fix(s['k'][:32]), 1)
        pdf.cell(12, 6, str(s['do']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['ya']), 1, 0, 'C')
        pdf.cell(12, 6, str(s['bo']), 1, 0, 'C')
        pdf.cell(39, 6, str(total), 1, 1, 'C')

    # --- F. KAYNAKLAR ---
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(190, 10, "ATANAN KAYNAKLAR", ln=True)
    pdf.set_font("Helvetica", '', 9)
    if user_data.get("kaynaklar"):
        for k in user_data["kaynaklar"]:
            pdf.cell(190, 7, tr_fix(f"- {k['d']} | {k['k']} | {k['ad']}"), ln=True)
    else:
        pdf.cell(190, 7, "Atanmis kaynak bulunamadi.", ln=True)

    return bytes(pdf.output())

# --- 6. ARAYÜZ VE UYGULAMA ---
if st.session_state.user is None:
    # Başlıkları CSS ile biraz daha aşağı itmek gerekebilir header gizlendiği için
    st.markdown("<br>", unsafe_allow_html=True)
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
            # Şifreyi SECRETS değişkeninden kontrol et
            if ap == ADMIN_SIFRESI:
                st.session_state.user, st.session_state.role = "Admin", "teacher"; st.rerun()
            else: st.error("Hatalı Şifre")

else:
    # --- GERİ SAYIM (DİNAMİK) ---
    hedef_str = st.session_state.db.get("lgs_tarih", VARSAYILAN_TARIH)
    try:
        hedef_tarih = datetime.datetime.strptime(hedef_str, "%Y-%m-%d")
        simdi = datetime.datetime.now()
        kalan = hedef_tarih - simdi
        days_left = kalan.days
    except:
        days_left = 0

    # Sidebar
    st.sidebar.markdown(f"<div style='background:#d32f2f;color:white;padding:10px;border-radius:5px;text-align:center;'><b>⏳ LGS'YE {days_left} GÜN</b><br><small>{hedef_str}</small></div>", unsafe_allow_html=True)
    st.sidebar.write(f"👤 {st.session_state.user}")
    if st.sidebar.button("Çıkış"): st.session_state.user = None; st.rerun()

    def data_hub(uid):
        uv = st.session_state.db["users"][uid]
        t1, t2, t3 = st.tabs(["📝 Soru", "📊 Deneme", "📚 Kitap"])
        
        with t1:
            c1, c2 = st.columns(2)
            tar = c1.date_input("Tarih", datetime.date.today(), key=f"t_{uid}")
            dr = c2.selectbox("Ders", list(DERSLER_KONULAR.keys()), key=f"d_{uid}")
            ko = st.selectbox("Konu", DERSLER_KONULAR[dr], key=f"soru_konu_{uid}")
            x1, x2, x3 = st.columns(3)
            do = x1.number_input("D", 0, key=f"do_{uid}")
            ya = x2.number_input("Y", 0, key=f"ya_{uid}")
            bo = x3.number_input("B", 0, key=f"bo_{uid}")
            if st.button("Soru Kaydet", key=f"btn_soru_{uid}"):
                uv["sorular"].append({"t":str(tar),"d":dr,"k":ko,"do":do,"ya":ya,"bo":bo})
                veri_kaydet(st.session_state.db)
                st.success("Soru kaydedildi!")

        with t2:
            st.markdown("### 📊 Deneme Sınavı Girişi")
            col_ust1, col_ust2 = st.columns(2)
            yay = col_ust1.text_input("Yayın Adı", key=f"y_{uid}")
            dt = col_ust2.date_input("Sınav Tarihi", datetime.date.today(), key=f"dt_{uid}")
            c_sol, c_sag = st.columns(2)
            ders_listesi = list(DERSLER_KONULAR.keys())
            t_net = 0
            d_detay = {}
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
                    st.divider()
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
                    st.divider()
            st.info(f"📌 Toplam Net: {round(t_net, 2)}")
            if st.button("Deneme Sonucunu Kaydet", key=f"btn_deneme_{uid}"):
                uv["denemeler"].append({"t": str(dt), "y": yay, "top": round(t_net, 2), "detay": d_detay})
                veri_kaydet(st.session_state.db)
                st.success("Deneme eklendi!")

        with t3:
            st.markdown("### 📚 Kitap Okuma")
            kad = st.text_input("Kitap Adı", key=f"b_ad_{uid}")
            kyz = st.text_input("Yazar", key=f"b_yazar_{uid}")
            ksy = st.number_input("Sayfa Sayısı", 0, key=f"b_sayfa_{uid}")
            c_b1, c_b2 = st.columns(2)
            bt = c_b1.date_input("Başlama", key=f"b_basla_{uid}")
            bit = c_b2.date_input("Bitiş", key=f"b_bitis_{uid}")
            if st.button("Kitap Ekle", key=f"btn_kitap_{uid}"):
                uv["kitaplar"].append({"ad":kad, "yz":kyz, "s":ksy, "b":str(bt), "bit":str(bit)})
                veri_kaydet(st.session_state.db)
                st.success("Kitap kaydedildi!")

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
        m = st.sidebar.radio("İşlemler", ["Öğrenci Ekle", "Veri Girişi", "Kaynak Ata", "Raporlar", "Sınav Tarihi Ayarla"])
        
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
                st.download_button("📄 PDF Analiz İndir", generate_pdf_report(sr, st.session_state.db["users"][sr]), f"{sr}_Karne.pdf")
        
        elif m == "Sınav Tarihi Ayarla":
            st.subheader("📅 LGS Tarihini Değiştir")
            current_str = st.session_state.db.get("lgs_tarih", VARSAYILAN_TARIH)
            try:
                current_date = datetime.datetime.strptime(current_str, "%Y-%m-%d").date()
            except:
                current_date = datetime.date.today()
                
            new_date = st.date_input("Yeni Sınav Tarihi", current_date)
            
            if st.button("Tarihi Güncelle"):
                st.session_state.db["lgs_tarih"] = str(new_date)
                veri_kaydet(st.session_state.db)
                st.success(f"Tarih güncellendi: {new_date}. Sol menüdeki sayaç yenilenecek.")
                st.rerun()
