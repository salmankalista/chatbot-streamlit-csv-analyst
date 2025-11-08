# csv_handler.py

import pandas as pd
import io
import streamlit as st
from typing import Optional, List
import logging

# (Sisa kode... deteksi delimiter, dll.)
# ...

def load_csv(
    uploaded_file: io.BytesIO,
    manual_delimiter: Optional[str] = None,
    manual_encoding: Optional[str] = None,
    manual_skiprows: int = 0
) -> Optional[pd.DataFrame]:
    try:
        file_content = uploaded_file.getvalue()
        
        delimiter = manual_delimiter
        encoding = manual_encoding
        
        if not manual_delimiter or not manual_encoding:
            logging.info("Menjalankan deteksi otomatis...")
            auto_delimiter, auto_encoding = detect_delimiter_and_encoding(file_content)
            
            if not delimiter: delimiter = auto_delimiter
            if not encoding: encoding = auto_encoding
        
        if not delimiter or not encoding:
            st.error("Gagal mendeteksi delimiter atau encoding secara otomatis.")
            logging.warning("Deteksi otomatis gagal, meminta input manual.")
            return None

        if manual_delimiter or manual_encoding:
            logging.info(f"Menggunakan pengaturan manual: Delimiter='{delimiter}', Encoding='{encoding}', Skiprows={manual_skiprows}")
            st.success(f"Menggunakan pengaturan manual: Delim='{delimiter}', Enc='{encoding}', Skip={manual_skiprows}")
        else:
            logging.info(f"Deteksi otomatis berhasil: Delimiter='{delimiter}', Encoding='{encoding}'")
            st.success(f"Deteksi otomatis berhasil: Delim='{delimiter}', Enc='{encoding}'")

        df = pd.read_csv(
            io.StringIO(file_content.decode(encoding)),
            sep=delimiter,
            engine='python',
            skiprows=manual_skiprows 
        )
        
        df.columns = df.columns.str.strip()
        logging.info(f"File CSV berhasil dimuat. Shape: {df.shape}")
        return df
        
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat CSV: {e}")
        logging.error(f"Gagal memuat CSV: {e}", exc_info=True)
        return None

# (pastikan fungsi detect_delimiter_and_encoding() juga ada di file ini)
def detect_delimiter_and_encoding(file_content: bytes) -> tuple[Optional[str], Optional[str]]:
    sample_lines = file_content.splitlines()[:20]
    best_delimiter = None; best_encoding = None; max_avg_fields = 0 
    for encoding in COMMON_ENCODINGS:
        try:
            decoded_sample = [line.decode(encoding) for line in sample_lines]
            for delimiter in COMMON_DELIMITERS:
                field_counts = [len(line.split(delimiter)) for line in decoded_sample if line.strip()]
                if not field_counts: continue
                avg_fields = sum(field_counts) / len(field_counts)
                if avg_fields > max_avg_fields and avg_fields > 1:
                    max_avg_fields = avg_fields; best_delimiter = delimiter; best_encoding = encoding
        except UnicodeDecodeError: continue
    logging.info(f"Deteksi otomatis menemukan: Delimiter='{best_delimiter}', Encoding='{best_encoding}'")
    return best_delimiter, best_encoding

COMMON_DELIMITERS: List[str] = [',', ';', '\t', '|']
COMMON_ENCODINGS: List[str] = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']