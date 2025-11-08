# data_agent.py

import pandas as pd
import streamlit as st
import logging
from io import StringIO
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI

def create_llm_instance(api_key: str):
    """Membuat instance LLM (dipanggil oleh app.py untuk tes dan eksekusi)."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.0,
        convert_to_functions=False 
    )

def get_dataframe_schema(df: pd.DataFrame) -> str:
    """Membuat ringkasan schema (info) dari dataframe untuk diberikan ke AI."""
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

def get_ai_code(
    query: str, 
    df: pd.DataFrame, 
    llm: ChatGoogleGenerativeAI
) -> str:
    """
    Satu-satunya fungsi yang memanggil AI.
    Meminta AI untuk menulis kode Streamlit/Pandas berdasarkan kueri.
    """
    
    schema = get_dataframe_schema(df)
    
    # --- PERBAIKAN KRITIS DI SINI ---
    # Kita mendefinisikan template sebagai string REGULER (bukan f-string)
    # Ini MENCEGAH Python mengeksekusi contoh-contoh di bawah.
    system_prompt_template = """
Anda adalah AI Data Analyst yang ahli dalam Python, Pandas, dan Streamlit.
Tugas Anda adalah menulis satu blok kode Python untuk menjawab pertanyaan user 
berdasarkan DataFrame Pandas yang disebut `df`.

--- PERATURAN WAJIB (HARUS DIIKUTI!) ---
1.  **HANYA KODE:** Respons Anda HARUS hanya berisi kode Python. JANGAN
    tulis penjelasan, JANGAN gunakan markdown (seperti ```python ... ```).
    Hanya kode mentah.
2.  **TAMPILKAN OUTPUT:** Kode Anda HARUS menampilkan outputnya ke layar.
    Gunakan fungsi Streamlit yang sesuai:
    * Untuk teks, angka, atau jawaban singkat: `st.markdown(f"### {hasil}")`
    * Untuk tabel (DataFrame/Series): `st.dataframe(hasil)`
    * Untuk plot sederhana: `st.line_chart(data, x=..., y=...)`, `st.bar_chart(...)`
3.  **PRIORITASKAN NATIVE CHARTS:** Selalu utamakan `st.line_chart`, 
    `st.bar_chart`, dan `st.area_chart`. Ini lebih cepat.
4.  **PLOT KOMPLEKS:** Gunakan `matplotlib` atau `seaborn` HANYA jika
    grafik yang diminta adalah scatter plot, heatmap, histogram, atau
    multi-axis.
    * Jika Anda menggunakannya, kode Anda HARUS diakhiri dengan `st.pyplot(plt.gcf())`.
5.  **SATU BLOK:** Tulis semua logika Anda dalam satu blok. Jangan pecah
    menjadi beberapa bagian.
6.  **VARIABEL YANG TERSEDIA:** Kode Anda akan dieksekusi dalam
    lingkungan di mana `df` (DataFrame), `st` (Streamlit), `pd` (Pandas),
    `plt` (matplotlib.pyplot), dan `sns` (seaborn) sudah diimpor dan
    tersedia.

--- CONTOH (Ini sekarang hanya teks biasa) ---
User: produk apa yang paling laris?
Anda Jawab:
st.markdown(f"### {df['NamaProduk'].value_counts().idxmax()}")

User: berapa rata-rata penjualan?
Anda Jawab:
st.markdown(f"### {df['JumlahPenjualan'].mean()}")

User: tampilkan 5 produk teratas berdasarkan penjualan
Anda Jawab:
st.dataframe(df.groupby('NamaProduk')['JumlahPenjualan'].sum().nlargest(5))

User: buat overview data
Anda Jawab:
st.subheader("Statistik Deskriptif")
st.dataframe(df.describe())
st.subheader("Info Kolom")
buffer = StringIO()
df.info(buf=buffer)
st.text(buffer.getvalue())

User: plot tren penjualan per tanggal
Anda Jawab:
st.line_chart(df.groupby('Tanggal')['JumlahPenjualan'].sum())
---

DATA FRAME SCHEMA (`df.info()`):
"""
    # --- PERBAIKAN SELESAI ---

    # Kita gabungkan string secara manual untuk keamanan
    final_prompt = (
        system_prompt_template 
        + schema 
        + "\n\nUSER QUERY:\n" 
        + query 
        + "\n\nPYTHON CODE (Hanya kode!):\n"
    )

    logging.info("Membuat kueri ke LLM untuk menghasilkan kode...")
    try:
        # Kirim prompt final yang sudah aman
        response = llm.invoke(final_prompt) 
        ai_code = response.content.strip()
        
        # Bersihkan jika AI masih menyertakan markdown
        if ai_code.startswith("```python"):
            ai_code = ai_code[9:]
        if ai_code.startswith("```"):
            ai_code = ai_code[3:]
        if ai_code.endswith("```"):
            ai_code = ai_code[:-3]
            
        logging.info(f"AI menghasilkan kode:\n{ai_code}")
        return ai_code.strip()
        
    except Exception as e:
        logging.error(f"Gagal memanggil LLM: {e}", exc_info=True)
        return f"st.error(f'Gagal menghasilkan kode AI: {e}')"