"""Genera los PDF de los informes (Edge headless) y la versión web del informe del Módulo 5.

Uso: python _fuentes/build.py   (desde la raíz del repositorio)
"""
import os
import pathlib
import re
import subprocess

RAIZ = pathlib.Path(__file__).resolve().parent.parent
F = RAIZ / "_fuentes"
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SALIDAS = {
    "informe_m1.html": "Modulo 1/M1 - TyHMII - Seleccion del enfoque tecnologico - SatellAgro.pdf",
    "informe_m2.html": "Modulo 2/M2 - TyHMII - Plan del piloto SatellAgro 2026-27.pdf",
    "informe_m3.html": "Modulo 3/M3 - TyHMII - Analisis pericial de imagen satelital.pdf",
    "informe_m4.html": "Modulo 4/M4 - TyHMII - SIG de la zona piloto Agrelo.pdf",
    "informe_m5.html": "Modulo 5/M5 - TyHMII - Dinamica de sistemas - Difusion de SatellAgro.pdf",
}

for src, dst in SALIDAS.items():
    out = RAIZ / dst
    if out.exists():
        out.unlink()
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={out}", (F / src).as_uri()], check=True, capture_output=True, timeout=120)
    print(f"{dst}: {out.stat().st_size // 1024} KB")

# versión web del informe del Módulo 5 (autocontenida en su carpeta, CSS embebido)
html = (F / "informe_m5.html").read_text(encoding="utf8")
css = (F / "informe.css").read_text(encoding="utf8")
html = html.replace('<link rel="stylesheet" href="informe.css">', f"<style>\n{css}\n</style>")
html = html.replace("../Modulo 5/figuras/", "figuras/")
(RAIZ / "Modulo 5" / "Informe_M5.html").write_text(html, encoding="utf8")
print("Modulo 5/Informe_M5.html")
