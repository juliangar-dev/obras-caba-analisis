import pandas as pd

# Leer el archivo de datos
df = pd.read_csv("data/raw/obras_registradas.csv", encoding="utf-8-sig")

# Tamaño: cuántas filas y columnas
print("Filas y columnas:", df.shape)

# Nombres de las columnas
print(df.columns.tolist())

# Las 5 primeras filas, para ver cómo son los datos
print(df.head())

# Los 10 barrios con más trámites
print(df["barrio"].value_counts().head(10))