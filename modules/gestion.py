import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# --- CONSTANTES ---
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # Estilos para asegurar que la tabla ocupe el ancho y no parpadee
    st.markdown("<style>[data-testid='stDataEditor'] {min-width: 100%;} [data-testid='stBlock'] {opacity: 1 !important;}</style>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 GESTIÓN SURA v7.5</h3>
            <p style='margin:0; opacity:0.8;'>Registros totales: {len(df):,} | Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # --- 1. FILTROS ---
    c1, c2, c3 = st.columns([1, 2, 1])
    
    with c1:
        ano_activo = st.selectbox("📅 Año", [str(a) for a in range(2026, 2031)])

    with c2:
        busqueda = st.text_input("🔍 Buscar por Nombre o DNI", placeholder="Ej: Leonardo...")

    with c3:
        if 'estado' in df.columns:
            estados_unicos = [str(e) for e in df['estado'].unique() if pd.notna(e)]
            lista_estados = sorted(estados_unicos)
        else:
            lista_estados = ["DESEMBOLSADO", "PENDIENTE", "CANCELADO", "OBSERVADO"]
        estado_filtro = st.multiselect("Filtrar Estado", lista_estados)

    # --- 2. LÓGICA DE FILTRADO ---
    mask = pd.Series(True, index=df.index)
    
    if busqueda:
        b = busqueda.lower()
        mask &= (df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False))
    
    if estado_filtro:
        mask &= df['estado'].astype(str).isin(estado_filtro)

    # Límite de 100 registros para evitar lentitud en el navegador
    df_filtered = df[mask].head(100).copy()

    # --- 3. PROCESAMIENTO DE HISTORIAL ---
    def extraer_historial_rapido(h, ano):
        if isinstance(h, dict) and ano in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[ano].items() if v is not None]
        return []

    df_filtered['Historial'] = df_filtered['historial'].apply(lambda h: extraer_historial_rapido(h, ano_activo))
    df_filtered.insert(0, 'N°', range(1, len(df_filtered) + 1))
    
    # --- 4. FUNCIÓN DE AUTOSAVE ---
    def handle_autosave():
        key = f"ed_{ano_activo}"
        if key in st.session_state:
            changes = st.session_state[key].get("edited_rows", {})
            if not changes: return

            payload = []
            for row_idx, modifs in changes.items():
                idx = int(row_idx)
                row_orig = df_filtered.iloc[idx]
                
                # Reconstrucción del JSON de historial
                hist_total = row_orig['historial'] if isinstance(row_orig['historial'], dict) else {}
                
                if 'Historial' in modifs:
                    nueva_lista = modifs['Historial']
                    dic_ano = {}
                    for m_f in MESES_FULL:
                        m_a = m_f[:3]
                        if m_a in nueva_lista: dic_ano[m_f] = 1
                        elif f"🔴 n.{m_a}" in nueva_lista: dic_ano[m_f] = 0
                        else: dic_ano[m_f] = None
                    hist_total[ano_activo] = dic_ano

                # Paquete de datos para Supabase
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
                    st.toast(f"💾 Sincronizado", icon="✅")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")

    # --- 5. EDITOR VISUAL (ORDEN SOLICITADO) ---
    st.data_editor(
        df_filtered[['N°', 'dni', 'nombre', 'celular', 'estado', 'monto', 'deuda', 'Historial']],
        column_config={
            "N°": st.column_config.NumberColumn(width=40),
            "dni": st.column_config.TextColumn("DNI", width=100, disabled=True),
            "nombre": st.column_config.TextColumn("Nombre", width=250, disabled=True),
            "celular": st.column_config.TextColumn("Celular", width=110),
            "estado": st.column_config.SelectboxColumn("Estado", options=lista_estados, width=120),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=90),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=90),
            "Historial": st.column_config.MultiselectColumn(
                f"Pagos {ano_activo}", 
                options=TODAS_LAS_OPCIONES, 
                width=300
            ),
        },
        hide_index=True,
        use_container_width=True,
        key=f"ed_{ano_activo}",
        on_change=handle_autosave
    )

    if len(df[mask]) > 100:
        st.info(f"💡 Se muestran los primeros 100 de {len(df[mask]):,} encontrados. Refina la búsqueda para filtrar más.")