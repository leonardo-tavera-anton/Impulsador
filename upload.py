import pandas as pd
from supabase import create_client
import streamlit as st

url = "https://foyhmgmaexrregnkzjfr.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZveWhtZ21hZXhycmVnbmt6amZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjcxMzQ5NywiZXhwIjoyMDg4Mjg5NDk3fQ.iBS6sZRyl3tcrd1a659ICHRYPu2_GpOf5yw-FVv7Gnw"
supabase = create_client(url, key)

def subir_datos():
    try:
        df = pd.read_excel("padron.xlsx") 
        df = df.fillna(0)
        datos = df.to_dict(orient='records')
        print(f"Subiendo {len(datos)} registros...")
        
        for i in range(0, len(datos), 500):
            lote = datos[i:i+500]
            supabase.table("clientes").insert(lote).execute()
            print(f"Progreso: {i + len(lote)} registros cargados.")
            
        print("¡Éxito total! Todos los datos están en Supabase.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    subir_datos()