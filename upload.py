import pandas as pd
from supabase import create_client
import json

# Configuración de conexión
URL = "https://foyhmgmaexrregnkzjfr.supabase.co"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZveWhtZ21hZXhycmVnbmt6amZyIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MjcxMzQ5NywiZXhwIjoyMDg4Mjg5NDk3fQ.iBS6sZRyl3tcrd1a659ICHRYPu2_GpOf5yw-FVv7Gnw"
supabase = create_client(URL, KEY)

def preparar_historial_vacio():
    """Crea una estructura de historial básica para los años 2026-2030."""
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
              "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    # Por defecto, todos los meses están vacíos (None)
    estructura = {str(anio): {mes: None for mes in meses} for anio in range(2026, 2031)}
    return estructura

def subir_datos():
    try:
        print("📖 Leyendo padron.xlsx...")
        # Leemos el Excel
        df = pd.read_excel("padron.xlsx") 
        
        # --- LIMPIEZA DE DATOS ---
        # Aseguramos que el DNI sea string y no tenga .0
        df['dni'] = df['dni'].astype(str).str.replace(r'\.0$', '', regex=True)
        
        # Llenamos nulos en celular, estado, monto y deuda
        df['celular'] = df['celular'].fillna("").astype(str)
        df['estado'] = df['estado'].fillna("PENDIENTE").astype(str)
        df['monto'] = pd.to_numeric(df['monto'], errors='coerce').fillna(0.0)
        df['deuda'] = pd.to_numeric(df['deuda'], errors='coerce').fillna(0.0)
        
        # Si el Excel no tiene la columna historial, la creamos vacía
        if 'historial' not in df.columns:
            hist_base = preparar_historial_vacio()
            df['historial'] = [hist_base for _ in range(len(df))]
        
        datos = df.to_dict(orient='records')
        total = len(datos)
        print(f"🚀 Iniciando subida de {total} registros...")
        
        # --- SUBIDA POR LOTES (BATCH) ---
        batch_size = 500
        for i in range(0, total, batch_size):
            lote = datos[i:i + batch_size]
            
            # Usamos upsert por si el DNI ya existe, que lo actualice en lugar de dar error
            supabase.table("clientes").upsert(lote).execute()
            
            porcentaje = (i + len(lote)) / total * 100
            print(f"✅ Progreso: {i + len(lote)}/{total} ({porcentaje:.1f}%)")
            
        print("\n¡Éxito total! El padrón de Nuevo Chimbote está sincronizado.")
        
    except FileNotFoundError:
        print("❌ Error: No se encontró el archivo 'padron.xlsx' en esta carpeta.")
    except Exception as e:
        print(f"❌ Error inesperado: {e}")

if __name__ == "__main__":
    subir_datos()