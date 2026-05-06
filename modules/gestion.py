import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# Constantes optimizadas
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # 1. CSS COMPACTO
    st.markdown("<style>[data-testid='stDataEditor'] {min-width: 100%;} .stSelectbox {margin-bottom: 0px;}</style>", unsafe_allow_html=True)

    st.markdown(f"""
        <div style="background: linear-gradient(90deg, #1e3a8a, #3b82f6); padding:15px; border-radius:10px; color:white; margin-bottom:15px;">
            <h3 style='margin:0;'>📋 GESTIÓN SURA v7.5 - OPTIMIZADA</h3>
            <p style='margin:0; opacity:0.8;'>Registros: {len(df):,} | Nuevo Chimbote 2026</p>
        </div>
    """, unsafe_allow_html=True)

    # 2. SELECTORES Y FILTROS
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        ano_activo = st.selectbox("📅 Año", [str(a) for a in range(2026, 2035)])
    with c2:
        busqueda = st.text_input("🔍 Buscar por Nombre o DNI", placeholder="Ej: Leonardo...")
    with c3:
        lista_estados = sorted(df['estado'].unique().tolist()) if 'estado' in df.columns else []
        estado_filtro = st.multiselect("Filtrar", lista_estados)

    # --- LÓGICA DE FILTRADO (Vuelo sin motor) ---
    # Trabajamos sobre una vista, no una copia completa todavía
    mask = pd.Series(True, index=df.index)
    
    if busqueda:
        b = busqueda.lower()
        mask &= (df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False))
    
    if estado_filtro:
        mask &= df['estado'].isin(estado_filtro)

    # OPTIMIZACIÓN CLAVE: Solo procesamos los primeros 100 resultados
    # Renderizar 47k de historial en el MultiselectColumn mataría el navegador.
    df_filtered = df[mask].head(100).copy()

    # 3. PROCESAMIENTO SOLO DE LO VISIBLE
    def extraer_historial_rapido(h, ano):
        if isinstance(h, dict) and ano in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[ano].items()]
        return []

    df_filtered['Historial'] = df_filtered['historial'].apply(lambda h: extraer_historial_rapido(h, ano_activo))
    df_filtered.insert(0, 'N°', range(1, len(df_filtered) + 1))
    
    # 4. CALLBACK DE GUARDADO (Autosave masivo)
    def handle_autosave():
        key = f"ed_{ano_activo}"
        if key in st.session_state:
            changes = st.session_state[key].get("edited_rows", {})
            if not changes: return

            payload = []
            for row_idx, modifs in changes.items():
                row_orig = df_filtered.iloc[int(row_idx)]
                dni_v = row_orig['dni']
                
                # Reconstrucción del historial
                hist_total = row_orig['historial'] if isinstance(row_orig['historial'], dict) else {}
                if 'Historial' in modifs:
                    nueva_lista = modifs['Historial']
                    dic_ano = {m: (1 if m[:3] in nueva_lista else 0 if f"🔴 n.{m[:3]}" in nueva_lista else None) for m in MESES_FULL}
                    # Limpiamos los None (meses no marcados)
                    hist_total[ano_activo] = {k: v for k, v in dic_ano.items() if v is not None}

                payload.append({
                    "dni": dni_v,
                    "historial": hist_total,
                    "estado": modifs.get('estado', row_orig['estado']),
                    "monto": float(modifs.get('monto', row_orig['monto'])),
                    "deuda": float(modifs.get('deuda', row_orig['deuda'])),
                    "celular": str(modifs.get('celular', row_orig['celular']))
                })

            if payload:
                try:
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast(f"💾 Guardado: {dni_v}", icon="✅")
                except Exception as e:
                    st.error(f"Error: {e}")

    # 5. EL EDITOR (Corazón de la App)
    st.data_editor(
        df_filtered[['N°', 'dni', 'nombre', 'celular', 'estado', 'Historial', 'monto', 'deuda']],
        column_config={
            "N°": st.column_config.NumberColumn(width=40),
            "dni": st.column_config.TextColumn("DNI", width=100, disabled=True),
            "nombre": st.column_config.TextColumn("Nombre", width=250, disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=lista_estados, width=120),
            "Historial": st.column_config.MultiselectColumn(f"Pagos {ano_activo}", options=TODAS_LAS_OPCIONES, width=300),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f", width=90),
            "deuda": st.column_config.NumberColumn("Deuda", format="%.2f", width=90),
        },
        hide_index=True,
        use_container_width=True,
        key=f"ed_{ano_activo}",
        on_change=handle_autosave
    )

    if len(df[mask]) > 100:
        st.warning(f"⚠️ Mostrando 100 de {len(df[mask])} resultados. Refina tu búsqueda para ver más.")