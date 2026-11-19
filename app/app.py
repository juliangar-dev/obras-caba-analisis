import altair as alt
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st

st.set_page_config(page_title="¿Qué se construye cerca tuyo?", page_icon="🏗️", layout="wide")

ARCHIVO = "data/processed/obras_limpio.csv"

# Colores por categoría (R, G, B) para el mapa
COLORES = {
    "Demolición": [214, 69, 65],
    "Obra (permisos y registros)": [47, 93, 138],
    "Propiedad horizontal": [224, 123, 57],
    "Instalaciones": [140, 140, 140],
    "Regularización": [120, 90, 160],
    "Ampliación / modificación": [60, 150, 110],
    "Otros": [190, 190, 190],
}


@st.cache_data
def cargar_datos():
    df = pd.read_csv(ARCHIVO, parse_dates=["fecha"])
    df["color"] = df["categoria"].map(COLORES)
    df["fecha_txt"] = df["fecha"].dt.strftime("%d/%m/%Y")
    return df


def distancia_metros(lat1, lon1, lat2, lon2):
    """Distancia en metros entre un punto y muchos puntos (fórmula de Haversine)."""
    radio_tierra = 6_371_000
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * radio_tierra * np.arcsin(np.sqrt(a))


@st.cache_data(show_spinner=False)
def buscar_direccion(texto):
    """Convierte una dirección en coordenadas.
    Primero usa el normalizador oficial de la Ciudad (USIG); si falla, OpenStreetMap."""
    try:
        r = requests.get(
            "https://servicios.usig.buenosaires.gob.ar/normalizar/",
            params={"direccion": texto, "geocodificar": "TRUE", "srid": 4326},
            timeout=10,
        )
        resultados = r.json().get("direccionesNormalizadas", [])
        if resultados and resultados[0].get("coordenadas"):
            c = resultados[0]["coordenadas"]
            return float(c["y"]), float(c["x"]), resultados[0]["direccion"]
    except Exception:
        pass

    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{texto}, Ciudad Autónoma de Buenos Aires, Argentina",
                    "format": "json", "limit": 1},
            headers={"User-Agent": "obras-caba-analisis (proyecto educativo)"},
            timeout=10,
        )
        resultados = r.json()
        if resultados:
            return (float(resultados[0]["lat"]), float(resultados[0]["lon"]),
                    resultados[0]["display_name"].split(", Comuna")[0])
    except Exception:
        pass

    return None


def promedio_mensual_por_anio(df):
    """Trámites por mes, promedio de cada año (desde 2021, porque 2020 está incompleto)."""
    df = df[df["anio"] >= 2021]
    meses = df.groupby("anio")["fecha"].apply(lambda f: f.dt.to_period("M").nunique())
    return df.groupby("anio").size() / meses


obras = cargar_datos()

# ---------- Encabezado ----------
st.title("🏗️ ¿Qué se construye cerca tuyo?")
st.markdown(
    "Escribí una dirección de la Ciudad de Buenos Aires y mirá todas las obras, demoliciones "
    "y trámites registrados a tu alrededor desde 2020, comparados con el resto de la Ciudad."
)

col_dir, col_radio = st.columns([3, 1])
with col_dir:
    direccion = st.text_input("Dirección", placeholder="Ej: Monroe 5000")
with col_radio:
    radio = st.select_slider("Radio", options=[200, 300, 500, 750, 1000], value=500,
                             format_func=lambda m: f"{m} m")

if not direccion:
    st.info("Escribí una dirección para empezar. Por ejemplo: *Triunvirato 4500* o *Av. Cabildo 2000*.")
    st.stop()

ubicacion = buscar_direccion(direccion)
if ubicacion is None:
    st.error("No encontré esa dirección. Probá con calle y altura, por ejemplo *Monroe 5000*.")
    st.stop()

lat, lon, nombre = ubicacion
obras["distancia"] = distancia_metros(lat, lon, obras["lat"].values, obras["lon"].values)
zona = obras[obras["distancia"] <= radio]

st.subheader(f"📍 {nombre}")

if zona.empty:
    st.warning(f"No hay trámites registrados a menos de {radio} m. Probá con un radio más grande.")
    st.stop()

# ---------- Indicadores ----------
pct_demol_zona = 100 * (zona["categoria"] == "Demolición").mean()
pct_demol_ciudad = 100 * (obras["categoria"] == "Demolición").mean()
pct_ph_zona = 100 * (zona["categoria"] == "Propiedad horizontal").mean()
pct_ph_ciudad = 100 * (obras["categoria"] == "Propiedad horizontal").mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trámites en la zona", f"{len(zona):,}".replace(",", "."))
c2.metric("Demoliciones", int((zona["categoria"] == "Demolición").sum()))
c3.metric("% demoliciones", f"{pct_demol_zona:.1f}%",
          f"{pct_demol_zona - pct_demol_ciudad:+.1f} pts vs. Ciudad", delta_color="off")
c4.metric("% edificios nuevos (PH)", f"{pct_ph_zona:.1f}%",
          f"{pct_ph_zona - pct_ph_ciudad:+.1f} pts vs. Ciudad", delta_color="off")

# Lectura automática de la zona
renovacion = pct_demol_zona + pct_ph_zona
renovacion_ciudad = pct_demol_ciudad + pct_ph_ciudad
if len(zona) < 30:
    lectura = "Hay pocos trámites en esta zona como para sacar conclusiones firmes."
elif renovacion > renovacion_ciudad * 1.2:
    lectura = ("**Zona en renovación.** Hay más demoliciones y planos de edificios nuevos que el promedio "
               "de la Ciudad: probablemente se estén reemplazando casas por edificios.")
elif renovacion < renovacion_ciudad * 0.8:
    lectura = ("**Zona estable.** Hay menos demoliciones y edificios nuevos que el promedio: "
               "la mayoría de los trámites son reformas o instalaciones en construcciones existentes.")
else:
    lectura = "**Zona en el promedio** de la Ciudad en cuanto a demoliciones y edificios nuevos."
st.markdown(lectura)

# ---------- Mapa ----------
st.markdown("#### Mapa")
categorias = st.multiselect("Mostrar", list(COLORES), default=list(COLORES))
puntos = zona[zona["categoria"].isin(categorias)]

capas = [
    pdk.Layer("ScatterplotLayer", data=pd.DataFrame({"lat": [lat], "lon": [lon]}),
              get_position="[lon, lat]", get_radius=radio, get_fill_color=[47, 93, 138, 25],
              get_line_color=[47, 93, 138, 160], stroked=True, line_width_min_pixels=1),
    pdk.Layer("ScatterplotLayer", data=puntos[["lat", "lon", "color", "direccion", "tipo_tramite", "fecha_txt"]],
              get_position="[lon, lat]", get_fill_color="color", get_radius=9,
              radius_min_pixels=3, pickable=True),
    pdk.Layer("ScatterplotLayer", data=pd.DataFrame({"lat": [lat], "lon": [lon]}),
              get_position="[lon, lat]", get_fill_color=[0, 0, 0], get_radius=12, radius_min_pixels=6),
]
zoom = {200: 16.6, 300: 16.1, 500: 15.4, 750: 14.8, 1000: 14.4}[radio]
st.pydeck_chart(pdk.Deck(
    layers=capas,
    initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom),
    map_provider="carto", map_style="light",
    tooltip={"text": "{direccion}\n{tipo_tramite}\n{fecha_txt}"},
), height=480)
st.markdown("&nbsp;&nbsp;&nbsp;".join(
    f"<span style='color:rgb({c[0]},{c[1]},{c[2]}); font-size:1.3em'>●</span> {n}"
    for n, c in COLORES.items()
), unsafe_allow_html=True)

# ---------- Gráficos ----------
g1, g2 = st.columns(2)

ESCALA = alt.Scale(domain=["Esta zona", "Toda la Ciudad"], range=["#e07b39", "#2f5d8a"])
LEYENDA = alt.Legend(orient="bottom", title=None)

with g1:
    st.markdown("#### Evolución (índice 2021 = 100)")
    evol_zona = promedio_mensual_por_anio(zona)
    evol_ciudad = promedio_mensual_por_anio(obras)
    if 2021 in evol_zona.index and evol_zona[2021] > 0:
        indice = pd.DataFrame({
            "Esta zona": 100 * evol_zona / evol_zona[2021],
            "Toda la Ciudad": 100 * evol_ciudad / evol_ciudad[2021],
        }).round(0).reset_index(names="anio").melt("anio", var_name="serie", value_name="indice")
        grafico = alt.Chart(indice).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("anio:O", title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("indice:Q", title="Índice (2021 = 100)", scale=alt.Scale(zero=False)),
            color=alt.Color("serie:N", scale=ESCALA, legend=LEYENDA),
            tooltip=[alt.Tooltip("anio:O", title="Año"), alt.Tooltip("serie:N", title=" "),
                     alt.Tooltip("indice:Q", title="Índice")],
        ).properties(height=320)
        st.altair_chart(grafico, width="stretch")
        st.caption("Promedio de trámites por mes de cada año. 100 = nivel de 2021.")
    else:
        st.caption("No hay datos suficientes de 2021 en esta zona para comparar.")

with g2:
    st.markdown("#### Tipo de trámite (%)")
    orden = obras["categoria"].value_counts().index.tolist()
    comparacion = pd.DataFrame({
        "Esta zona": zona["categoria"].value_counts(normalize=True) * 100,
        "Toda la Ciudad": obras["categoria"].value_counts(normalize=True) * 100,
    }).fillna(0).round(1).reset_index(names="categoria").melt(
        "categoria", var_name="serie", value_name="porcentaje")
    grafico = alt.Chart(comparacion).mark_bar().encode(
        y=alt.Y("categoria:N", sort=orden, title=None),
        yOffset=alt.YOffset("serie:N", sort=["Esta zona", "Toda la Ciudad"]),
        x=alt.X("porcentaje:Q", title="% de los trámites"),
        color=alt.Color("serie:N", scale=ESCALA, legend=LEYENDA),
        tooltip=[alt.Tooltip("categoria:N", title="Tipo"), alt.Tooltip("serie:N", title=" "),
                 alt.Tooltip("porcentaje:Q", title="%")],
    ).properties(height=320)
    st.altair_chart(grafico, width="stretch")

# ---------- Últimos trámites ----------
st.markdown("#### Últimos trámites en la zona")
ultimos = zona.sort_values("fecha", ascending=False).head(15)
st.dataframe(
    ultimos[["fecha_txt", "direccion", "tipo_tramite", "distancia"]].rename(columns={
        "fecha_txt": "Fecha", "direccion": "Dirección", "tipo_tramite": "Trámite",
        "distancia": "Distancia (m)"}).round({"Distancia (m)": 0}),
    hide_index=True,
)

st.divider()
st.caption(
    "Datos: [Obras registradas](https://data.buenosaires.gob.ar/dataset/obras-registradas), "
    "datos abiertos del Gobierno de la Ciudad de Buenos Aires (sep 2020 - oct 2026). "
    "[Código del proyecto](https://github.com/juliangar-dev/obras-caba-analisis)."
)
