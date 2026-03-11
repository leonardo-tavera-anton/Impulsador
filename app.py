import streamlit as st
import pandas as pd
from supabase import create_client
import plotly.express as px

# Conexión con Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Impulsador PRO", layout="wide")

# --- LÓGICA DE INTERFAZ ---
st.title("🚀 Sistema Impulsador")
menu = st.sidebar.radio("Navegación", ["Cargar Base", "Dashboard de Tendencias", "Buscador DNI"])

if menu == "Cargar Base":
    st.header("📥 Carga Mensual")
    mes = st.selectbox("Mes", ["Enero", "Febrero", "Marzo", "Abril", "Mayo"])
    yo_filtre = st.toggle("¿Lo filtré yo?", value=True)
    val = 1 if yo_filtre else 0

    archivo = st.file_uploader("Sube Excel o CSV", type=['xlsx', 'csv'])

    if archivo and st.button("Sincronizar Datos"):
        df = pd.read_excel(archivo) if archivo.name.endswith('xlsx') else pd.read_csv(archivo)
        df.columns = df.columns.str.lower().str.strip()
        
        for _, row in df.iterrows():
            dni = str(row['dni']).strip()
            # Recuperar historial previo
            res = supabase.table('clientes').select("historial").eq("dni", dni).execute()
            hist = res.data[0]['historial'] if res.data else {}
            
            # Actualizar mes
            hist[mes.lower()] = val
            
            # Guardar/Actualizar
            supabase.table('clientes').upsert({
                "dni": dni,
                "nombre": row.get('nombre'),
                "monto": float(row.get('monto', 0)),
                "estado": row.get('estado', 'Pendiente'),
                "historial": hist
            }).execute()
        st.success("¡Base actualizada correctamente!")

elif menu == "Dashboard de Tendencias":
    st.header("📊 Análisis de Estados")
    res = supabase.table('clientes').select("estado, monto").execute()
    if res.data:
        df_plot = pd.DataFrame(res.data)
        fig = px.pie(df_plot, names='estado', title="Distribución de tus 40 estados")
        st.plotly_chart(fig)

elif menu == "Buscador DNI":
    dni_busq = st.text_input("Ingresa DNI:")
    if dni_busq:
        res = supabase.table('clientes').select("*").eq("dni", dni_busq).execute()
        if res.data:
            c = res.data[0]
            st.write(f"### {c['nombre']}")
            st.write(f"**Estado:** {c['estado']}")
            st.write("**Historial:**", c['historial'])