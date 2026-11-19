import sqlite3
import pandas as pd

conexion = sqlite3.connect("data/processed/obras.db")


def consultar(titulo, sql):
    """Ejecuta una consulta SQL y muestra el resultado con un título."""
    print("\n---", titulo, "---")
    resultado = pd.read_sql(sql, conexion)
    print(resultado)
    return resultado


ranking = consultar("Barrios con más trámites", """
SELECT barrio, COUNT(*) AS cantidad
FROM obras
GROUP BY barrio
ORDER BY cantidad DESC
LIMIT 10
""")

demoliciones = consultar("Proporción de demoliciones por barrio", """
SELECT barrio,
       COUNT(*) AS total,
       SUM(CASE WHEN categoria = 'Demolición' THEN 1 ELSE 0 END) AS demoliciones,
       ROUND(100.0 * SUM(CASE WHEN categoria = 'Demolición' THEN 1 ELSE 0 END) / COUNT(*), 1) AS porcentaje
FROM obras
GROUP BY barrio
HAVING COUNT(*) >= 500
ORDER BY porcentaje DESC
LIMIT 10
""")

por_anio = consultar("Trámites por año (promedio mensual)", """
SELECT anio,
       COUNT(*) AS cantidad,
       COUNT(DISTINCT mes) AS meses,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT mes)) AS promedio_mensual
FROM obras
GROUP BY anio
ORDER BY anio
""")

categorias = consultar("Tipos de trámite en toda la ciudad", """
SELECT categoria,
       COUNT(*) AS cantidad,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM obras), 1) AS porcentaje
FROM obras
GROUP BY categoria
ORDER BY cantidad DESC
""")

urquiza_vs_ciudad = consultar("Villa Urquiza vs. toda la ciudad (% por tipo)", """
SELECT categoria,
       ROUND(100.0 * SUM(CASE WHEN barrio = 'VILLA URQUIZA' THEN 1 ELSE 0 END)
             / (SELECT COUNT(*) FROM obras WHERE barrio = 'VILLA URQUIZA'), 1) AS pct_villa_urquiza,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM obras), 1) AS pct_ciudad
FROM obras
GROUP BY categoria
ORDER BY pct_ciudad DESC
""")

urquiza_por_anio = consultar("Villa Urquiza por año (promedio mensual)", """
SELECT anio,
       COUNT(*) AS cantidad,
       ROUND(1.0 * COUNT(*) / COUNT(DISTINCT mes)) AS promedio_mensual
FROM obras
WHERE barrio = 'VILLA URQUIZA' AND anio >= 2021
GROUP BY anio
ORDER BY anio
""")

conexion.close()