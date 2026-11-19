import pandas as pd

from src.limpieza import categorizar, extraer_coordenadas, limpiar, quitar_tildes


def test_quitar_tildes():
    assert quitar_tildes("INSTALACIÓN TÉRMICA") == "INSTALACION TERMICA"


def test_categorizar_demolicion():
    assert categorizar("PERMISO DE DEMOLICION") == "Demolición"


def test_categorizar_con_y_sin_tilde():
    # Las dos formas de escribirlo tienen que caer en la misma categoría
    assert categorizar("REGISTRO DE PLANO DE DEMOLICIÓN") == "Demolición"
    assert categorizar("PROYECTO INSTALACION ELECTRICA") == "Instalaciones"
    assert categorizar("REGISTRO DE PROYECTO DE INSTALACIÓN ELÉCTRICA") == "Instalaciones"


def test_categorizar_desconocido_va_a_otros():
    assert categorizar("SOLICITUD DE COPIA DE PLANO") == "Otros"


def test_extraer_coordenadas():
    lon, lat = extraer_coordenadas("POINT(-58.4755 -34.5858)")
    assert lon == -58.4755
    assert lat == -34.5858


def test_extraer_coordenadas_invalidas():
    assert extraer_coordenadas("texto roto") == (None, None)


def test_limpiar_elimina_duplicados_y_crea_columnas():
    datos = pd.DataFrame({
        "id_registr": [1, 1, 2],
        "fecha": ["2023-03-16 14:40:46", "2023-03-16 14:40:46", "2024-01-05 10:00:00"],
        "ubicacion": ["LLERENA 2655", "LLERENA 2655", "MONROE 5000"],
        "descripcio": ["PERMISO DE DEMOLICION", "PERMISO DE DEMOLICION", "OBRA NUEVA"],
        "barrio": [" VILLA URQUIZA ", " VILLA URQUIZA ", "BELGRANO"],
        "comuna": ["Comuna 12", "Comuna 12", "Comuna 13"],
        "wkt_2": ["POINT(-58.48 -34.57)", "POINT(-58.48 -34.57)", "POINT(-58.46 -34.56)"],
    })
    resultado = limpiar(datos)

    assert len(resultado) == 2                           # se fue el repetido
    assert resultado.iloc[0]["barrio"] == "VILLA URQUIZA"  # sin espacios de más
    assert resultado.iloc[0]["anio"] == 2023
    assert resultado.iloc[0]["categoria"] == "Demolición"