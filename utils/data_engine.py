import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def get_supabase():
    """Establece la conexión con la base de datos."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=600)
def load_sura_core_db():
    """Carga los 47k registros de forma masiva."""
    try:
        res = supabase.table("clientes").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if not df.empty:
            # Limpieza: Evitar que el DNI se vea como flotante (ej: 455.0)
            df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True)
            # Asegurar que el historial sea un diccionario válido
            df['historial'] = df['historial'].apply(lambda x: x if isinstance(x, dict) else {})
            # Formatear números
            for col in ['monto', 'deuda']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0)
        return df
    except Exception as e:
        st.error(f"Error al conectar con Supabase: {e}")
        return pd.DataFrame()