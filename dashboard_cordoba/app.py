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
    layout="wide"
)

# ====================================
# CARGAR DATOS
# ====================================
@st.cache_data
def cargar_datos():
    # Cargar datos
    df = pd.read_csv('data_cor.csv', sep=';', encoding='latin-1')
    
    # Convertir DIVIPOLA a string
    df['divipola'] = df['divipola'].astype(str)
    
    # Limpiar datos (reemplazar valores vacíos con 0)
    df = df.fillna(0)
    
    # Convertir columnas numéricas
    columnas_numericas = ['int_loc', 'int_aloj', 'int_aloviv', 'int_larv', 'int_iec', 
                          'int_fum', 'int_tild', 'int_vac', 'int_per', 'int_tot',
                          'pob_alo', 'pob_viv', 'pob_imp', 'pob_ben', 'pob_tot',
                          'cas_den', 'cas_lei', 'cas_mal']
    
    for col in columnas_numericas:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Calcular campos derivados
    df['int_tot'] = df[['int_aloj', 'int_aloviv', 'int_larv', 'int_iec', 'int_fum', 'int_tild', 'int_vac']].sum(axis=1)
    df['pob_imp'] = df[['pob_alo', 'pob_viv']].sum(axis=1)
    df['pob_tot'] = df[['pob_imp', 'pob_ben']].sum(axis=1)
    
    return df

# Cargar los datos
df = cargar_datos()

# ====================================
# TÍTULO PRINCIPAL
# ====================================
st.title("🌊 Dashboard Intervenciones ETV y Zoonosis")
st.markdown("---")

# ====================================
# SECCIÓN 1: DISTRIBUCIÓN DE TIPOS DE INTERVENCIÓN
# ====================================
st.header("📊 Distribución de Tipos de Intervención")

municipio_seleccionado = st.selectbox(
    "🏘️ Municipio (para distribución)",
    ['Todos'] + sorted(df['mun'].unique().tolist()),
    key="municipio_pie"
)

# Filtrar datos según municipio
if municipio_seleccionado == 'Todos':
    datos_pie = df.copy()
else:
    datos_pie = df[df['mun'] == municipio_seleccionado].copy()

# Variables de intervención para el pie
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

# Sumar totales por tipo de intervención
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
            textfont=dict(size=12),
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )
    ])
    
    fig_pie.update_layout(
        title=f'Distribución de Intervenciones - {municipio_seleccionado}',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
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
    "📊 Tipo de Intervención (para comparativa)",
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

# Mapeo de nombres a columnas
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

# Métrica total
total_int = df[columna_int].sum()
st.metric(
    label=f"Total: {variable_intervencion}",
    value=f"{int(total_int):,}"
)

# Gráfico de barras
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
                colorbar=dict(title="Cantidad"),
                line=dict(color='white', width=1)
            )
        )
    ])
    
    fig_int.update_layout(
        title=f'{variable_intervencion} por Municipio',
        xaxis_title='Cantidad',
        yaxis_title='Municipio',
        height=max(500, len(datos_int) * 30),
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=150, r=50, t=80, b=50)
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
    "👥 Tipo de Población (para comparativa)",
    options=[
        'Población total intervenida',
        'Población impactada (viviendas+alojamientos)',
        'Población beneficiada indirecta',
        'Población impactada en alojamientos',
        'Población impactada en viviendas'
    ],
    key="var_poblacion"
)

# Mapeo de nombres a columnas
map_poblacion = {
    'Población total intervenida': 'pob_tot',
    'Población impactada (viviendas+alojamientos)': 'pob_imp',
    'Población beneficiada indirecta': 'pob_ben',
    'Población impactada en alojamientos': 'pob_alo',
    'Población impactada en viviendas': 'pob_viv'
}

columna_pob = map_poblacion[variable_poblacion]

# Métrica total
total_pob = df[columna_pob].sum()
st.metric(
    label=f"Total: {variable_poblacion}",
    value=f"{int(total_pob):,}"
)

# Gráfico de barras
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
                colorbar=dict(title="Personas"),
                line=dict(color='white', width=1)
            )
        )
    ])
    
    fig_pob.update_layout(
        title=f'{variable_poblacion} por Municipio',
        xaxis_title='Número de Personas',
        yaxis_title='Municipio',
        height=max(500, len(datos_pob) * 30),
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=150, r=50, t=80, b=50)
    )
    
    st.plotly_chart(fig_pob, use_container_width=True)
else:
    st.warning("No hay datos para esta variable")

st.markdown("---")

# ====================================
# SECCIÓN 4: CASOS DE ETV
# ====================================
st.header("🦟 Casos de ETV Identificados")

# Métricas totales
col1, col2, col3 = st.columns(3)

with col1:
    total_dengue = df['cas_den'].sum()
    st.metric(
        label="🦟 Total Casos Dengue",
        value=f"{int(total_dengue):,}"
    )

with col2:
    total_leishmaniasis = df['cas_lei'].sum()
    st.metric(
        label="🦟 Total Casos Leishmaniasis",
        value=f"{int(total_leishmaniasis):,}"
    )

with col3:
    total_malaria = df['cas_mal'].sum()
    st.metric(
        label="🦟 Total Casos Malaria",
        value=f"{int(total_malaria):,}"
    )

# Gráfico de barras agrupadas
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
        yaxis_title='Municipio',
        barmode='group',
        height=max(500, len(datos_etv) * 35),
        yaxis={'tickmode': 'linear', 'tickfont': {'size': 10}},
        margin=dict(l=150, r=50, t=80, b=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig_etv, use_container_width=True)
else:
    st.warning("No hay casos de ETV registrados")

# ====================================
# PIE DE PÁGINA
# ====================================
st.markdown("---")
st.caption("Dashboard desarrollado con Streamlit | Emergencia por Inundación - Córdoba")
