import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# 1. CONSTANTES GLOBALES
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # --- ESTILOS CSS ---
    st.markdown("<style>[data-testid='stDataEditor'] {min-width: 100%;} .stSelectbox {margin-bottom: 0px;}</style>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 GESTIÓN SURA v7.5 - OPTIMIZADA</h3>
            <p style='margin:0; opacity:0.8;'>Registros totales: {len(df):,} | Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 2. SELECTORES Y FILTROS (CORREGIDO) ---
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        anos_disponibles = [str(a) for a in range(2026, 2031)]
        ano_activo = st.selectbox("📅 Año", anos_disponibles)

    with c2:
        busqueda = st.text_input("🔍 Buscar por Nombre o DNI", placeholder="Ej: Leonardo...")

    with c3:
        # CORRECCIÓN AQUÍ: Evitamos el error de sorted entre float y str
        if 'estado' in df.columns:
            # Convertimos a string y quitamos nulos antes de ordenar
            estados_unicos = [str(e) for e in df['estado'].unique() if pd.notna(e)]
            lista_estados = sorted(estados_unicos)
        else:
            lista_estados = []
        
        estado_filtro = st.multiselect("Filtrar Estado", lista_estados)

    # --- 3. LÓGICA DE FILTRADO ---
    mask = pd.Series(True, index=df.index)
    
    if busqueda:
        b = busqueda.lower()
        mask &= (df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False))
    
    if estado_filtro:
        mask &= df['estado'].astype(str).isin(estado_filtro)

    # Optimizamos: Solo procesamos los primeros 100 para evitar lag
    df_filtered = df[mask].head(100).copy()

    # --- 4. PROCESAMIENTO DE HISTORIAL ---
    def extraer_historial_rapido(h, ano):
        if isinstance(h, dict) and ano in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[ano].items() if v is not None]
        return []

    df_filtered['Historial'] = df_filtered['historial'].apply(lambda h: extraer_historial_rapido(h, ano_activo))
    df_filtered.insert(0, 'N°', range(1, len(df_filtered) + 1))
    
    # --- 5. CALLBACK DE AUTOSAVE ---
    def handle_autosave():
        key = f"ed_{ano_activo}"
        if key in st.session_state:
            changes = st.session_state[key].get("edited_rows", {})
            if not changes: return

            payload = []
            for row_idx, modifs in changes.items():
                # Convertimos row_idx a int para evitar errores de acceso
                idx = int(row_idx)
                row_orig = df_filtered.iloc[idx]
                dni_v = row_orig['dni']
                
                # Reconstrucción del historial JSON
                hist_total = row_orig['historial'] if isinstance(row_orig['historial'], dict) else {}
                
                if 'Historial' in modifs:
                    nueva_lista = modifs['Historial']
                    dic_ano = {}
                    for m_f in MESES_FULL:
                        m_a = m_f[:3]
                        if m_a in nueva_lista: dic_ano[m_f] = 1
                        elif f"🔴 n.{m_a}" in nueva_lista: dic_ano[m_f] = 0
                    
                    hist_total[ano_activo] = dic_ano

                # Preparar datos para Supabase
                payload.append({
                    "dni": dni_v,
                    "historial": hist_total,
                    "estado": str(modifs.get('estado', row_orig['estado'])),
                    "monto": float(modifs.get('monto', row_orig['monto'])),
                    "deuda": float(modifs.get('deuda', row_orig['deuda'])),
                    "celular": str(modifs.get('celular', row_orig['celular']))
                })

            if payload:
                try:
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast(f"💾 Guardado correctamente", icon="✅")
                except Exception as e:
                    st.error(f"Error al sincronizar: {e}")

    # --- 6. EL EDITOR VISUAL ---
    st.data_editor(
        df_filtered[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']],
        column_config={
            "N°": st.column_config.NumberColumn(width=40),
            "dni": st.column_config.TextColumn("DNI", width=100, disabled=True),
            "nombre": st.column_config.TextColumn("Nombre", width=250, disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=lista_estados, width=120),
            "Historial": st.column_config.MultiselectColumn(
                f"Pagos {ano_activo}", 
                options=TODAS_LAS_OPCIONES, 
                width=300
            ),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=90),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=90),
            "celular": st.column_config.TextColumn("Celular", width=110),
        },
        hide_index=True,
        use_container_width=True,
        key=f"ed_{ano_activo}",
        on_change=handle_autosave
    )

    if len(df[mask]) > 100:
        st.warning(f"⚠️ Mostrando los primeros 100 resultados de {len(df[mask]):,}. Refina la búsqueda si no encuentras a alguien.")