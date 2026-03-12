import streamlit as st
import pandas as pd
from supabase import create_client

# Usa tus credenciales de Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

@st.cache_data(ttl=600)
def load_sura_core_db(year):
    try:
        # IMPORTANTE: El nombre debe ser 'clientes' como en tu SQL
        response = supabase.table("clientes").select("*").execute()
        data = response.data
        
        if not data:
            return pd.DataFrame() # Aquí es donde salta el "Esperando conexión..."
            
        df = pd.DataFrame(data)
        
        # Forzamos tipos numéricos para que tus 10 gráficos no fallen
        for col in ['monto', 'deuda', 'cuota']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión: {str(e)}")
        return pd.DataFrame()