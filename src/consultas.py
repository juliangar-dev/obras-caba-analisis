import sqlite3
import pandas as pd

conexion = sqlite3.connect("data/processed/obras.db")

consulta = """
SELECT barrio,
       COUNT(*) AS total,
       SUM(CASE WHEN categoria = 'Demolición' THEN 1 ELSE 0 END) AS demoliciones,
       ROUND(100.0 * SUM(CASE WHEN categoria = 'Demolición' THEN 1 ELSE 0 END) / COUNT(*), 1) AS porcentaje
FROM obras
GROUP BY barrio
HAVING COUNT(*) >= 500
ORDER BY porcentaje DESC
LIMIT 10
"""

resultado = pd.read_sql(consulta, conexion)
print(resultado)

conexion.close()