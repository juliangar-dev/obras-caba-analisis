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

conexion.close()