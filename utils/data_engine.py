import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def get_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=3600, show_spinner=False)
def load_sura_core_db():
    all_data = []
    offset, chunk = 0, 1000
    msg = st.empty()
    try:
        while True:
            msg.info(f"⚡ Sincronizando: {offset:,} registros...")
            res = supabase.table("clientes").select("*").range(offset, offset + chunk - 1).execute()
            if not res.data: break
            all_data.extend(res.data)
            if len(res.data) < chunk: break
            offset += chunk
        
        df = pd.DataFrame(all_data)
        # LIMPIEZA ATÓMICA: Se hace una sola vez
        if not df.empty:
            df.columns = [c.lower().strip() for c in df.columns]
            df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True)
            for c in ['monto', 'deuda', 'cuota']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0.0)
            if 'historial' not in df.columns:
                df['historial'] = [{} for _ in range(len(df))]
        
        msg.empty()
        return df
    except Exception as e:
        msg.error(f"Error: {e}")
        return pd.DataFrame()