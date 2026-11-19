import re
import unicodedata

import pandas as pd

ARCHIVO_ORIGINAL = "data/raw/obras_registradas.csv"
ARCHIVO_LIMPIO = "data/processed/obras_limpio.csv"


def quitar_tildes(texto):
    """Pasa 'INSTALACIÓN' a 'INSTALACION' para comparar textos sin problemas de tildes."""
    texto = unicodedata.normalize("NFD", texto)
    return "".join(letra for letra in texto if unicodedata.category(letra) != "Mn")


def categorizar(descripcion):
    """Agrupa los más de 100 tipos de trámite en unas pocas categorías."""
    d = quitar_tildes(str(descripcion).upper())

    if "AMPLIACION" in d:
        return "Ampliación / modificación"
    if "DEMOLICION" in d:
        return "Demolición"
    if any(p in d for p in ["INSTALACION", "SALAS DE MAQUINAS", "INCENDIO",
                            "ELEMENTOS GUIADOS", "INFLAMABLES"]):
        return "Instalaciones"
    if any(p in d for p in ["REGULARIZACION", "CONTRAVENCION", "SIN PERMISO"]):
        return "Regularización"
    if "PROPIEDAD HORIZONTAL" in d:
        return "Propiedad horizontal"
    if "OBRA" in d or "PLANO CONFORME" in d:
        return "Obra (permisos y registros)"
    return "Otros"


def extraer_coordenadas(punto):
    """De 'POINT(-58.47 -34.58)' saca longitud y latitud como números."""
    numeros = re.findall(r"-?\d+\.?\d*", str(punto))
    if len(numeros) != 2:
        return None, None
    return float(numeros[0]), float(numeros[1])


def limpiar(df):
    df = df.copy()

    # Quitar filas repetidas (mismo número de registro)
    df = df.drop_duplicates(subset="id_registr")

    # Fechas: de texto a fecha real, y columnas de año y mes
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["anio"] = df["fecha"].dt.year
    df["mes"] = df["fecha"].dt.to_period("M").astype(str)

    # Textos: sacar espacios de más
    df["barrio"] = df["barrio"].str.strip()
    df["descripcio"] = df["descripcio"].str.strip()

    # Agrupar tipos de trámite
    df["categoria"] = df["descripcio"].apply(categorizar)

    # Coordenadas para el mapa
    coordenadas = df["wkt_2"].apply(extraer_coordenadas)
    df["lon"] = coordenadas.str[0]
    df["lat"] = coordenadas.str[1]

    # Quedarse solo con las columnas útiles, con nombres claros
    df = df.rename(columns={"id_registr": "id", "descripcio": "tipo_tramite",
                            "ubicacion": "direccion"})
    return df[["id", "fecha", "anio", "mes", "barrio", "comuna", "direccion",
               "tipo_tramite", "categoria", "lat", "lon"]]


if __name__ == "__main__":
    original = pd.read_csv(ARCHIVO_ORIGINAL, encoding="utf-8-sig")
    limpio = limpiar(original)
    limpio.to_csv(ARCHIVO_LIMPIO, index=False, encoding="utf-8")

    print("Filas originales:", len(original))
    print("Filas limpias:   ", len(limpio))
    print()
    print(limpio["categoria"].value_counts())