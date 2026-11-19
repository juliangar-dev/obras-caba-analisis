import sqlite3
import pandas as pd

# 1. Leer los datos limpios
df = pd.read_csv("data/processed/obras_limpio.csv")

# 2. Crear (o abrir) el archivo de la base de datos
conexion = sqlite3.connect("data/processed/obras.db")

# 3. Guardar la tabla adentro, con el nombre "obras"
df.to_sql("obras", conexion, if_exists="replace", index=False)

conexion.close()
print("Base de datos creada con", len(df), "filas")