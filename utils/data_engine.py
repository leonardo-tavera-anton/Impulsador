import streamlit as st
import pandas as pd
import requests

URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {"apikey": KEY, "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

@st.cache_data(ttl=300)
def load_sura_core_db(anio_actual):
    all_data = []
    offset, limit = 0, 1000
    while True:
        r = requests.get(f"{URL}/rest/v1/clientes?select=*&order=dni&offset={offset}&limit={limit}", headers=HEADERS)
        batch = r.json()
        if not batch: break
        all_data.extend(batch)
        if len(batch) < limit: break
        offset += limit
    
    df = pd.DataFrame(all_data)
    if not df.empty:
        for col in ['monto', 'cuota', 'deuda']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        
        def check_month(hist, mes):
            try: return "✅" if hist.get(str(anio_actual), {}).get(mes) == 1 else "❌"
            except: return "❌"
        
        for m in ['enero', 'febrero', 'marzo']:
            df[m[:3].upper()] = df['historial'].apply(lambda x: check_month(x, m))
    return df