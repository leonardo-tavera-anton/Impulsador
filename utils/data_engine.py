import streamlit as st
import pandas as pd
from supabase import create_client
import os
import time

@st.cache_resource
def get_supabase():
    """Establece la conexión única con Supabase."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=3600, show_spinner=False)
def load_sura_core_db():
    """Carga los 47k registros usando caché local Parquet para velocidad máxima."""
    cache_file = "cache_padron.parquet"
    
    # 1. Intentar cargar desde el archivo local (0.5 segundos)
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file) < 3600):
        return pd.read_parquet(cache_file)

    # 2. Si no hay caché, descargar de Supabase por lotes
    all_data = []
    offset, chunk = 0, 1000
    msg_carga = st.empty()
    
    try:
        while True:
            msg_carga.info(f"⚡ Sincronizando Padrón: {offset:,} registros...")
            res = supabase.table("clientes").select("*").range(offset, offset + chunk - 1).execute()
            if not res.data: break
            all_data.extend(res.data)
            if len(res.data) < chunk: break
            offset += chunk
            
        df = pd.DataFrame(all_data)
        
        # Limpieza de datos crítica
        if not df.empty:
            df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True)
            for col in ['monto', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Guardar copia local para el próximo inicio de sesión
            df.to_parquet(cache_file)
            
        msg_carga.empty()
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()