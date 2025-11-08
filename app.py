# app.py

import streamlit as st
import pandas as pd
import sys
import os
import logging
import matplotlib.pyplot as plt 
import seaborn as sns           
from io import StringIO         

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logging.info("Aplikasi Streamlit dimulai.")
# --- Selesai Logging ---

# Impor modul yang sudah kita buat
try:
    from csv_handler import load_csv
    from data_agent import create_llm_instance, get_ai_code
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError as e:
    st.error(f"Gagal mengimpor modul. Pastikan file 'csv_handler.py' dan 'data_agent.py' ada di direktori yang sama. Error: {e}")
    logging.error(f"Gagal impor modul: {e}", exc_info=True)
    st.stop()
    
# --- 1. Konfigurasi Halaman dan Session State ---
st.set_page_config(layout="wide", page_title="📊 AI Data Analyst (Model Generator Kode)")

# Inisialisasi session state
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = None
if 'api_key_valid' not in st.session_state:
    st.session_state['api_key_valid'] = False
if 'llm' not in st.session_state:
    st.session_state['llm'] = None

# --- 2. Sidebar (Kontrol UI) ---
with st.sidebar:
    st.title("🧩 Setup Aplikasi")
    
    api_key_input = st.text_input(
        "Masukkan Google API Key Anda", 
        type="password",
        help="Dapatkan kunci Anda dari Google AI Studio."
    )
    
    if st.button("Cek API Key"):
        if not api_key_input:
            st.warning("Silakan masukkan API Key terlebih dahulu.")
        else:
            with st.spinner("Memvalidasi API Key..."):
                try:
                    test_llm = create_llm_instance(api_key_input)
                    test_llm.invoke("test") 
                    
                    st.success("API Key valid dan berfungsi!")
                    st.session_state['api_key_valid'] = True
                    st.session_state['api_key'] = api_key_input
                    st.session_state['llm'] = test_llm 
                    os.environ["GEMINI_API_KEY"] = api_key_input
                    logging.info("API Key berhasil divalidasi.")
                except Exception as e:
                    st.error(f"API Key tidak valid atau gagal terhubung. Error: {e}")
                    logging.error(f"Validasi API Key gagal: {e}", exc_info=True)
                    st.session_state['api_key_valid'] = False
    
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Unggah file CSV Anda", 
        type=["csv"],
        disabled=not st.session_state['api_key_valid']
    )
    
    with st.expander("⚙️ Opsi Lanjutan (Manual Override)", expanded=False):
        manual_delimiter = st.selectbox("Pilih Delimiter Manual", ["Otomatis", ",", ";", "\t", "|"], 0)
        manual_encoding = st.selectbox("Pilih Encoding Manual", ["Otomatis", "utf-8", "latin1", "iso-8859-1", "cp1252"], 0)
        manual_skiprows = st.number_input("Baris untuk Dilewati (Skip Rows)", 0, value=0, step=1)

    if uploaded_file is not None and st.session_state['api_key_valid']:
        delimiter_arg = None if manual_delimiter == "Otomatis" else manual_delimiter
        encoding_arg = None if manual_encoding == "Otomatis" else manual_encoding
        
        df_loaded = load_csv(
            uploaded_file, 
            manual_delimiter=delimiter_arg,
            manual_encoding=encoding_arg,
            manual_skiprows=manual_skiprows
        )
        
        if df_loaded is not None:
            st.session_state['df'] = df_loaded
        else:
            st.session_state['df'] = None
            
    st.markdown("---")
    
    if st.button("Hapus Riwayat Chat"):
        st.session_state['chat_history'] = []
        logging.info("Riwayat chat dihapus.")
        st.rerun()

# --- 3. Area Utama (Main Layout) ---
st.title("📊 AI Data Analyst (Model Generator Kode)")

if not st.session_state['api_key_valid']:
    st.info("🔑 Silakan masukkan Google API Key Anda di sidebar dan klik 'Cek API Key' untuk memulai.")
    st.stop()

if st.session_state['df'] is None:
    st.info("📂 Silakan unggah file CSV Anda di sidebar untuk memulai analisis.")
    st.stop()

df = st.session_state['df']
llm = st.session_state['llm']

with st.expander("Lihat Data Overview (Preview, Info, Statistik)", expanded=False):
    st.subheader(f"Preview Data (Total {df.shape[0]} baris, {df.shape[1]} kolom)")
    st.dataframe(df.head(50))
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statistik Deskriptif")
        # --- PERBAIKAN PYARROW: Hapus include='all' ---
        st.dataframe(df.describe()) 
    with col2:
        st.subheader("Info Tipe Kolom & Nilai Null")
        buffer = StringIO()
        df.info(buf=buffer)
        s = buffer.getvalue()
        st.text(s)


st.markdown("---")

# --- 4. AI Assistant Chat (LOGIKA BARU) ---
st.header("🤖 AI Assistant Chat")

for message in st.session_state['chat_history']:
    role = "user" if isinstance(message, HumanMessage) else "assistant"
    with st.chat_message(role):
        if isinstance(message, AIMessage) and "**Maaf, terjadi Error Eksekusi:**" in message.content:
            st.error(message.content)
        else:
            st.markdown(message.content)

user_query = st.chat_input("Tulis pertanyaan atau perintah analisis... (misal: 'Tampilkan rata-rata penjualan per tahun')")

if user_query:
    logging.info(f"Menerima kueri baru dari user: {user_query}")
    st.session_state['chat_history'].append(HumanMessage(content=user_query))
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.spinner("🧠 AI sedang menulis kode..."):
            
            # --- PERBAIKAN NAMEERROR: Inisialisasi variabel di sini ---
            ai_code_string = "" 
            
            try:
                # 1. Panggil AI untuk mendapatkan string kode
                ai_code_string = get_ai_code(user_query, df, llm)
                
                # 2. Siapkan environment untuk exec()
                global_vars = {
                    "df": df,
                    "st": st,
                    "pd": pd,
                    "plt": plt,
                    "sns": sns,
                    "StringIO": StringIO 
                }
                
                # 3. Jalankan kode di Main Thread!
                exec(ai_code_string, global_vars)
                
                response_for_history = "Perintah berhasil dieksekusi."
                st.session_state['chat_history'].append(AIMessage(content=response_for_history))

            except Exception as e:
                # 5. Jika exec() GAGAL (atau get_ai_code GAGAL)
                logging.error(f"Gagal mengeksekusi kode AI: {e}\nKode: {ai_code_string}", exc_info=True)
                
                # Sekarang ini aman karena ai_code_string pasti terdefinisi
                error_message = f"**Maaf, terjadi Error Eksekusi:**\n\n```\n{e}\n```\n\n**Kode yang Gagal Dijalankan:**\n```python\n{ai_code_string}\n```"
                st.error(error_message)
                
                st.session_state['chat_history'].append(AIMessage(content=error_message))