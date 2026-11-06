"""Genera los PDF de los informes (Edge headless) y la versión web del informe del Módulo 5.

Uso: python _fuentes/build.py   (desde la raíz del repositorio)

Las imágenes pesadas se pasan a JPEG (calidad 82, máx. 1600 px de ancho) sólo para el PDF,
así los informes quedan livianos y el visor de GitHub los puede mostrar.
"""
import pathlib
import re
import subprocess

from PIL import Image

RAIZ = pathlib.Path(__file__).resolve().parent.parent
F = RAIZ / "_fuentes"
TMP = F / "_tmp"  # ignorado por git: se regenera en cada corrida
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
SALIDAS = {
    "informe_m1.html": "Modulo 1/M1 - TyHMII - Seleccion del enfoque tecnologico - SatellAgro.pdf",
    "informe_m2.html": "Modulo 2/M2 - TyHMII - Plan del piloto SatellAgro 2026-27.pdf",
    "informe_m3.html": "Modulo 3/M3 - TyHMII - Analisis pericial de imagen satelital.pdf",
    "informe_m4.html": "Modulo 4/M4 - TyHMII - SIG de la zona piloto Agrelo.pdf",
    "informe_m5.html": "Modulo 5/M5 - TyHMII - Dinamica de sistemas - Difusion de SatellAgro.pdf",
}
TMP.mkdir(exist_ok=True)
(TMP / "informe.css").write_text((F / "informe.css").read_text(encoding="utf8"), encoding="utf8")


def a_jpeg(m):
    rel = m.group(1)
    origen = (F / rel).resolve()
    if origen.stat().st_size < 300_000:
        return f'src="{origen.as_uri()}"'
    im = Image.open(origen).convert("RGB")
    if im.width > 1600:
        im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
    destino = TMP / (origen.stem + ".jpg")
    im.save(destino, quality=82, optimize=True)
    return f'src="{destino.name}"'


for src, dst in SALIDAS.items():
    html = (F / src).read_text(encoding="utf8")
    html = re.sub(r'src="(\.\./[^"]+\.png)"', a_jpeg, html)
    tmp_html = TMP / src
    tmp_html.write_text(html, encoding="utf8")
    out = RAIZ / dst
    if out.exists():
        out.unlink()
    subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--virtual-time-budget=8000",
                    f"--print-to-pdf={out}", tmp_html.as_uri()], check=True, capture_output=True, timeout=120)
    print(f"{dst}: {out.stat().st_size // 1024} KB")

# versión web del informe del Módulo 5 (autocontenida en su carpeta, CSS embebido)
html = (F / "informe_m5.html").read_text(encoding="utf8")
css = (F / "informe.css").read_text(encoding="utf8")
html = html.replace('<link rel="stylesheet" href="informe.css">', f"<style>\n{css}\n</style>")
html = html.replace("../Modulo 5/figuras/", "figuras/")
(RAIZ / "Modulo 5" / "Informe_M5.html").write_text(html, encoding="utf8")
print("Modulo 5/Informe_M5.html")
