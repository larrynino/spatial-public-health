import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

# ====================================
# CONFIGURACIÓN DE LA PÁGINA
# ====================================
st.set_page_config(
    page_title="Dashboard Emergencia Inundación - Córdoba",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ====================================
# CSS RESPONSIVO (mobile + desktop)
# ====================================
st.markdown("""
    <style>
        /* Títulos responsivos */
        h1 { font-size: clamp(1.2rem, 4vw, 2rem) !important; }
        h2 { font-size: clamp(1rem, 3vw, 1.5rem) !important; }
        h3 { font-size: clamp(0.9rem, 2.5vw, 1.2rem) !important; }

        /* Contenedor principal más compacto */
        .block-container {
            padding: 1rem 1rem 2rem 1rem !important;
            max-width: 100% !important;
        }

        /* Widgets más grandes para touch en mobile */
        .stSelectbox > div > div {
            min-height: 44px !important;
            font-size: clamp(0.8rem, 2.5vw, 1rem) !important;
        }

        /* Métricas más compactas */
        [data-testid="metric-container"] {
            background-color: #f0f4f8;
            border-radius: 8px;
            padding: 0.8rem !important;
            text-align: center;
        }

        [data-testid="metric-container"] label {
            font-size: clamp(0.7rem, 2vw, 0.9rem) !important;
        }

        [data-testid="metric-container"] [data-testid="stMetricValue"] {
            font-size: clamp(1.2rem, 4vw, 2rem) !important;
        }

        /* Separadores */
        hr {
            margin: 0.8rem 0 !important;
        }

        /* Plotly charts */
        .stPlotlyChart {
            width: 100% !important;
        }

        /* Ocultar footer de Streamlit */
        footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ====================================
# CARGAR DATOS
# ====================================
@st.cache_data
def cargar_datos():
    import os
    dir_path = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(dir_path, 'data_cor.csv')
    df = pd.read_csv(csv_path, sep=';', encoding='latin-1')

    df['divipola'] = df['divipola'].astype(str)
    df = df.fillna(0)

    columnas_numericas = ['int_loc', 'int_aloj', 'int_aloviv', 'int_larv', 'int_iec',
                          'int_fum', 'int_tild', 'int_vac', 'int_per', 'int_tot',
                          'pob_alo', 'pob_viv', 'pob_imp', 'pob_ben', 'pob_tot',
                          'cas_den', 'cas_lei', 'cas_mal']

    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['int_tot'] = df[['int_aloj', 'int_aloviv', 'int_larv', 'int_iec', 'int_fum', 'int_tild', 'int_vac']].sum(axis=1)
    df['pob_imp'] = df[['pob_alo', 'pob_viv']].sum(axis=1)
    df['pob_tot'] = df[['pob_imp', 'pob_ben']].sum(axis=1)

    return df

df = cargar_datos()

# ====================================
# TÍTULO PRINCIPAL
# ====================================
st.title("🌊 Dashboard Intervenciones ETV y Zoonosis")
st.caption("Emergencia por Inundación - Córdoba")
st.markdown("---")

# ====================================
# SECCIÓN 1: DISTRIBUCIÓN DE TIPOS DE INTERVENCIÓN
# ====================================
st.header("📊 Distribución de Tipos de Intervención")

municipio_seleccionado = st.selectbox(
    "🏘️ Municipio",
    ['Todos'] + sorted(df['mun'].unique().tolist()),
    key="municipio_pie"
)

if municipio_seleccionado == 'Todos':
    datos_pie = df.copy()
else:
    datos_pie = df[df['mun'] == municipio_seleccionado].copy()

variables_pie = {
    'Localidades': 'int_loc',
    'Alojamientos': 'int_aloj',
    'Aloj. y Viviendas': 'int_aloviv',
    'Larvicidas': 'int_larv',
    'IEC': 'int_iec',
    'Fumigaciones': 'int_fum',
    'TILD': 'int_tild',
    'Vacunación': 'int_vac'
}

valores = []
etiquetas = []

for nombre, columna in variables_pie.items():
    total = datos_pie[columna].sum()
    if total > 0:
        valores.append(total)
        etiquetas.append(nombre)

if len(valores) > 0:
    fig_pie = go.Figure(data=[
        go.Pie(
            labels=etiquetas,
            values=valores,
            marker=dict(
                colors=[
                    '#08306b', '#08519c', '#2171b5', '#4292c6',
                    '#6baed6', '#9ecae1', '#c6dbef', '#deebf7'
                ],
                line=dict(color='white', width=2)
            ),
            textinfo='label+percent',
            textfont=dict(size=11),
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )
    ])

    fig_pie.update_layout(
        title=f'Distribución de Intervenciones - {municipio_seleccionado}',
        height=420,
        autosize=True,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11)
        ),
        margin=dict(l=10, r=10, t=50, b=80)
    )

    st.plotly_chart(fig_pie, use_container_width=True)
else:
    st.warning("No hay datos de intervenciones para este municipio")

st.markdown("---")

# ====================================
# SECCIÓN 2: COMPARATIVA INTERVENCIONES
# ====================================
st.header("📈 Comparativa de Intervenciones entre Municipios")

variable_intervencion = st.selectbox(
    "📊 Tipo de Intervención",
    options=[
        'Total intervenciones',
        'Localidades intervenidas',
        'Alojamientos intervenidos',
        'Alojamientos y viviendas intervenidas',
        'Aplicaciones larvicidas',
        'Intervenciones IEC',
        'Fumigaciones espaciales',
        'TILD entregados',
        'Vacunación animal',
        'Personal técnico'
    ],
    key="var_intervencion"
)

map_intervenciones = {
    'Total intervenciones': 'int_tot',
    'Localidades intervenidas': 'int_loc',
    'Alojamientos intervenidos': 'int_aloj',
    'Alojamientos y viviendas intervenidas': 'int_aloviv',
    'Aplicaciones larvicidas': 'int_larv',
    'Intervenciones IEC': 'int_iec',
    'Fumigaciones espaciales': 'int_fum',
    'TILD entregados': 'int_tild',
    'Vacunación animal': 'int_vac',
    'Personal técnico': 'int_per'
}

columna_int = map_intervenciones[variable_intervencion]
total_int = df[columna_int].sum()

st.metric(
    label=f"Total: {variable_intervencion}",
    value=f"{int(total_int):,}"
)

datos_int = df[df[columna_int] > 0].sort_values(columna_int, ascending=True)

if len(datos_int) > 0:
    fig_int = go.Figure(data=[
        go.Bar(
            x=datos_int[columna_int],
            y=datos_int['mun'],
            orientation='h',
            marker=dict(
                color=datos_int[columna_int],
                colorscale=[
                    [0, '#08306b'],
                    [0.5, '#2171b5'],
                    [1, '#4292c6']
                ],
                showscale=True,
                colorbar=dict(title="Cantidad", thickness=12),
                line=dict(color='white', width=1)
            )
        )
    ])

    fig_int.update_layout(
        title=f'{variable_intervencion} por Municipio',
        xaxis_title='Cantidad',
        yaxis_title='',
        height=max(400, len(datos_int) * 28),
        autosize=True,
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=130, r=60, t=60, b=40),
        font=dict(size=11)
    )

    st.plotly_chart(fig_int, use_container_width=True)
else:
    st.warning("No hay datos para esta variable")

st.markdown("---")

# ====================================
# SECCIÓN 3: COMPARATIVA POBLACIÓN
# ====================================
st.header("👥 Comparativa de Población Intervenida entre Municipios")

variable_poblacion = st.selectbox(
    "👥 Tipo de Población",
    options=[
        'Población total intervenida',
        'Población impactada (viviendas+alojamientos)',
        'Población beneficiada indirecta',
        'Población impactada en alojamientos',
        'Población impactada en viviendas'
    ],
    key="var_poblacion"
)

map_poblacion = {
    'Población total intervenida': 'pob_tot',
    'Población impactada (viviendas+alojamientos)': 'pob_imp',
    'Población beneficiada indirecta': 'pob_ben',
    'Población impactada en alojamientos': 'pob_alo',
    'Población impactada en viviendas': 'pob_viv'
}

columna_pob = map_poblacion[variable_poblacion]
total_pob = df[columna_pob].sum()

st.metric(
    label=f"Total: {variable_poblacion}",
    value=f"{int(total_pob):,}"
)

datos_pob = df[df[columna_pob] > 0].sort_values(columna_pob, ascending=True)

if len(datos_pob) > 0:
    fig_pob = go.Figure(data=[
        go.Bar(
            x=datos_pob[columna_pob],
            y=datos_pob['mun'],
            orientation='h',
            marker=dict(
                color=datos_pob[columna_pob],
                colorscale=[
                    [0, '#084081'],
                    [0.5, '#0868ac'],
                    [1, '#2b8cbe']
                ],
                showscale=True,
                colorbar=dict(title="Personas", thickness=12),
                line=dict(color='white', width=1)
            )
        )
    ])

    fig_pob.update_layout(
        title=f'{variable_poblacion} por Municipio',
        xaxis_title='Número de Personas',
        yaxis_title='',
        height=max(400, len(datos_pob) * 28),
        autosize=True,
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=130, r=60, t=60, b=40),
        font=dict(size=11)
    )

    st.plotly_chart(fig_pob, use_container_width=True)
else:
    st.warning("No hay datos para esta variable")

st.markdown("---")

# ====================================
# SECCIÓN 4: CASOS DE ETV
# ====================================
st.header("🦟 Casos de ETV Identificados")

# Métricas en 3 columnas (se apilan en mobile)
col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label="🦟 Dengue",
        value=f"{int(df['cas_den'].sum()):,}"
    )

with col2:
    st.metric(
        label="🦟 Leishmaniasis",
        value=f"{int(df['cas_lei'].sum()):,}"
    )

with col3:
    st.metric(
        label="🦟 Malaria",
        value=f"{int(df['cas_mal'].sum()):,}"
    )

st.markdown(" ")

datos_etv = df[(df['cas_den'] > 0) | (df['cas_lei'] > 0) | (df['cas_mal'] > 0)].copy()

if len(datos_etv) > 0:
    datos_etv['total_casos'] = datos_etv['cas_den'] + datos_etv['cas_lei'] + datos_etv['cas_mal']
    datos_etv = datos_etv.sort_values('total_casos', ascending=True)

    fig_etv = go.Figure()

    fig_etv.add_trace(go.Bar(
        name='Dengue',
        y=datos_etv['mun'],
        x=datos_etv['cas_den'],
        orientation='h',
        marker=dict(color='#d62728', line=dict(color='white', width=1)),
        hovertemplate='<b>%{y}</b><br>Dengue: %{x}<extra></extra>'
    ))

    fig_etv.add_trace(go.Bar(
        name='Leishmaniasis',
        y=datos_etv['mun'],
        x=datos_etv['cas_lei'],
        orientation='h',
        marker=dict(color='#ff7f0e', line=dict(color='white', width=1)),
        hovertemplate='<b>%{y}</b><br>Leishmaniasis: %{x}<extra></extra>'
    ))

    fig_etv.add_trace(go.Bar(
        name='Malaria',
        y=datos_etv['mun'],
        x=datos_etv['cas_mal'],
        orientation='h',
        marker=dict(color='#2ca02c', line=dict(color='white', width=1)),
        hovertemplate='<b>%{y}</b><br>Malaria: %{x}<extra></extra>'
    ))

    fig_etv.update_layout(
        title='Casos de ETV Identificados por Municipio',
        xaxis_title='Número de Casos',
        yaxis_title='',
        barmode='group',
        height=max(400, len(datos_etv) * 32),
        autosize=True,
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=130, r=20, t=60, b=40),
        font=dict(size=11),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        )
    )

    st.plotly_chart(fig_etv, use_container_width=True)
else:
    st.warning("No hay casos de ETV registrados")

# ====================================
# PIE DE PÁGINA
# ====================================
st.markdown("---")
st.caption("Dashboard desarrollado con Streamlit | Emergencia por Inundación - Córdoba")
