import streamlit as st
import pandas as pd
from supabase import create_client

# Conexión Segura
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

def load_sura_core_db(year=None):
    """Bucle de paginación para traer los 6,952 registros."""
    all_data = []
    offset = 0
    chunk_size = 1000 # Supabase entrega máximo 1000 por vez
    
    try:
        while True:
            # Pedimos el rango actual (0-999, 1000-1999, etc.)
            res = supabase.table("clientes").select("*").range(offset, offset + chunk_size - 1).execute()
            if not res.data:
                break
            all_data.extend(res.data)
            if len(res.data) < chunk_size: # Si trajo menos de 1000, terminamos
                break
            offset += chunk_size
            
        df = pd.DataFrame(all_data)
        
        # Limpieza rápida para el editor
        for col in ['monto', 'deuda', 'cuota']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Normalizar meses para checkboxes
        for m in ['Mar', 'Abr', 'May']:
            if m in df.columns:
                df[m] = df[m].apply(lambda x: True if str(x).lower() in ['1', '1.0', 'si', 'true'] else False)
            else:
                df[m] = False
        return df
    except Exception as e:
        st.error(f"Error en Data Engine: {e}")
        return pd.DataFrame()