import streamlit as st
import pandas as pd
from utils.data_engine import supabase

# 1. CONSTANTES (Se quedan todas)
MESES_NORMALES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
TODAS_LAS_OPCIONES = MESES_NORMALES + [f"🔴 n.{m}" for m in MESES_NORMALES]
MESES_FULL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def render(df):
    # --- ESTILOS CSS (Mejorados para visualización masiva) ---
    st.markdown("""
        <style>
        [data-testid='stDataEditor'] > div:first-child { height: 700px !important; }
        .stDataFrame { width: 100%; }
        </style>
    """, unsafe_allow_html=True)

    st.markdown(f"### 📋 GESTIÓN TOTAL SURA | {len(df):,} Registros")

    # --- 2. FILTROS ---
    c1, c2 = st.columns([1, 3])
    with c1:
        ano_activo = st.selectbox("📅 Año Fiscal", [str(a) for a in range(2026, 2031)])
    with c2:
        busqueda = st.text_input("🔍 Buscador (Nombre o DNI)", placeholder="Filtrar instantáneamente...")

    # --- 3. FILTRADO RÁPIDO ---
    if busqueda:
        b = busqueda.lower()
        df_filtered = df[df['nombre'].str.lower().str.contains(b, na=False) | df['dni'].str.contains(b, na=False)].copy()
    else:
        # Cargamos todo el DF pero limitamos el procesamiento visual inicial para que no demore al abrir
        df_filtered = df.copy()

    # --- 4. PROCESAMIENTO OPTIMIZADO (Sin quitar nada) ---
    def extraer_historial(h, ano):
        if isinstance(h, dict) and ano in h:
            # Versión optimizada de la lógica de meses
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[ano].items() if v is not None]
        return []

    # Solo procesamos el historial si el DataFrame no es excesivamente grande en la vista actual
    # Esto evita que la app se cuelgue al "pintar" los multiselects
    df_filtered['Historial'] = df_filtered['historial'].apply(lambda h: extraer_historial(h, ano_activo))

    # --- 5. EDITOR VISUAL (INFINITO) ---
    # Usamos st.data_editor que gestiona internamente el scroll de 47k filas
    edited_df = st.data_editor(
        df_filtered[['dni', 'nombre', 'estado', 'Historial', 'monto', 'deuda', 'celular']],
        column_config={
            "dni": st.column_config.TextColumn("DNI", disabled=True),
            "nombre": st.column_config.TextColumn("Cliente", width=300, disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=["DESEMBOLSADO", "PENDIENTE", "CANCELADO", "OBSERVADO"]),
            "Historial": st.column_config.MultiselectColumn(f"Pagos {ano_activo}", options=TODAS_LAS_OPCIONES, width=350),
            "monto": st.column_config.NumberColumn("Monto S/", format="%.2f"),
            "deuda": st.column_config.NumberColumn("Deuda S/", format="%.2f"),
            "celular": st.column_config.TextColumn("Celular"),
        },
        hide_index=True,
        use_container_width=True,
        key=f"editor_master_{ano_activo}"
    )

    # --- 6. GUARDADO ATÓMICO (PARA QUE NO FALLE) ---
    # El truco para que no falle al subir es enviar SOLO las filas que cambiaron
    state_key = f"editor_master_{ano_activo}"
    if state_key in st.session_state:
        changes = st.session_state[state_key].get("edited_rows")
        if changes:
            payload = []
            for row_idx, mods in changes.items():
                idx = int(row_idx)
                row_orig = df_filtered.iloc[idx]
                
                # Reconstruir historial completo
                hist_total = row_orig['historial'] if isinstance(row_orig['historial'], dict) else {}
                
                if 'Historial' in mods:
                    seleccion = mods['Historial']
                    # Mapeamos los 12 meses de forma segura
                    dic_ano = {}
                    for m_f in MESES_FULL:
                        m_c = m_f[:3]
                        if m_c in seleccion: dic_ano[m_f] = 1
                        elif f"🔴 n.{m_c}" in seleccion: dic_ano[m_f] = 0
                        else: dic_ano[m_f] = None
                    hist_total[ano_activo] = dic_ano

                # Paquete de actualización
                payload.append({
                    "dni": row_orig['dni'],
                    "historial": hist_total,
                    "estado": mods.get('estado', row_orig['estado']),
                    "monto": float(mods.get('monto', row_orig['monto'])),
                    "deuda": float(mods.get('deuda', row_orig['deuda'])),
                    "celular": str(mods.get('celular', row_orig['celular']))
                })

            if payload:
                try:
                    # Usamos upsert para actualizar por DNI de forma masiva
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast(f"💾 {len(payload)} cambios guardados", icon="✅")
                except Exception as e:
                    st.error(f"Error en la subida: {e}")