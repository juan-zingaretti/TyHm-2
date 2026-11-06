"""Módulo 5: escenarios, pruebas STEP y sensibilidad del modelo de difusión de SatellAgro.

Uso: python analisis_m5.py <carpeta_figuras>
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from modelo_guerrilla import DT, ESCENARIOS, indicadores, simular

FIG = sys.argv[1]
os.makedirs(FIG, exist_ok=True)
COL = ["#2e7d32", "#f9a825", "#c62828", "#6d4c41", "#1565c0"]
res = {"escenarios": {}, "presentacion": {
    "Guerrilla calibrada (10 % falsas alarmas)": [1.4, 8, 82, 0.90, 0.77, -1649],
    "Guerrilla sin calibrar (30 %)": [1.3, 7, 43, 0.84, 0.54, -3455],
    "Zumbido: alerta en cada imagen": [1.4, 8, 46, 0.58, 0.70, -3855],
    "Contacto en frío": [1.0, 2, 14, 0.88, 0.41, -4396],
    "1 reunión por semana, calibrada": [5.3, 30, 181, 0.87, 0.83, 2433]}}


def sem_a_fecha(ax):
    ax.set_xticks([0, 8.5, 17, 26, 34.7, 43.4, 52, 60.7, 69.3, 78],
                  ["nov-26", "ene-27", "mar-27", "may-27", "jul-27", "sep-27", "nov-27", "ene-28", "mar-28", "abr-28"],
                  fontsize=8)
    ax.axvspan(4, 22, color="#fff3e0", zorder=0); ax.axvspan(56, 74, color="#fff3e0", zorder=0)
    ax.grid(alpha=.3)


# 1. cinco tácticas
runs = {n: simular(c) for n, c in ESCENARIOS.items()}
for n, (t, r) in runs.items():
    res["escenarios"][n] = indicadores(t, r)
fig, axs = plt.subplots(2, 2, figsize=(12, 7.6))
axs = axs.ravel()
for (n, (t, r)), c in zip(runs.items(), COL):
    axs[0].plot(t, r["Suscriptos"], color=c, label=n, lw=2)
    axs[1].plot(t, r["Reputación"], color=c, lw=2)
    axs[2].plot(t, r["Resultado acumulado"], color=c, lw=2)
    axs[3].plot([], [], color=c, lw=3, label=n)
for a, ti, yl in zip(axs[:3], ("Suscriptos", "Reputación", "Resultado acumulado"), ("regantes", "0–1", "USD")):
    a.set_title(ti); a.set_ylabel(yl); sem_a_fecha(a)
axs[2].axhline(0, color="k", lw=.8)
axs[3].axis("off"); axs[3].legend(fontsize=11, frameon=False, loc="center", title="Táctica", title_fontsize=11)
fig.suptitle("Cinco tácticas con los mismos supuestos (franja naranja = temporada dic–mar)", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "01_cinco_tacticas.png"), dpi=140); plt.close(fig)

# 2. embudo del escenario recomendado
t, r = runs["Guerrilla calibrada (10 % falsas alarmas)"]
fig, ax = plt.subplots(figsize=(10, 4))
for k, c in (("Regantes sin conocer", "#90a4ae"), ("Conocen sin pedir", "#ffb74d"), ("Con reporte", "#ba68c8"),
             ("Suscriptos", "#2e7d32"), ("Abandonaron", "#c62828"), ("Descartaron", "#795548")):
    ax.plot(t, r[k], label=k, color=c, lw=2)
ax.set_ylabel("regantes"); ax.legend(frameon=False, ncol=3, fontsize=9); sem_a_fecha(ax)
ax.set_title("Embudo del regante · guerrilla calibrada")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "02_embudo.png"), dpi=140); plt.close(fig)

# 3. pruebas STEP (modelo marketing_guerrilla_STEP.mdl)
R0 = "Reuniones con inspectores por semana"; FA = "Fracción de falsas alarmas"
pruebas = {
    "Original (0,25 reuniones/sem · 30 % FA)": [],
    "STEP reuniones: 0,25 → 1 en semana 4": [(R0, 1.0, 4)],
    "STEP calibración: FA 30 % → 10 % en semana 22": [(FA, 0.1, 22)],
    "Ambos escalones": [(R0, 1.0, 4), (FA, 0.1, 22)],
}
res["step"] = {}
fig, axs = plt.subplots(2, 2, figsize=(13, 7.5))
for (n, st), c in zip(pruebas.items(), ["#616161", "#1565c0", "#2e7d32", "#c62828"]):
    t, r = simular(steps=st)
    res["step"][n] = indicadores(t, r)
    axs[0, 0].plot(t, r[R0], color=c, lw=2, label=n)
    axs[0, 1].plot(t, r["Cauces aliados"], color=c, lw=2)
    axs[1, 0].plot(t, r["Suscriptos"], color=c, lw=2)
    axs[1, 1].plot(t, r["Reputación"], color=c, lw=2)
for a, ti in zip(axs.ravel(), ("Entrada: reuniones por semana", "Cauces aliados", "Suscriptos", "Reputación")):
    a.set_title(ti); sem_a_fecha(a)
axs[0, 0].legend(fontsize=8, frameon=False)
fig.suptitle("Pruebas con la función STEP: respuesta del sistema a un cambio brusco de política", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "03_pruebas_step.png"), dpi=140); plt.close(fig)

# 4. sensibilidad: reuniones × falsas alarmas → suscriptos y resultado
reun = np.round(np.arange(0.25, 1.51, 0.25), 2)
fas = np.round(np.arange(0.0, 0.41, 0.05), 2)
M_s = np.zeros((len(fas), len(reun))); M_r = np.zeros_like(M_s)
for i, fa in enumerate(fas):
    for j, rr in enumerate(reun):
        t, r = simular({FA: float(fa), R0: float(rr)})
        M_s[i, j] = r["Suscriptos"][-1]; M_r[i, j] = r["Resultado acumulado"][-1]
fig, axs = plt.subplots(2, 1, figsize=(9, 9.5))
for a, M, ti, cm, fmt in ((axs[0], M_s, "Suscriptos al final (abr-2028)", "Greens", "{:.0f}"),
                          (axs[1], M_r, "Resultado acumulado (USD)", "RdYlGn", "{:,.0f}")):
    lim = np.abs(M).max()
    im = a.imshow(M, cmap=cm, aspect="auto", origin="lower", vmin=(-lim if cm == "RdYlGn" else None), vmax=(lim if cm == "RdYlGn" else None))
    a.set_xticks(range(len(reun)), [str(x).replace(".", ",") for x in reun]); a.set_yticks(range(len(fas)), [f"{int(x*100)} %" for x in fas])
    a.set_xlabel("reuniones con inspectores por semana"); a.set_ylabel("fracción de falsas alarmas"); a.set_title(ti)
    for i in range(len(fas)):
        for j in range(len(reun)):
            a.text(j, i, fmt.format(M[i, j]).replace(",", "."), ha="center", va="center", fontsize=8.5)
    fig.colorbar(im, ax=a, shrink=.85)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "04_sensibilidad.png"), dpi=140); plt.close(fig)
res["sensibilidad"] = {"reuniones": reun.tolist(), "falsas_alarmas": fas.tolist(),
                       "suscriptos": np.round(M_s).tolist(), "resultado_usd": np.round(M_r).tolist()}
# punto de equilibrio: mínimo de reuniones con resultado >= 0 para cada FA
res["equilibrio"] = {f"{int(fa*100)}%": next((float(reun[j]) for j in range(len(reun)) if M_r[i, j] >= 0), None)
                     for i, fa in enumerate(fas)}

# 5. precio
precios = [75, 100, 150, 200, 250]
res["precio"] = {}
for pz in precios:
    t, r = simular({FA: 0.1, "Precio por temporada": pz})
    res["precio"][pz] = round(float(r["Resultado acumulado"][-1]))

json.dump(res, open(os.path.join(FIG, "..", "resultados_m5.json"), "w", encoding="utf8"), indent=1, ensure_ascii=False)
print(json.dumps({k: res[k] for k in ("escenarios", "step", "equilibrio", "precio")}, indent=1, ensure_ascii=False))
