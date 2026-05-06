import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def get_supabase():
    """Conexión única a Supabase."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = get_supabase()

@st.cache_data(ttl=600)
def load_sura_core_db():
    """Carga inicial de la base de datos."""
    try:
        res = supabase.table("clientes").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Limpieza de DNI para evitar decimales .0
            df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame()