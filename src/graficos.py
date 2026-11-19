import sqlite3

import matplotlib.pyplot as plt
import pandas as pd

conexion = sqlite3.connect("data/processed/obras.db")
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
AZUL = "#2f5d8a"
NARANJA = "#e07b39"


def guardar(nombre):
    plt.tight_layout()
    plt.savefig(f"img/{nombre}.png", dpi=150)
    plt.close()
    print("Guardado: img/" + nombre + ".png")


# 1. Barrios con más trámites
barrios = pd.read_sql("""
SELECT barrio, COUNT(*) AS cantidad
FROM obras
GROUP BY barrio
ORDER BY cantidad DESC
LIMIT 10
""", conexion)

plt.figure(figsize=(8, 5))
colores = [NARANJA if b == "VILLA URQUIZA" else AZUL for b in barrios["barrio"]]
plt.barh(barrios["barrio"][::-1], barrios["cantidad"][::-1], color=colores[::-1])
plt.title("Barrios con más trámites de obra (sep 2020 - oct 2026)")
plt.xlabel("Cantidad de trámites")
guardar("1_barrios")

# 2. Evolución: promedio mensual por año (2021 en adelante)
anios = pd.read_sql("""
SELECT anio, ROUND(1.0 * COUNT(*) / COUNT(DISTINCT mes)) AS promedio_mensual
FROM obras
WHERE anio >= 2021
GROUP BY anio
ORDER BY anio
""", conexion)

plt.figure(figsize=(8, 5))
plt.plot(anios["anio"], anios["promedio_mensual"], marker="o", color=AZUL, linewidth=2)
for x, y in zip(anios["anio"], anios["promedio_mensual"]):
    plt.annotate(f"{int(y):,}".replace(",", "."), (x, y), textcoords="offset points",
                 xytext=(0, 8), ha="center")
plt.title("Trámites de obra por mes, promedio anual (Ciudad de Buenos Aires)")
plt.ylabel("Trámites por mes")
plt.xticks(anios["anio"])
plt.ylim(0, anios["promedio_mensual"].max() * 1.15)
guardar("2_evolucion")

# 3. Villa Urquiza vs. toda la ciudad, por tipo de trámite
comparacion = pd.read_sql("""
SELECT categoria,
       ROUND(100.0 * SUM(CASE WHEN barrio = 'VILLA URQUIZA' THEN 1 ELSE 0 END)
             / (SELECT COUNT(*) FROM obras WHERE barrio = 'VILLA URQUIZA'), 1) AS villa_urquiza,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM obras), 1) AS ciudad
FROM obras
WHERE categoria NOT IN ('Otros', 'Ampliación / modificación')
GROUP BY categoria
ORDER BY ciudad DESC
""", conexion)

posiciones = range(len(comparacion))
plt.figure(figsize=(9, 5))
plt.bar([p - 0.2 for p in posiciones], comparacion["villa_urquiza"], width=0.4,
        label="Villa Urquiza", color=NARANJA)
plt.bar([p + 0.2 for p in posiciones], comparacion["ciudad"], width=0.4,
        label="Toda la ciudad", color=AZUL)
plt.xticks(list(posiciones), comparacion["categoria"], rotation=15)
plt.ylabel("% del total de trámites")
plt.title("Villa Urquiza vs. toda la ciudad: tipo de trámite")
plt.legend(frameon=False)
guardar("3_urquiza_vs_ciudad")

# 4. Mapa: dónde se concentran los trámites
puntos = pd.read_sql("SELECT lat, lon FROM obras", conexion)

plt.figure(figsize=(7, 7))
plt.hexbin(puntos["lon"], puntos["lat"], gridsize=60, cmap="YlOrRd", mincnt=1)
plt.colorbar(label="Cantidad de trámites")
plt.title("Concentración de trámites de obra en la Ciudad")
plt.axis("equal")
plt.axis("off")
guardar("4_mapa")

conexion.close()