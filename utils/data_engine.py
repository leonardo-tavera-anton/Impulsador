import streamlit as st
import pandas as pd
from supabase import create_client

# Conexión persistente y cacheada
@st.cache_resource
def get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = get_supabase_client()

@st.cache_data(ttl=3600, show_spinner=False)
def load_sura_core_db():
    """Trae 47k registros de forma eficiente y limpia."""
    all_data = []
    offset = 0
    chunk_size = 1000 
    
    # Placeholder de progreso en el sidebar para no estorbar
    status = st.sidebar.empty()
    
    try:
        while True:
            status.info(f"⏳ Cargando: {offset:,} filas...")
            res = supabase.table("clientes").select("*").range(offset, offset + chunk_size - 1).execute()
            
            if not res.data:
                break
                
            all_data.extend(res.data)
            
            if len(res.data) < chunk_size:
                break
            offset += chunk_size
            
        df = pd.DataFrame(all_data)
        status.empty()

        if not df.empty:
            # LIMPIEZA VECTORIZADA (Mucho más rápida que los bucles for)
            df.columns = [str(c).lower().strip() for c in df.columns]
            
            # Limpieza de DNI
            if 'dni' in df.columns:
                df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
            
            # Conversión numérica masiva
            num_cols = ['monto', 'deuda', 'cuota']
            for col in num_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
            
            # Asegurar columna historial
            if 'historial' not in df.columns:
                df['historial'] = [{} for _ in range(len(df))]

        return df
    except Exception as e:
        st.error(f"❌ Error en Data Engine: {e}")
        return pd.DataFrame()