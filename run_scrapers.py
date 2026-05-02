#!/usr/bin/env python3
"""
Ejecuta ambos scrapers automáticamente (Gamma y Plan Suárez)
"""

import subprocess
import sys

def run_scraper(script_name):
    print(f"🚀 Ejecutando {script_name}...")
    # Se usa sys.executable para asegurar que use el mismo Python de GitHub
    result = subprocess.run([sys.executable, script_name, "--headless"])
    if result.returncode == 0:
        print(f"✅ {script_name} completado")
        return True
    else:
        print(f"❌ Error en {script_name}")
        return False

if __name__ == "__main__":
    ok1 = run_scraper("scraper_gamma.py")
    ok2 = run_scraper("scraper_plansuarez.py")
    if ok1 and ok2:
        print("🎉 Todos los scrapers finalizaron correctamente")
    else:
        print("⚠️ Hubo errores")
        sys.exit(1)
