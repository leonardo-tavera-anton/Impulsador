import streamlit as st
import pandas as pd
import requests
import re

st.set_page_config(page_title="Impulsador PRO", layout="wide")

# Conexión manual a Supabase
URL = st.secrets["SUPABASE_URL"]
KEY = st.secrets["SUPABASE_KEY"]
HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal, resolution=merge-duplicates"
}

def limpiar_monto(valor):
    """Limpia símbolos como 'S/' y convierte a número."""
    if pd.isna(valor): return 0.0
    texto = str(valor).replace('S/', '').replace(',', '').strip()
    try:
        return float(re.findall(r"[-+]?\d*\.\d+|\d+", texto)[0])
    except:
        return 0.0

# --- BARRA LATERAL ---
st.sidebar.title("Configuración")
try:
    test = requests.get(f"{URL}/rest/v1/clientes?limit=1", headers=HEADERS)
    if test.status_code in [200, 201, 204]:
        st.sidebar.success("✅ Supabase Conectado")
except:
    st.sidebar.error("❌ Error de Conexión")

menu = st.sidebar.radio("Navegación", ["Cargar Base", "Buscador DNI"])

if menu == "Cargar Base":
    st.header("📥 Sincronización de Datos")
    mes = st.selectbox("Selecciona Mes de Carga", ["enero", "febrero", "marzo", "abril", "mayo"])
    archivo = st.file_uploader("Sube tu Excel (Leo Base Total)", type=['xlsx'])

    if archivo and st.button("Iniciar Sincronización"):
        df = pd.read_excel(archivo)
        df.columns = df.columns.str.lower().str.strip()
        
        progreso = st.progress(0)
        status = st.empty()
        
        for i, row in df.iterrows():
            dni = str(row.get('dni', '')).split('.')[0].strip()
            if not dni or dni == 'nan': continue
            
            # Limpieza de datos del Excel
            monto = limpiar_monto(row.get('monto', 0))
            cuota = limpiar_monto(row.get('cuota', 0))
            deuda = limpiar_monto(row.get('deuda', 0))
            
            # Obtener historial actual
            get_res = requests.get(f"{URL}/rest/v1/clientes?dni=eq.{dni}&select=historial", headers=HEADERS)
            hist = get_res.json()[0].get('historial', {}) if (get_res.status_code == 200 and get_res.json()) else {}
            
            # Actualizar historial
            hist[mes] = 1
            
            payload = {
                "dni": dni,
                "nombre": str(row.get('nombre', 'Sin nombre')),
                "monto": monto,
                "cuota": cuota,
                "deuda": deuda,
                "estado": str(row.get('estado', 'Pendiente')),
                "historial": hist
            }
            
            requests.post(f"{URL}/rest/v1/clientes", headers=HEADERS, json=payload)
            progreso.progress((i + 1) / len(df))
            status.text(f"Sincronizando fila {i+1} de {len(df)}...")
            
        st.success(f"¡Base de {mes} cargada correctamente!")

elif menu == "Buscador DNI":
    dni_busq = st.text_input("Ingrese DNI para consultar:")
    if dni_busq:
        res = requests.get(f"{URL}/rest/v1/clientes?dni=eq.{dni_busq}", headers=HEADERS)
        data = res.json()
        if data:
            c = data[0]
            st.subheader(f"👤 {c['nombre']}")
            col1, col2, col3 = st.columns(3)
            col1.metric("Monto", f"S/ {c['monto']}")
            col2.metric("Cuota", f"S/ {c['cuota']}")
            col3.metric("Deuda", f"S/ {c['deuda']}", delta_color="inverse")
            st.info(f"**Estado:** {c['estado']}")
            st.write("**Historial de Cargas:**", c['historial'])
        else:
            st.warning("DNI no encontrado.")