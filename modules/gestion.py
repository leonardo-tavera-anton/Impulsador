import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# 1. CONSTANTES GLOBALES
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # --- ESTILOS CSS PARA MODO EXCEL ---
    st.markdown("""
        <style>
        [data-testid='stDataEditor'] { min-width: 100%; }
        /* Forzamos una altura mayor para el scroll tipo Excel */
        [data-testid="stDataEditor"] > div:first-child { height: 600px !important; }
        .stSelectbox { margin-bottom: 0px; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 LISTADO MAESTRO SURA v7.5</h3>
            <p style='margin:0; opacity:0.8;'>Modo Hoja de Cálculo | Registros: {len(df):,}</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 2. FILTROS ---
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        ano_activo = st.selectbox("📅 Año Fiscal", [str(a) for a in range(2026, 2031)])

    with c2:
        busqueda = st.text_input("🔍 Filtro de búsqueda (DNI o Nombre)", placeholder="Escribe para buscar instantáneamente...")

    with c3:
        if 'estado' in df.columns:
            estados_unicos = [str(e) for e in df['estado'].unique() if pd.notna(e)]
            lista_estados = sorted(estados_unicos)
        else:
            lista_estados = []
        estado_filtro = st.multiselect("Filtrar por Estado", lista_estados)

    # --- 3. LÓGICA DE FILTRADO (SIN LÍMITE DE 100) ---
    mask = pd.Series(True, index=df.index)
    
    if busqueda:
        b = busqueda.lower()
        mask &= (df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False))
    
    if estado_filtro:
        mask &= df['estado'].astype(str).isin(estado_filtro)

    # Cargamos el DataFrame completo filtrado
    df_filtered = df[mask].copy()

    # --- 4. PROCESAMIENTO DE HISTORIAL ---
    def extraer_historial_rapido(h, ano):
        if isinstance(h, dict) and ano in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[ano].items() if v is not None]
        return []

    # Transformación eficiente
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
                idx = int(row_idx)
                row_orig = df_filtered.iloc[idx]
                
                # Reconstrucción del historial
                hist_total = row_orig['historial'] if isinstance(row_orig['historial'], dict) else {}
                
                if 'Historial' in modifs:
                    nueva_lista = modifs['Historial']
                    dic_ano = {m_f: (1 if m_f[:3] in nueva_lista else (0 if f"🔴 n.{m_f[:3]}" in nueva_lista else None)) for m_f in MESES_FULL}
                    hist_total[ano_activo] = dic_ano

                payload.append({
                    "dni": row_orig['dni'],
                    "historial": hist_total,
                    "estado": str(modifs.get('estado', row_orig['estado'])),
                    "monto": float(modifs.get('monto', row_orig['monto'])),
                    "deuda": float(modifs.get('deuda', row_orig['deuda'])),
                    "celular": str(modifs.get('celular', row_orig['celular']))
                })

            if payload:
                try:
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast("✅ Cambios guardados", icon="💾")
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- 6. EL EDITOR VISUAL (INFINITO) ---
    st.data_editor(
        df_filtered[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']],
        column_config={
            "N°": st.column_config.NumberColumn(width=50, disabled=True),
            "dni": st.column_config.TextColumn("DNI", width=120, disabled=True),
            "nombre": st.column_config.TextColumn("Nombre completo", width=300, disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=lista_estados, width=150),
            "Historial": st.column_config.MultiselectColumn(
                f"Pagos {ano_activo}", 
                options=TODAS_LAS_OPCIONES, 
                width=350
            ),
            "monto": st.column_config.NumberColumn("Monto S/", format="%.2f"),
            "deuda": st.column_config.NumberColumn("Deuda S/", format="%.2f"),
            "celular": st.column_config.TextColumn("Celular"),
        },
        hide_index=True,
        use_container_width=True,
        key=f"ed_{ano_activo}",
        on_change=handle_autosave
    )