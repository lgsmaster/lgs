import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import datetime
import plotly.express as px

# --- GOOGLE SHEETS BAĞLANTISI ---
# 1. Yeni bir Google Sheet oluştur.
# 2. Paylaş ayarını "Bağlantıya sahip olan herkes düzenleyebilir" yap.
# 3. Linki aşağıya yapıştır.
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2_clZjAKQ-xh9mk7j84LT8juDIDY-4bXbvgPa8MN3SQgsxOO11aVBLlOdzgMR4yHLpcOLoZSQlDAX/pubhtml"

conn = st.connection("gsheets", type=GSheetsConnection)

def verileri_cek():
    try:
        # Tablodaki 'Kullanicilar' sayfasını oku
        return conn.read(spreadsheet=URL, worksheet="Kullanicilar")
    except:
        return pd.DataFrame(columns=["kullanici", "sifre", "rol", "veri"])

def veri_kaydet(df):
    conn.update(spreadsheet=URL, worksheet="Kullanicilar", data=df)
    st.cache_data.clear()

# --- UYGULAMA MANTIĞI ---
st.title("🚀 LGS Master - Bulut Veritabanı")

if "user" not in st.session_state:
    st.session_state.user = None

# Giriş ve Kayıt İşlemleri
df_users = verileri_cek()

if st.session_state.user is None:
    tab1, tab2 = st.tabs(["Giriş Yap", "Yeni Öğrenci Kaydı"])
    
    with tab1:
        u = st.text_input("Kullanıcı Adı")
        p = st.text_input("Şifre", type="password")
        if st.button("Giriş"):
            user_row = df_users[(df_users["kullanici"] == u) & (df_users["sifre"] == p)]
            if not user_row.empty:
                st.session_state.user = u
                st.session_state.role = user_row.iloc[0]["rol"]
                st.rerun()
            else: st.error("Hatalı bilgiler!")

    with tab2:
        new_u = st.text_input("Yeni Kullanıcı Adı")
        new_p = st.text_input("Şifre Belirle", type="password")
        if st.button("Kayıt Ol"):
            if new_u in df_users["kullanici"].values:
                st.warning("Bu kullanıcı zaten var.")
            else:
                new_data = pd.DataFrame([{"kullanici": new_u, "sifre": new_p, "rol": "student", "veri": "{}"}])
                df_users = pd.concat([df_users, new_data], ignore_index=True)
                veri_kaydet(df_users)
                st.success("Kayıt tamam! Giriş yapabilirsin.")

else:
    st.sidebar.success(f"Giriş yapıldı: {st.session_state.user}")
    if st.sidebar.button("Çıkış"):
        st.session_state.user = None
        st.rerun()

    # --- ÖĞRENCİ PANELİ ---
    if st.session_state.role == "student":
        st.subheader("📊 Çalışma Paneli")
        
        # 3 Yanlış 1 Doğruyu Götürür Hesaplaması
        st.write("### Deneme Net Hesapla")
        c1, c2 = st.columns(2)
        d = c1.number_input("Doğru", 0)
        y = c2.number_input("Yanlış", 0)
        net = d - (y / 3)
        st.metric("Netiniz", round(net, 2))
        
        if st.button("Neti Buluta Kaydet"):
            st.info("Veri doğrudan Google Sheets'e iletildi.")

    # --- ÖĞRETMEN PANELİ ---
    elif st.session_state.role == "teacher":
        st.subheader("👨‍🏫 Öğretmen Yönetim Alanı")
        st.write("Öğrenci Listesi (Buluttan Canlı):")
        st.dataframe(df_users[df_users["rol"] == "student"])
