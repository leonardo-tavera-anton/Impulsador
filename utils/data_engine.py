import streamlit as st
import pandas as pd
from supabase import create_client
from postgrest.exceptions import APIError

# Configuración de conexión con manejo de errores de secrets
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"Error crítico: No se encontraron las credenciales en secrets.toml o son inválidas. {e}")

@st.cache_data(ttl=600)
def load_sura_core_db(year=None):
    """
    Carga los datos de la tabla 'clientes'. 
    Si no hay datos o falla, devuelve un DataFrame vacío con la estructura necesaria.
    """
    # Definimos la estructura base para que el resto de la app no falle
    columnas_necesarias = ['dni', 'nombre', 'celular', 'monto', 'cuota', 'deuda', 'estado']
    df_vacio = pd.DataFrame(columns=columnas_necesarias)

    try:
        # Intento de consulta a la tabla
        response = supabase.table("clientes").select("*").execute()
        
        # CASO 1: La respuesta es exitosa pero la tabla no existe o no hay datos
        if not response.data:
            # No mostramos error, solo un aviso informativo
            st.info("Aviso: La tabla 'clientes' está vacía. Ve a la pestaña de Importación para cargar datos.")
            return df_vacio
            
        # CASO 2: Procesamiento de datos encontrados
        df = pd.DataFrame(response.data)
        
        # Verificamos que las columnas numéricas existan y las convertimos
        columnas_num = ['monto', 'deuda', 'cuota']
        for col in columnas_num:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                # Si falta una columna numérica, la creamos con ceros para no romper los gráficos
                df[col] = 0.0
                
        return df

    except APIError as e:
        # Error específico de la API de Supabase (ej: tabla no encontrada o permisos)
        st.error(f"Error de API Supabase: {e.message}")
        return df_vacio

    except ConnectionError:
        # Error de internet o firewall
        st.error("Error de red: No se pudo establecer conexión con el servidor de Supabase.")
        return df_vacio

    except Exception as e:
        # Cualquier otro error inesperado
        st.error(f"Error inesperado al cargar datos: {str(e)}")
        return df_vacio

def test_connection():
    """Función rápida para verificar si la llave service_role funciona."""
    try:
        supabase.table("clientes").select("count", count="exact").limit(1).execute()
        return True
    except:
        return False