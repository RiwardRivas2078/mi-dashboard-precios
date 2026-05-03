#!/usr/bin/env python3
import subprocess
import sys
import os

def run_scraper(script_name):
    # Esto fuerza a Python a buscar el archivo en la misma carpeta donde está este script
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), script_name)
    
    print(f"🚀 Intentando ejecutar: {script_path}")
    
    if not os.path.exists(script_path):
        print(f"❌ ERROR CRÍTICO: El archivo {script_name} no existe en la raíz del repo.")
        return False

    result = subprocess.run([sys.executable, script_path, "--headless"])
    
    if result.returncode == 0:
        print(f"✅ {script_name} completado con éxito.")
        return True
    else:
        print(f"❌ {script_name} falló con código de salida {result.returncode}")
        return False

if __name__ == "__main__":
    print("--- Iniciando proceso de scraping ---")
    ok1 = run_scraper("scraper_gamma.py")
    ok2 = run_scraper("scraper_plansuarez.py")
    
    if ok1 and ok2:
        print("🎉 ¡Victoria! Todos los scrapers finalizaron correctamente.")
    else:
        print("⚠️ Proceso terminado con errores parciales.")
        sys.exit(1)
