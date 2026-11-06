"""Réplica en Python del modelo Vensim marketing_guerrilla.mdl (SatellAgro).

Mismas ecuaciones, mismos parámetros y el mismo integrador de Euler con TIME STEP = 0,25 semanas,
para poder correr escenarios, pruebas STEP y análisis de sensibilidad sin depender de la licencia de Vensim.
Semana 0 = 1 de noviembre de 2026; semana 78 = fin de abril de 2028 (dos temporadas).
"""
import numpy as np

BASE = {
    "Reuniones con inspectores por semana": 0.25, "Modo de contacto": 0, "Política de alertas": 0,
    "Fracción de falsas alarmas": 0.3, "Capacidad de reportes por semana": 15, "Semana de inicio de cobro": 48,
    "Cauces en la zona": 40, "Probabilidad de acuerdo base": 0.25, "Mejora por caso de éxito": 0.5,
    "Regantes por cauce": 120, "Fracción con vid": 0.6, "Tasa de difusión del inspector": 0.08,
    "Tasa de contacto en frío": 0.25, "Fuerza del boca a boca": 0.3, "Peso del boca a boca negativo": 1.5,
    "Fracción que pide por inspector": 0.12, "Fracción que pide en frío": 0.04, "Tiempo de evaluación": 2,
    "Probabilidad base de roncha": 0.45, "Reputación inicial": 0.7, "Fracción que reintenta": 0.5,
    "Abandono base": 0.005, "Tolerancia a alertas": 0.5, "Sensibilidad al zumbido": 0.05,
    "Probabilidad de abandono por falsa alarma": 0.08, "Tiempo de formación de reputación": 6,
    "Peso de las falsas alarmas": 0.8, "Fracción documentable": 0.1, "Duración del cierre": 1,
    "Precio por temporada": 150, "Semanas de temporada": 26, "Costo por reporte": 15, "Costo por reunión": 40,
    "Costo fijo semanal": 50,
}
VENTANA = ([0, 4, 17, 22, 26, 48, 52, 56, 69, 74, 78], [0.5, 1, 1, 0.5, 0.1, 0.1, 0.5, 1, 1, 0.5, 0.3])
FINAL, DT = 78, 0.25


def pulse(t, start, width):
    return 1.0 if start <= t < start + width else 0.0


def xidz(a, b, x):
    return a / b if b != 0 else x


def simular(cambios=None, steps=()):
    """Corre el modelo. `cambios` modifica parámetros; cada elemento de `steps` = (parámetro, valor_nuevo, semana)
    reemplaza el parámetro por un escalón tipo STEP de Vensim a partir de esa semana."""
    p = dict(BASE, **(cambios or {}))
    s = {"Cauces sin contactar": p["Cauces en la zona"], "Cauces aliados": 0.0, "Regantes sin conocer": 0.0,
         "Conocen sin pedir": 0.0, "Con reporte": 0.0, "Descartaron": 0.0, "Suscriptos": 0.0, "Abandonaron": 0.0,
         "Reputación": p["Reputación inicial"], "Casos de éxito publicados": 0.0, "Ingresos acumulados": 0.0,
         "Costos acumulados": 0.0, "Altas acumuladas": 0.0}
    out = {k: [] for k in list(s) + ["Mercado alcanzado", "Pedidos de reporte", "Altas", "Abandonos",
                                    "Resultado acumulado", "Retención", "Costo por alta", "Ventana estacional",
                                    "Reuniones con inspectores por semana"]}
    tiempos = np.arange(0, FINAL + DT / 2, DT)
    for t in tiempos:
        q = dict(p)
        for param, nuevo, semana in steps:
            if t >= semana:
                q[param] = nuevo
        ven = float(np.interp(t, *VENTANA))
        efecto_casos = min(3, 1 + s["Casos de éxito publicados"] * q["Mejora por caso de éxito"])
        apertura = min(s["Cauces sin contactar"] / DT, q["Reuniones con inspectores por semana"] *
                       q["Probabilidad de acuerdo base"] * efecto_casos * s["Reputación"] / q["Reputación inicial"])
        mercado = s["Cauces aliados"] * q["Regantes por cauce"] * q["Fracción con vid"]
        incorporacion = apertura * q["Regantes por cauce"] * q["Fracción con vid"]
        frio = q["Modo de contacto"] == 1
        difusion = s["Regantes sin conocer"] * ven * (q["Tasa de contacto en frío"] if frio else q["Tasa de difusión del inspector"])
        conv = max(0, xidz(s["Suscriptos"] - q["Peso del boca a boca negativo"] * s["Abandonaron"], mercado, 0))
        boca = s["Regantes sin conocer"] * q["Fuerza del boca a boca"] * conv * ven
        deseados = s["Conocen sin pedir"] * ven * s["Reputación"] * (q["Fracción que pide en frío"] if frio else q["Fracción que pide por inspector"])
        pedidos = min(deseados, q["Capacidad de reportes por semana"])
        roncha = min(1, q["Probabilidad base de roncha"] * (0.3 + 0.7 * ven) * s["Reputación"] / q["Reputación inicial"])
        altas = s["Con reporte"] * roncha / q["Tiempo de evaluación"]
        vuelven = s["Con reporte"] * (1 - roncha) * q["Fracción que reintenta"] / q["Tiempo de evaluación"]
        descartes = s["Con reporte"] * (1 - roncha) * (1 - q["Fracción que reintenta"]) / q["Tiempo de evaluación"]
        alertas = ven * (1.4 if q["Política de alertas"] == 1 else 0.25)
        tasa_ab = (q["Abandono base"] + max(0, alertas - q["Tolerancia a alertas"]) * q["Sensibilidad al zumbido"]
                   + alertas * q["Fracción de falsas alarmas"] * q["Probabilidad de abandono por falsa alarma"])
        abandonos = s["Suscriptos"] * tasa_ab
        aporte = min(0.3, s["Casos de éxito publicados"] * 0.05)
        pen_fa = q["Peso de las falsas alarmas"] * q["Fracción de falsas alarmas"] * min(1, s["Suscriptos"] / 10)
        pen_frio = 0.25 * q["Modo de contacto"]
        pen_ab = 0.5 * xidz(s["Abandonaron"], mercado, 0)
        rep_obj = max(0.05, min(1, q["Reputación inicial"] + aporte - pen_fa - pen_frio - pen_ab))
        cambio_rep = (rep_obj - s["Reputación"]) / q["Tiempo de formación de reputación"]
        cierre = pulse(t, 22, 1) + pulse(t, 74, 1)
        nuevos_casos = s["Suscriptos"] * q["Fracción documentable"] * (1 - q["Fracción de falsas alarmas"]) * cierre / q["Duración del cierre"]
        ingresos = s["Suscriptos"] * q["Precio por temporada"] / q["Semanas de temporada"] if t >= q["Semana de inicio de cobro"] else 0
        costos = pedidos * q["Costo por reporte"] + q["Reuniones con inspectores por semana"] * q["Costo por reunión"] + q["Costo fijo semanal"]

        # guardar (valores al inicio del paso, como Vensim)
        for k in s:
            out[k].append(s[k])
        out["Mercado alcanzado"].append(mercado); out["Pedidos de reporte"].append(pedidos)
        out["Altas"].append(altas); out["Abandonos"].append(abandonos)
        out["Resultado acumulado"].append(s["Ingresos acumulados"] - s["Costos acumulados"])
        out["Retención"].append(xidz(s["Suscriptos"], s["Altas acumuladas"], 0))
        out["Costo por alta"].append(xidz(s["Costos acumulados"], s["Altas acumuladas"], 0))
        out["Ventana estacional"].append(ven)
        out["Reuniones con inspectores por semana"].append(q["Reuniones con inspectores por semana"])

        # integrar (Euler)
        d = {"Cauces sin contactar": -apertura, "Cauces aliados": apertura,
             "Regantes sin conocer": incorporacion - difusion - boca,
             "Conocen sin pedir": difusion + boca + vuelven - pedidos,
             "Con reporte": pedidos - altas - vuelven - descartes, "Descartaron": descartes,
             "Suscriptos": altas - abandonos, "Abandonaron": abandonos, "Reputación": cambio_rep,
             "Casos de éxito publicados": nuevos_casos, "Ingresos acumulados": ingresos,
             "Costos acumulados": costos, "Altas acumuladas": altas}
        for k in s:
            s[k] += DT * d[k]
    return tiempos, {k: np.array(v) for k, v in out.items()}


ESCENARIOS = {
    "Guerrilla calibrada (10 % falsas alarmas)": {"Fracción de falsas alarmas": 0.1},
    "Guerrilla sin calibrar (30 %)": {"Fracción de falsas alarmas": 0.3},
    "Zumbido: alerta en cada imagen": {"Fracción de falsas alarmas": 0.1, "Política de alertas": 1},
    "Contacto en frío": {"Fracción de falsas alarmas": 0.1, "Modo de contacto": 1},
    "1 reunión por semana, calibrada": {"Fracción de falsas alarmas": 0.1, "Reuniones con inspectores por semana": 1},
}


def indicadores(t, r):
    i22 = int(22 / DT)  # cierre de la temporada 1 (fin de marzo de 2027), como en la tabla de la presentación
    return {"cauces_t1": round(float(r["Cauces aliados"][i22]), 1), "altas_t1": round(float(r["Altas acumuladas"][i22]), 0),
            "suscriptos_t2": round(float(r["Suscriptos"][-1]), 0), "retencion": round(float(r["Retención"][-1]), 2),
            "reputacion": round(float(r["Reputación"][-1]), 2), "resultado_usd": round(float(r["Resultado acumulado"][-1]), 0),
            "casos": round(float(r["Casos de éxito publicados"][-1]), 1), "costo_por_alta": round(float(r["Costo por alta"][-1]), 0)}


if __name__ == "__main__":
    for n, c in ESCENARIOS.items():
        print(n, indicadores(*simular(c)))
