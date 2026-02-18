import json
import warnings

import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

warnings.filterwarnings("ignore")

# ── CONFIG DE PÁGINA ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard ETV y Zoonosis – Córdoba",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# CSS mínimo para mejorar la legibilidad en mobile
st.markdown(
    """
    <style>
    /* Reducir padding lateral en mobile */
    .block-container { padding: 1rem 1rem 2rem 1rem; }
    /* Métricas más compactas */
    [data-testid="metric-container"] {
        background: #f0f4f8;
        border-radius: 8px;
        padding: 0.6rem 1rem;
    }
    /* Separador */
    hr { margin: 1.5rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── CONSTANTES ───────────────────────────────────────────────────────────────
DATA_PATH   = "data/data_cor.csv"
SHAPE_PATH  = "data/mun_cor.shp"
COL_NOMBRE  = "mpio_cnmbr"   # ajusta si tu shapefile usa otro campo

COLUMNAS_NUMERICAS = [
    "int_loc", "int_aloj", "int_aloviv", "int_larv", "int_iec",
    "int_fum", "int_tild", "int_vac", "int_per", "int_tot",
    "pob_alo", "pob_viv", "pob_imp", "pob_ben", "pob_tot",
    "cas_den", "cas_lei", "cas_mal",
]

OPCIONES_INTERVENCION = {
    "Total intervenciones":                  "int_tot",
    "Localidades intervenidas":              "int_loc",
    "Alojamientos intervenidos":             "int_aloj",
    "Alojamientos y viviendas intervenidas": "int_aloviv",
    "Aplicaciones larvicidas":               "int_larv",
    "Intervenciones IEC":                    "int_iec",
    "Fumigaciones espaciales":               "int_fum",
    "TILD entregados":                       "int_tild",
    "Vacunación animal":                     "int_vac",
    "Personal técnico":                      "int_per",
}

OPCIONES_POBLACION = {
    "Población total intervenida":                    "pob_tot",
    "Población impactada (viviendas+alojamientos)":   "pob_imp",
    "Población beneficiada indirecta":                "pob_ben",
    "Población impactada en alojamientos":            "pob_alo",
    "Población impactada en viviendas":               "pob_viv",
}


# ── CARGA Y PROCESAMIENTO DE DATOS (cacheado) ────────────────────────────────
@st.cache_data(show_spinner="Cargando datos…")
def cargar_datos():
    # CSV
    df = pd.read_csv(DATA_PATH, sep=";", encoding="latin-1")
    df["divipola"] = df["divipola"].astype(str).str.zfill(5)
    df = df.fillna(0)

    for col in COLUMNAS_NUMERICAS:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["int_tot"] = df[["int_aloj", "int_aloviv", "int_larv",
                         "int_iec", "int_fum", "int_tild", "int_vac"]].sum(axis=1)
    df["pob_imp"] = df[["pob_alo", "pob_viv"]].sum(axis=1)
    df["pob_tot"] = df[["pob_imp", "pob_ben"]].sum(axis=1)

    # Shapefile
    mun_cor = gpd.read_file(SHAPE_PATH).to_crs(epsg=4326)
    mun_cor["mpio_cdpmp"] = mun_cor["mpio_cdpmp"].astype(str).str.zfill(5)

    # Detectar columna de nombre si no existe
    col_nom = COL_NOMBRE
    if col_nom not in mun_cor.columns:
        candidatas = [c for c in mun_cor.columns
                      if any(k in c.lower() for k in ("nmbr", "nombre", "name"))]
        col_nom = candidatas[0] if candidatas else mun_cor.columns[1]

    # JOIN
    df_agg = df.groupby("divipola")[COLUMNAS_NUMERICAS].sum().reset_index()
    gdf = mun_cor.merge(df_agg, left_on="mpio_cdpmp", right_on="divipola", how="left")
    gdf[COLUMNAS_NUMERICAS] = gdf[COLUMNAS_NUMERICAS].fillna(0)

    geojson = json.loads(gdf.to_json())
    centro  = {"lat": gdf.geometry.centroid.y.mean(),
               "lon": gdf.geometry.centroid.x.mean()}

    return gdf, col_nom, geojson, centro


gdf, col_nombre, geojson, centro = cargar_datos()
lista_municipios = sorted(
    gdf[gdf["int_tot"] > 0][col_nombre].dropna().unique().tolist()
)


# ── FUNCIONES DE GRÁFICOS ────────────────────────────────────────────────────
def fig_mapa(variable, escala, titulo_barra):
    nombre_var = next(k for k, v in {**OPCIONES_INTERVENCION,
                                      **OPCIONES_POBLACION}.items() if v == variable)
    fig = px.choropleth_mapbox(
        gdf,
        geojson=geojson,
        locations=gdf.index,
        color=variable,
        hover_name=col_nombre,
        hover_data={variable: ":,.0f"},
        color_continuous_scale=escala,
        mapbox_style="open-street-map",
        zoom=7,
        center=centro,
        opacity=0.7,
        labels={variable: nombre_var},
    )
    fig.update_layout(
        title=f"Mapa: {nombre_var} por Municipio",
        height=500,
        margin=dict(l=0, r=0, t=45, b=0),
        coloraxis_colorbar=dict(title=titulo_barra),
    )
    return fig


def fig_pie(municipio):
    datos = gdf if municipio == "Todos" else gdf[gdf[col_nombre] == municipio]
    variables_pie = {
        "Localidades": "int_loc",
        "Alojamientos": "int_aloj",
        "Aloj. y Viviendas": "int_aloviv",
        "Larvicidas": "int_larv",
        "IEC": "int_iec",
        "Fumigaciones": "int_fum",
        "TILD": "int_tild",
        "Vacunación": "int_vac",
    }
    vals, labs = [], []
    for nombre, col in variables_pie.items():
        t = datos[col].sum()
        if t > 0:
            vals.append(t)
            labs.append(nombre)
    if not vals:
        return None
    fig = go.Figure(data=[go.Pie(
        labels=labs, values=vals,
        marker=dict(
            colors=["#08306b","#08519c","#2171b5","#4292c6",
                    "#6baed6","#9ecae1","#c6dbef","#deebf7"],
            line=dict(color="white", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>Cantidad: %{value}<br>%{percent}<extra></extra>",
    )])
    fig.update_layout(
        title=f"Distribución de Intervenciones – {municipio}",
        height=460,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        margin=dict(l=0, r=0, t=45, b=0),
    )
    return fig


def fig_etv():
    datos = gdf[(gdf["cas_den"] > 0) | (gdf["cas_lei"] > 0) | (gdf["cas_mal"] > 0)].copy()
    if datos.empty:
        return None
    datos["total_casos"] = datos[["cas_den","cas_lei","cas_mal"]].sum(axis=1)
    datos = datos.sort_values("total_casos", ascending=True)
    fig = go.Figure()
    for col_, color_, label_ in [
        ("cas_den", "#d62728", "Dengue"),
        ("cas_lei", "#ff7f0e", "Leishmaniasis"),
        ("cas_mal", "#2ca02c", "Malaria"),
    ]:
        fig.add_trace(go.Bar(
            name=label_, y=datos[col_nombre], x=datos[col_],
            orientation="h",
            marker=dict(color=color_, line=dict(color="white", width=1)),
            hovertemplate=f"<b>%{{y}}</b><br>{label_}: %{{x}}<extra></extra>",
        ))
    fig.update_layout(
        title="Casos de ETV Identificados por Municipio",
        xaxis_title="Número de Casos", yaxis_title="",
        barmode="group",
        height=max(420, len(datos) * 35),
        yaxis={"tickmode": "linear", "tickfont": {"size": 10}},
        margin=dict(l=10, r=10, t=45, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ── LAYOUT DEL DASHBOARD ─────────────────────────────────────────────────────
st.title("🌊 Dashboard Intervenciones ETV y Zoonosis – Córdoba")
st.markdown("---")

# ── SECCIÓN 1: PIE ───────────────────────────────────────────────────────────
st.subheader("📊 Distribución de Tipos de Intervención")

municipio_sel = st.selectbox(
    "🏘️ Municipio",
    options=["Todos"] + lista_municipios,
    index=0,
)

pie = fig_pie(municipio_sel)
if pie:
    st.plotly_chart(pie, use_container_width=True)
else:
    st.info("No hay datos de intervenciones para este municipio.")

st.markdown("---")

# ── SECCIÓN 2: MAPA INTERVENCIONES ───────────────────────────────────────────
st.subheader("📈 Comparativa de Intervenciones entre Municipios")

intervencion_sel = st.selectbox(
    "📊 Tipo de Intervención",
    options=list(OPCIONES_INTERVENCION.keys()),
    index=0,
)
var_int = OPCIONES_INTERVENCION[intervencion_sel]

# Métrica
total_int = int(gdf[var_int].sum())
st.metric(label=f"Total: {intervencion_sel}", value=f"{total_int:,}")

# Mapa
st.plotly_chart(
    fig_mapa(var_int, "Blues", "Cantidad"),
    use_container_width=True,
)

st.markdown("---")

# ── SECCIÓN 3: MAPA POBLACIÓN ────────────────────────────────────────────────
st.subheader("👥 Comparativa de Población Intervenida entre Municipios")

poblacion_sel = st.selectbox(
    "👥 Tipo de Población",
    options=list(OPCIONES_POBLACION.keys()),
    index=0,
)
var_pob = OPCIONES_POBLACION[poblacion_sel]

# Métrica
total_pob = int(gdf[var_pob].sum())
st.metric(label=f"Total: {poblacion_sel}", value=f"{total_pob:,}")

# Mapa
st.plotly_chart(
    fig_mapa(var_pob, "YlOrRd", "Personas"),
    use_container_width=True,
)

st.markdown("---")

# ── SECCIÓN 4: ETV ───────────────────────────────────────────────────────────
st.subheader("🦟 Casos de ETV Identificados")

c1, c2, c3 = st.columns(3)
c1.metric("🦟 Dengue",         f"{int(gdf['cas_den'].sum()):,}")
c2.metric("🦟 Leishmaniasis",  f"{int(gdf['cas_lei'].sum()):,}")
c3.metric("🦟 Malaria",        f"{int(gdf['cas_mal'].sum()):,}")

etv = fig_etv()
if etv:
    st.plotly_chart(etv, use_container_width=True)
else:
    st.info("No hay casos de ETV registrados.")
