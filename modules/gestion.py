import streamlit as st
import requests
import time
from datetime import datetime

def render(df_core):
    URL = st.secrets["SUPABASE_URL"]
    HEADERS = {"apikey": st.secrets["SUPABASE_KEY"], "Authorization": f"Bearer {st.secrets['SUPABASE_KEY']}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates"}
    
    st.markdown("<h1 class='sura-title'>GESTIÓN OPERATIVA</h1>", unsafe_allow_html=True)
    search = st.text_input("🔍 Localizar por DNI o Nombre:").upper()
    df_f = df_core[df_core['nombre'].str.contains(search, na=False) | df_core['dni'].str.contains(search)]

    selection = st.dataframe(
        df_f[["dni", "nombre", "monto", "cuota", "deuda", "estado", "ENE", "FEB", "MAR"]],
        use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row", key="table_gest"
    )

    if len(selection.selection.rows) > 0:
        sel = df_f.iloc[selection.selection.rows[0]]
        with st.form("edit_form"):
            c1, c2, c3 = st.columns(3)
            new_nom = c1.text_input("Nombre", value=sel['nombre'])
            new_est = c2.selectbox("Estado", st.session_state.custom_estados, index=st.session_state.custom_estados.index(sel['estado']) if sel['estado'] in st.session_state.custom_estados else 0)
            new_mon = c3.number_input("Monto", value=float(sel['monto']))
            
            if st.form_submit_button("💾 GUARDAR CAMBIOS"):
                payload = {"dni": str(sel['dni']), "nombre": new_nom.upper(), "estado": new_est, "monto": new_mon}
                res = requests.post(f"{URL}/rest/v1/clientes", headers=HEADERS, json=[payload])
                if res.status_code in [200, 201, 204]:
                    st.success("Sincronizado.")
                    st.cache_data.clear()
                    time.sleep(1)
                    st.rerun()