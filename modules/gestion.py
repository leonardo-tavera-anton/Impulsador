import streamlit as st
import pandas as pd
from utils.data_engine import supabase

def render(df):
    # CSS para que se vea como Excel y no se corte
    st.markdown("<style>[data-testid='stDataEditor'] > div:first-child { height: 650px !important; }</style>", unsafe_allow_html=True)

    # Filtros rápidos
    c1, c2 = st.columns([1, 3])
    with c1:
        ano = st.selectbox("Año", [str(a) for a in range(2026, 2031)], key="sel_ano")
    with c2:
        query = st.text_input("🔍 Buscador Maestro (DNI o Nombre)", key="main_search")

    # Filtrado ultra-rápido en memoria
    if query:
        q = query.lower()
        df_final = df[df['nombre'].str.lower().str.contains(q, na=False) | df['dni'].str.contains(q, na=False)].copy()
    else:
        # Si no hay búsqueda, mostramos una muestra grande pero manejable
        df_final = df.head(500).copy()

    # Procesar historial SOLO para lo que se va a mostrar
    def fast_hist(h, a):
        if isinstance(h, dict) and a in h:
            return [m[:3] if v == 1 else f"🔴 n.{m[:3]}" for m, v in h[a].items() if v is not None]
        return []

    df_final['Pagos'] = df_final['historial'].apply(lambda x: fast_hist(x, ano))

    # Editor tipo Excel
    edited_df = st.data_editor(
        df_final[['dni', 'nombre', 'estado', 'Pagos', 'monto', 'deuda', 'celular']],
        column_config={
            "dni": st.column_config.TextColumn("DNI", disabled=True),
            "nombre": st.column_config.TextColumn("Cliente", width=300, disabled=True),
            "estado": st.column_config.SelectboxColumn("Estado", options=["DESEMBOLSADO", "PENDIENTE", "CANCELADO"]),
            "Pagos": st.column_config.MultiselectColumn("Meses", options=["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]),
            "monto": st.column_config.NumberColumn("Monto", format="%.2f"),
        },
        hide_index=True,
        use_container_width=True,
        key="editor_padrón"
    )

    # GUARDADO OPTIMIZADO (Solo lo que cambió)
    state_key = "editor_padrón"
    if state_key in st.session_state:
        changes = st.session_state[state_key].get("edited_rows")
        if changes:
            payload = []
            for row_idx, mods in changes.items():
                # Obtenemos la data original de la fila editada
                real_row = df_final.iloc[int(row_idx)]
                
                # Actualizar historial si cambió
                new_h = real_row['historial'] if isinstance(real_row['historial'], dict) else {}
                if 'Pagos' in mods:
                    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
                    new_h[ano] = {m: (1 if m[:3] in mods['Pagos'] else 0) for m in meses}

                payload.append({
                    "dni": real_row['dni'],
                    "historial": new_h,
                    "estado": mods.get('estado', real_row['estado']),
                    "monto": float(mods.get('monto', real_row['monto'])),
                    "deuda": float(mods.get('deuda', real_row['deuda'])),
                    "celular": str(mods.get('celular', real_row['celular']))
                })

            if payload:
                try:
                    supabase.table("clientes").upsert(payload).execute()
                    st.toast("✅ Guardado en Supabase", icon="💾")
                except Exception as e:
                    st.error(f"Error al guardar: {e}")