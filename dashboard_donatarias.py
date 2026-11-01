import os
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from acerca_de import mostrar_acerca_de   # texto de la pestaña "Acerca de" (acerca_de.py, misma carpeta)
import numpy as np
import plotly.io as pio


# IDENTIDAD VISUAL
COLOR_GRIS_CLARO   = "#F2F2F2"
COLOR_ROJO_PROFUNDO = "#8B2C1A"
COLOR_ROJO_OXIDO    = "#B15E2E"
COLOR_AZUL_PRUSIA   = "#003153"
COLOR_GRIS_GRAFITO  = "#2C2C2C"
COLOR_BLANCO        = "#FFFFFF"

# Paleta categórica para usar en gráficos con varias categorías (orden = orden de uso)
PALETA_CATEGORICA = [COLOR_AZUL_PRUSIA, COLOR_ROJO_PROFUNDO, COLOR_ROJO_OXIDO, COLOR_GRIS_GRAFITO, "#8FA9B8"]

# Template de Plotly aplicado por default a TODAS las figuras
pio.templates["marca_donatarias"] = pio.templates["plotly_white"]
pio.templates["marca_donatarias"].layout.update(
    font=dict(family="Roboto Mono, monospace", color=COLOR_GRIS_GRAFITO, size=13),
    title_font=dict(family="Montserrat, sans-serif", color=COLOR_GRIS_GRAFITO, size=18),
    paper_bgcolor=COLOR_BLANCO,
    plot_bgcolor=COLOR_BLANCO,
    colorway=PALETA_CATEGORICA,
)
pio.templates.default = "marca_donatarias"

def estilizar_figura(fig, altura=390):
    fig.update_layout(
        height=altura,
        paper_bgcolor=COLOR_BLANCO,
        plot_bgcolor=COLOR_BLANCO,

        font=dict(
            family="Roboto Mono, monospace",
            color=COLOR_GRIS_GRAFITO,
            size=11
        ),

        title=dict(
            font=dict(
                family="Montserrat, sans-serif",
                color=COLOR_GRIS_GRAFITO,
                size=15
            ),
            x=0.01,
            xanchor="left",
            y=0.97,
            yanchor="top"
        ),

        margin=dict(
            l=50,
            r=20,
            t=45,
            b=55
        ),

        legend=dict(
            font=dict(
                family="Montserrat, sans-serif",
                color=COLOR_GRIS_GRAFITO,
                size=10
            )
        ),

        hoverlabel=dict(
            font_family="Roboto Mono, monospace"
        )
    )

    # EJE X
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E5E5E5",
        zeroline=False,
        linecolor="#D0D0D0",
        tickangle=0,
        automargin=True,
        tickfont=dict(
            family="Montserrat, sans-serif",
            size=11,
            color=COLOR_GRIS_GRAFITO
        )
    )


    # EJE Y
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E5E5E5",
        zeroline=False,
        linecolor="#D0D0D0",
        automargin=True,
        tickangle=0,
        tickfont=dict(
            family="Roboto Mono, monospace",
            size=10,
            color=COLOR_GRIS_GRAFITO
        )
    )

    return fig


def leyenda_compacta(fig, entradas, titulo=None, simbolo="●",
                     x=0.01, y=0.99, xanchor="left", yanchor="top", tamano=9):
    """Leyenda compacta DENTRO de la gráfica (por defecto arriba a la izquierda).
    Se dibuja como una sola anotación de texto: el interlineado lo da la fuente (~12 px por renglón),
    no el mínimo de ~20 px de la leyenda nativa de Plotly. A cambio no es clicable.

    entradas: lista de (nombre, color_hex) en el orden en que deben aparecer.
    """
    renglones = []
    if titulo:
        renglones.append(f"<span style='color:#7A7A7A'>{titulo}</span>")
    for nombre, color in entradas:
        renglones.append(f"<span style='color:{color};font-size:{tamano + 3}px'>{simbolo}</span> {nombre}")
    fig.update_layout(showlegend=False, margin=dict(r=15))
    fig.add_annotation(
        text="<br>".join(renglones),
        xref="paper", yref="paper", x=x, y=y, xanchor=xanchor, yanchor=yanchor,
        align="left", showarrow=False,
        font=dict(family="Montserrat, sans-serif", size=tamano, color=COLOR_GRIS_GRAFITO),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="rgba(44,44,44,0.15)", borderwidth=1, borderpad=4,
    )
    return fig


def hex_a_rgba(color_hex, alpha):
    h = color_hex.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


st.set_page_config(page_title="Dashboard Donatarias", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@600;700&family=Cormorant+Garamond:wght@400;500&family=Roboto+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Cormorant Garamond', serif;
    color: #2C2C2C;
}

h1, h2, h3, h4 {
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 700 !important;
    color: #2C2C2C !important;
}

.stApp {
    background-color: #F2F2F2;
}

section[data-testid="stSidebar"] {
    background-color: #003153;
}
section[data-testid="stSidebar"] * {
    color: #F2F2F2 !important;
    font-family: 'Montserrat', sans-serif !important;
}

div[data-testid="stMetric"] {
    background-color: #FFFFFF;
    border-left: 4px solid #8B2C1A;
    padding: 12px 16px;
    border-radius: 4px;
}
div[data-testid="stMetricValue"] {
    font-family: 'Roboto Mono', monospace !important;
    color: #8B2C1A !important;
}

.stTabs [data-baseweb="tab"] {
    font-family: 'Montserrat', sans-serif;
    font-weight: 600;
    color: #2C2C2C;
}
.stTabs [aria-selected="true"] {
    color: #8B2C1A !important;
    border-bottom-color: #8B2C1A !important;
}

/* =========================================
   FILTROS MULTISELECT
   ========================================= */

section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #8B2C1A !important;
    border-color: #8B2C1A !important;
}

section[data-testid="stSidebar"] [data-baseweb="tag"] span {
    color: #FFFFFF !important;
}

section[data-testid="stSidebar"] [data-baseweb="tag"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
}

section[data-testid="stSidebar"] [data-baseweb="tag"]:hover {
    background-color: #8B2C1A !important;
}
            
/* =========================================
   ESPACIADO GENERAL
   ========================================= */

[data-testid="stAppViewContainer"] .main .block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
    padding-left: 1.2rem;
    padding-right: 1.2rem;
    max-width: 100%;
}

[data-testid="stVerticalBlock"] {
    gap: 0.5rem;
}
            
/* =========================================
   MULTISELECT — TAGS SELECCIONADOS
   ========================================= */

.stMultiSelect [data-baseweb="tag"],
.stMultiSelect [data-baseweb="tag"] > div {
    background-color: #8B2C1A !important;
    border-color: #8B2C1A !important;
}

.stMultiSelect [data-baseweb="tag"] span {
    color: #FFFFFF !important;
}

.stMultiSelect [data-baseweb="tag"] svg {
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
}

.stMultiSelect [data-baseweb="tag"]:hover,
.stMultiSelect [data-baseweb="tag"]:focus {
    background-color: #8B2C1A !important;
    border-color: #8B2C1A !important;
}
            
/* =========================================
   FILTROS — BOTONES DE POPOVER
   ========================================= */
section[data-testid="stSidebar"] [data-testid="stPopover"] button {
    background-color: #FFFFFF !important;
    color: #2C2C2C !important;
    border: 1px solid rgba(255,255,255,0.3) !important;
    font-family: 'Montserrat', sans-serif !important;
    font-weight: 600 !important;
    text-align: left !important;
    border-radius: 4px !important;
}
section[data-testid="stSidebar"] [data-testid="stPopover"] button:hover {
    border-color: #8B2C1A !important;
    color: #8B2C1A !important;
}

/* Checkboxes del filtro de organización */
section[data-testid="stSidebar"] [data-testid="stPopover"] button p,
section[data-testid="stSidebar"] [data-testid="stPopover"] button div,
section[data-testid="stSidebar"] [data-testid="stPopover"] button span {
    color: #003153 !important;
}

section[data-testid="stSidebar"] [data-testid="stPopover"] button p,
section[data-testid="stSidebar"] [data-testid="stPopover"] button div,
section[data-testid="stSidebar"] [data-testid="stPopover"] button span {
    color: #003153 !important;
}

</style>
""", unsafe_allow_html=True)

# CATÁLOGO DE ESTADOS
# Carátula y Destino de donativos escriben los estados distinto
# ("NUEVO LEON" vs "Nuevo León", "MEXICO" vs "Estado de México", "COAHUILA DE ZARAGOZA" vs "Coahuila"...).
# Todo se lleva a este catálogo para que el filtro muestre cada estado una sola vez.
import re
import unicodedata

ESTADOS = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas", "Chihuahua",
    "Ciudad de México", "Coahuila", "Colima", "Durango", "Estado de México", "Guanajuato", "Guerrero",
    "Hidalgo", "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
    "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", "Tamaulipas",
    "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
]
SIN_DATO = "Sin dato"
SIN_DESTINO = "Sin destino declarado"

def _clave_estado(t):
    t = "".join(c for c in unicodedata.normalize("NFKD", str(t)) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip().upper()

ALIAS_ESTADOS = {_clave_estado(e): e for e in ESTADOS}
ALIAS_ESTADOS.update({
    "MEXICO": "Estado de México",
    "COAHUILA DE ZARAGOZA": "Coahuila",
    "MICHOACAN DE OCAMPO": "Michoacán",
    "VERACRUZ DE IGNACIO DE LA LLAVE": "Veracruz",
    "DISTRITO FEDERAL": "Ciudad de México",
    "CDMX": "Ciudad de México",
})

def normalizar_estado(serie):
    def f(t):
        if pd.isna(t) or not str(t).strip():
            return SIN_DATO
        return ALIAS_ESTADOS.get(_clave_estado(t), str(t).strip().title())
    return serie.map(f)

# CARGA DE DATOS
# Carpeta del proyecto (donde está este archivo). Así funciona igual en tu Mac y en Streamlit Cloud.
BASE = Path(__file__).resolve().parent
# Los Excel unidos viven en <proyecto>/data. Para usar otra carpeta en local:
#   DONATARIAS_DATA="/ruta/a/dataet" streamlit run dashboard_donatarias.py
RUTA = os.environ.get("DONATARIAS_DATA", str(BASE / "data"))

@st.cache_data
def cargar_datos():
    generales = pd.read_excel(f"{RUTA}/Generales.xlsx")
    donativos = pd.read_excel(f"{RUTA}/Ingreso por donativos.xlsx")
    relacionados = pd.read_excel(f"{RUTA}/Ingresos relacionados.xlsx")
    no_relacionados = pd.read_excel(f"{RUTA}/Ingresos no relacionados.xlsx")
    gastos = pd.read_excel(f"{RUTA}/Gastos.xlsx")
    identidad = pd.read_excel(f"{RUTA}/Identidad organizacional.xlsx")
    fl_total_df = pd.read_excel(f"{RUTA}/flota_laboral_total.xlsx", index_col=0)
    sp_df = pd.read_excel(f"{RUTA}/Salario promedio.xlsx", index_col=0)
    dv_df = pd.read_excel(f"{RUTA}/dependencia_voluntariado.xlsx", index_col=0)
    cog_df = pd.read_excel(f"{RUTA}/costo_órgano_gubernamental.xlsx", index_col=0)
    cpb_df = pd.read_excel(f"{RUTA}/costo por beneficiario.xlsx", index_col=0)

    # Carátula → estado donador (sede de la donataria) y situación fiscal, uno por (Año, Rfc).
    # Un Rfc puede tener varios folios en el año: se queda el último enviado.
    caratula = pd.read_excel(f"{RUTA}/Carátula.xlsx")
    orden = ["Año", "Fecha de envío", "Folio"] if "Fecha de envío" in caratula.columns else ["Año", "Folio"]
    caratula = caratula.sort_values(orden).drop_duplicates(subset=["Año", "Rfc"], keep="last")
    caratula["Estado donador"] = normalizar_estado(caratula["Entidad federativa"])
    caratula["Situación fiscal"] = (
        caratula["Situación fiscal"].fillna("").astype(str).str.strip().str.capitalize().replace("", SIN_DATO)
    )
    caratula = caratula[["Año", "Rfc", "Estado donador", "Situación fiscal"]]

    # Destino de donativos → estados donde cada organización aplicó donativos (puede ser más de uno)
    destino = pd.read_excel(f"{RUTA}/Destino de donativos.xlsx", usecols=["Año", "Rfc", "Entidad federativa"])
    destino["Estado receptor"] = normalizar_estado(destino["Entidad federativa"])
    destino = destino[["Año", "Rfc", "Estado receptor"]].drop_duplicates()

    return (generales, donativos, relacionados, no_relacionados, gastos, identidad,
            fl_total_df, sp_df, dv_df, cog_df, cpb_df, caratula, destino)

(generales, donativos, relacionados, no_relacionados, gastos, identidad,
 fl_total_df, sp_df, dv_df, cog_df, cpb_df, caratula, destino) = cargar_datos()

LLAVE = ["Año", "Rfc"]  # ajustar 'ID' a la llave real

# PREPARACIÓN DE INDICADORES BASE 
don_efectivo = donativos.groupby(LLAVE)["Monto efectivo"].sum().reset_index()
don_especie = donativos.groupby(LLAVE)["Monto especie"].sum().reset_index()
ing_relacionados = relacionados.groupby(LLAVE)["Monto"].sum().reset_index().rename(columns={"Monto": "Ingresos relacionados"})
ing_no_relacionados = no_relacionados.groupby(LLAVE)["Monto"].sum().reset_index().rename(columns={"Monto": "Ingresos no relacionados"})

total_ingresos = (
    don_efectivo
    .merge(don_especie, on=LLAVE, how="outer")
    .merge(ing_relacionados, on=LLAVE, how="outer")
    .merge(ing_no_relacionados, on=LLAVE, how="outer")
    .fillna(0)
)

total_ingresos["Total Ingresos Anio Fiscal"] = (
    total_ingresos["Monto efectivo"]
    + total_ingresos["Monto especie"]
    + total_ingresos["Ingresos relacionados"]
    + total_ingresos["Ingresos no relacionados"]
)
total_ingresos["Total Donativos Recibidos"] = (
    total_ingresos["Monto efectivo"] + total_ingresos["Monto especie"]
)
total_ingresos["Dependencia de donativos"] = (
    total_ingresos["Total Donativos Recibidos"] / total_ingresos["Total Ingresos Anio Fiscal"]
).fillna(0)

gastos["Total Gastos"] = (
    gastos["Monto nacional operación"] + gastos["Monto nacional admin"]
    + gastos["Monto extranjero operación"] + gastos["Monto extranjero admin"]
)
total_gastos = gastos.groupby(LLAVE)["Total Gastos"].sum().reset_index()

total_ingresos = total_ingresos.merge(total_gastos, on=LLAVE, how="left")
total_ingresos["Total Gastos"] = total_ingresos["Total Gastos"].fillna(0)

total_ingresos["Sustentabilidad"] = (
    (total_ingresos["Total Ingresos Anio Fiscal"] - total_ingresos["Total Gastos"])
    / total_ingresos["Total Ingresos Anio Fiscal"]
)

total_ingresos["Sustentabilidad"] = (
    total_ingresos["Sustentabilidad"]
    .replace([float("inf"), -float("inf")], 0)
    .fillna(0)
)

def asignar_quintil(df):
    df = df.copy()
    df["Quintil de ingresos"] = pd.qcut(
        df["Total Ingresos Anio Fiscal"].rank(method="first", ascending=False),
        5,
        labels=["Q1", "Q2", "Q3", "Q4", "Q5"]
    )
    return df

# Un año a la vez (escrito así funciona en pandas 2 y 3; groupby().apply ya no conserva la columna "Año" en pandas 3)
total_ingresos = pd.concat([asignar_quintil(g) for _, g in total_ingresos.groupby("Año")], ignore_index=True)
total_ingresos = total_ingresos[total_ingresos["Año"] != 2026]  # sin datos aún

total_ingresos = total_ingresos.merge(
    identidad[["Año", "Rfc", "Identidad organizacional", "Total Beneficiarios", "Costo por beneficiario"]],
    on=["Año", "Rfc"], how="left"
)
total_ingresos["Identidad organizacional"] = total_ingresos["Identidad organizacional"].fillna("No clasificada")

total_ingresos = total_ingresos.merge(
    generales[["Año", "Rfc", "Razón social", "Actividad"]].drop_duplicates(subset=["Año", "Rfc"]),
    on=["Año", "Rfc"], how="left"
)

total_ingresos = total_ingresos.merge(caratula, on=["Año", "Rfc"], how="left")
total_ingresos["Estado donador"] = total_ingresos["Estado donador"].fillna(SIN_DATO)
total_ingresos["Situación fiscal"] = total_ingresos["Situación fiscal"].fillna(SIN_DATO)

# SIDEBAR — FILTROS GLOBALES

# HELPERS DE FILTROS
def filtro_popover(label, opciones, key):
    """Filtro estándar: caso base = todas seleccionadas, clic quita una."""
    if key not in st.session_state:
        st.session_state[key] = list(opciones)

    seleccionados = st.session_state[key]
    if len(seleccionados) == len(opciones):
        resumen = "Todos"
    elif len(seleccionados) == 0:
        resumen = "Ninguno"
    else:
        resumen = f"{len(seleccionados)} de {len(opciones)}"

    with st.sidebar.popover(f"{label}: {resumen}", width="stretch"):
        col_a, col_b = st.columns(2)
        if col_a.button("Todos", key=f"{key}_todos", width="stretch"):
            st.session_state[key] = list(opciones)
            st.rerun()
        if col_b.button("Ninguno", key=f"{key}_ninguno", width="stretch"):
            st.session_state[key] = []
            st.rerun()
        st.multiselect(" ", opciones, key=key, label_visibility="collapsed")

    return st.session_state[key]


def filtro_organizacion_popover(label, opciones_df, key):
    if key not in st.session_state:
        st.session_state[key] = []

    n_sel = len(st.session_state[key])
    resumen = "Todas" if n_sel == 0 else f"{n_sel} seleccionada(s)"

    with st.sidebar.popover(f"{label}: {resumen}", width="stretch"):
        busqueda = st.text_input(
            "Buscar", key=f"{key}_busqueda",
            placeholder="Escribe el nombre...", label_visibility="collapsed"
        )

        opciones_filtradas = opciones_df
        if busqueda:
            opciones_filtradas = opciones_df[
                opciones_df["Razón social"].str.contains(busqueda, case=False, na=False)
            ]

        if n_sel > 0:
            if st.button("Limpiar selección", key=f"{key}_limpiar", width="stretch"):
                st.session_state[key] = []
                st.rerun()

        MAX_MOSTRAR = 100
        total_resultados = len(opciones_filtradas)
        opciones_mostrar = opciones_filtradas.head(MAX_MOSTRAR)
        if total_resultados > MAX_MOSTRAR:
            st.caption(f"Mostrando {MAX_MOSTRAR} de {total_resultados} — afina la búsqueda para ver más.")
        elif total_resultados == 0:
            st.caption("Sin resultados.")

        # Contenedor con altura fija y scroll propio -> el popover deja de crecer
        # sin límite, así cabe hacia abajo y no se voltea.
        with st.container(height=280):
            for _, fila in opciones_mostrar.iterrows():
                rfc, nombre = fila["Rfc"], fila["Razón social"]
                marcado = rfc in st.session_state[key]
                nuevo = st.checkbox(nombre, value=marcado, key=f"{key}_chk_{rfc}")
                if nuevo and not marcado:
                    st.session_state[key].append(rfc)
                    st.rerun()
                elif not nuevo and marcado:
                    st.session_state[key].remove(rfc)
                    st.rerun()

    return st.session_state[key]

# =========================================================
# SIDEBAR — FILTROS GLOBALES
# =========================================================
st.sidebar.header("Filtros")

anios_disponibles = sorted(total_ingresos["Año"].unique())
anios_sel = filtro_popover("Año", anios_disponibles, key="anios_sel")

quintiles_sel = filtro_popover("Quintil de ingresos", ["Q1", "Q2", "Q3", "Q4", "Q5"], key="quintiles_sel")

identidades_disponibles = sorted(total_ingresos["Identidad organizacional"].dropna().unique())
identidad_sel = filtro_popover("Identidad organizacional", identidades_disponibles, key="identidad_sel")

actividades_disponibles = sorted(total_ingresos["Actividad"].dropna().unique())
actividad_sel = filtro_popover("Actividad", actividades_disponibles, key="actividad_sel")

def ordenar_estados(valores):
    """Orden del catálogo; lo que no esté en él (Sin dato, Sin destino...) al final."""
    valores = set(valores)
    return [e for e in ESTADOS if e in valores] + sorted(valores - set(ESTADOS))

estados_donador_disponibles = ordenar_estados(
    set(total_ingresos["Estado donador"]) | set(caratula["Estado donador"])
)
estado_donador_sel = filtro_popover("Estado donador", estados_donador_disponibles, key="estado_donador_sel")

estados_receptor_disponibles = ordenar_estados(set(destino["Estado receptor"]) | {SIN_DESTINO})
estado_receptor_sel = filtro_popover("Estado receptor", estados_receptor_disponibles, key="estado_receptor_sel")

situaciones_disponibles = sorted(set(total_ingresos["Situación fiscal"]) | set(caratula["Situación fiscal"]))
situacion_sel = filtro_popover("Situación fiscal", situaciones_disponibles, key="situacion_sel")

orgs_disponibles = (
    total_ingresos[["Rfc", "Razón social"]]
    .dropna()
    .drop_duplicates(subset=["Rfc"])
    .sort_values("Razón social")
)
organizacion_sel = filtro_organizacion_popover("Organización", orgs_disponibles, key="organizacion_sel")

if not anios_sel:
    st.warning("Selecciona al menos un año en los filtros.")
    st.stop()

anio_sel = max(anios_sel)

df_anio = total_ingresos[total_ingresos["Año"] == anio_sel]
df_filtrado = df_anio[
    df_anio["Quintil de ingresos"].isin(quintiles_sel)
    & df_anio["Identidad organizacional"].isin(identidad_sel)
    & df_anio["Actividad"].isin(actividad_sel)
]
if organizacion_sel:
    df_filtrado = df_filtrado[df_filtrado["Rfc"].isin(organizacion_sel)]

df_filtrado = df_filtrado[
    df_filtrado["Estado donador"].isin(estado_donador_sel)
    & df_filtrado["Situación fiscal"].isin(situacion_sel)
]

def filtrar_estado_receptor(df):
    """Deja las organizaciones que aplicaron donativos en al menos uno de los estados receptores elegidos.
    Las que no declararon destino solo pasan si "Sin destino declarado" está seleccionado."""
    if set(estado_receptor_sel) >= set(estados_receptor_disponibles):
        return df                                    # caso base: todos seleccionados → no filtra
    dest_anio = destino[destino["Año"] == anio_sel]
    rfcs_ok = set(dest_anio.loc[dest_anio["Estado receptor"].isin(estado_receptor_sel), "Rfc"])
    if SIN_DESTINO in estado_receptor_sel:
        rfcs_ok |= set(df["Rfc"]) - set(dest_anio["Rfc"])
    return df[df["Rfc"].isin(rfcs_ok)]

df_filtrado = filtrar_estado_receptor(df_filtrado)

# Organizaciones del año que están en Generales pero sin ingresos registrados
# (no existen en total_ingresos, por eso no tienen quintil ni identidad)
g_anio = generales[generales["Año"] == anio_sel].drop_duplicates(subset=["Año", "Rfc"])
sin_ingresos = g_anio[~g_anio["Rfc"].isin(df_anio["Rfc"])]

sin_ingresos = sin_ingresos[sin_ingresos["Actividad"].isin(actividad_sel)]
if organizacion_sel:
    sin_ingresos = sin_ingresos[sin_ingresos["Rfc"].isin(organizacion_sel)]

sin_ingresos = sin_ingresos.merge(caratula, on=["Año", "Rfc"], how="left")
sin_ingresos["Estado donador"] = sin_ingresos["Estado donador"].fillna(SIN_DATO)
sin_ingresos["Situación fiscal"] = sin_ingresos["Situación fiscal"].fillna(SIN_DATO)
sin_ingresos = sin_ingresos[
    sin_ingresos["Estado donador"].isin(estado_donador_sel)
    & sin_ingresos["Situación fiscal"].isin(situacion_sel)
]
sin_ingresos = filtrar_estado_receptor(sin_ingresos)

# No tienen quintil, así que solo cuentan si el filtro de quintil está completo.
# Tampoco tienen identidad, así que se tratan como "No clasificada".
if len(quintiles_sel) < 5 or "No clasificada" not in identidad_sel:
    sin_ingresos = sin_ingresos.iloc[0:0]

# =========================================================
# TÍTULO Y KPIs (Indicadores 2 y 3)
# =========================================================

if len(anios_sel) > 1:
    st.caption(f"Los indicadores de corte anual muestran {anio_sel}, el año más reciente de tu selección. El Gráfico 4 usa todos los años seleccionados.")

st.title("Dashboard Donatarias")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    total_kpi = df_filtrado["Total Ingresos Anio Fiscal"].sum()
    st.metric("Total de ingresos año fiscal", f"${total_kpi/1_000_000:,.1f}M MXN")

with col_kpi2:
    dependencia_prom = df_filtrado["Dependencia de donativos"].mean()
    st.metric("Dependencia de donativos promedio", f"{dependencia_prom:.1%}")

with col_kpi3:
    n_orgs = df_filtrado["Rfc"].nunique() + sin_ingresos["Rfc"].nunique()
    st.metric("Organizaciones activas", f"{n_orgs:,}")

# =========================================================
# TABS
# =========================================================
tab1, tab2, tab3, tab4 = st.tabs(["Estructura financiera", "Fuerza laboral y eficiencia", "Sankey de movimiento de recursos", "Acerca de"])

# ---------------------------------------------------------
# TAB 1 — Indicadores 1, 4, 10, 11 (grid 2x2)
# ---------------------------------------------------------
with tab1:
    fila1_col1, fila1_col2 = st.columns(2)
    fila2_col1, fila2_col2 = st.columns(2)

    # --- Gráfico 1: Quintil de ingresos (treemap) ---
    with fila1_col1:
        monto_quintil = (
            df_anio.groupby("Quintil de ingresos", observed=True)["Total Ingresos Anio Fiscal"]
            .sum()
            .reindex(["Q1", "Q2", "Q3", "Q4", "Q5"])
            .reset_index()
        )
        monto_quintil.columns = ["Quintil", "Monto total"]

        fig1 = px.treemap(
            monto_quintil,
            path=["Quintil"],
            values="Monto total",
            color="Quintil",
            color_discrete_map={
                "Q1": COLOR_ROJO_PROFUNDO, "Q2": COLOR_ROJO_OXIDO,
                "Q3": COLOR_AZUL_PRUSIA, "Q4": COLOR_GRIS_GRAFITO, "Q5": "#8FA9B8"
            },
            title=f"Monto de ingresos por quintil ({anio_sel})"
        )
        fig1.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", textfont_size=14)
        fig1 = estilizar_figura(fig1, altura=390)
        st.plotly_chart(fig1, width="stretch")

    # --- Gráfico 4: Origen de donativo por identidad fiscal ---
    with fila1_col2:
        # Traer el quintil de cada organización/año desde total_ingresos
        donativos_quintil = donativos.merge(
            total_ingresos[["Año", "Rfc", "Quintil de ingresos"]],
            on=["Año", "Rfc"],
            how="left"
        )

        # Aplicar el filtro de quintiles del sidebar (no el de año, aquí el año va en el eje X)
        donativos_quintil = donativos_quintil[
            donativos_quintil["Quintil de ingresos"].isin(quintiles_sel)
        ]

        donativos_quintil["Monto donativo"] = (
            donativos_quintil["Monto efectivo"] + donativos_quintil["Monto especie"]
        )

        origen_por_anio = (
            donativos_quintil.groupby(["Año", "Donante"])["Monto donativo"]
            .sum()
            .reset_index()
        )

        fig4 = px.line(
            origen_por_anio,
            x="Año",
            y="Monto donativo",
            color="Donante",
            markers=True,
            title="Origen de donativo por identidad fiscal (monto por año)"
        )
        fig4.update_layout(yaxis_title="Monto (MXN)")
        # Etiquetas más cortas en la leyenda ("Donativo Persona Física Nacional" → "Persona Física Nacional")
        fig4.for_each_trace(lambda t: t.update(name=t.name.replace("Donativo ", "")))
        fig4 = estilizar_figura(fig4, altura=390)
        # Las líneas arrancan en la parte baja → arriba a la izquierda queda libre para la leyenda.
        # Un poco de aire arriba (~15 %) para que la leyenda no tape la línea más alta al inicio de la serie.
        if not origen_por_anio.empty:
            fig4.update_yaxes(range=[0, origen_por_anio["Monto donativo"].max() * 1.15])
        fig4 = leyenda_compacta(
            fig4,
            [(t.name, t.line.color) for t in fig4.data],
            titulo="Tipo de donante",
            simbolo="━",
        )

        st.plotly_chart(fig4, width="stretch")

    # --- Gráfico 10: Sustentabilidad anual de flujo presupuestal (bubble chart) ---
    with fila2_col1:
        bins_sust = [-float("inf"), -0.30, -0.10, 0, 0.10, float("inf")]
        labels_sust = ["Déficit crítico", "Déficit significativo", "Déficit moderado", "Superávit moderado", "Superávit saludable"]

        df_filtrado_sust = df_filtrado.copy()
        df_filtrado_sust["Categoría"] = pd.cut(
            df_filtrado_sust["Sustentabilidad"], bins=bins_sust, labels=labels_sust
        )

        conteo_sust = df_filtrado_sust["Categoría"].value_counts().reindex(labels_sust).reset_index()
        conteo_sust.columns = ["Categoría", "Número de organizaciones"]

        fig10 = px.bar(
            conteo_sust, x="Categoría", y="Número de organizaciones",
            title=f"Sustentabilidad de flujo presupuestal ({anio_sel})",
            text="Número de organizaciones",
            color="Categoría",
            color_discrete_map={
                "Déficit crítico": COLOR_ROJO_PROFUNDO,
                "Déficit significativo": COLOR_ROJO_OXIDO,
                "Déficit moderado": COLOR_GRIS_GRAFITO,
                "Superávit moderado": "#5B8DA6",
                "Superávit saludable": COLOR_AZUL_PRUSIA
            }
        )

        labels_sust_visual = [
            "Déficit<br>crítico",
            "Déficit<br>significativo",
            "Déficit<br>moderado",
            "Superávit<br>moderado",
            "Superávit<br>saludable"
        ]

        fig10.update_layout(showlegend=False, xaxis_title="", yaxis_title="Número de organizaciones")

        fig10 = estilizar_figura(fig10, altura=390)
    
        fig10.update_xaxes(
            tickangle=0,
            automargin=True,
            tickfont=dict(
                family="Montserrat, sans-serif",
                size=11,
                color=COLOR_GRIS_GRAFITO
            )
        )


        st.plotly_chart(fig10, width="stretch")
    # --- Gráfico 11: Identidad organizacional ---
    with fila2_col2:
        df_g11 = df_anio[df_anio["Identidad organizacional"].isin(identidad_sel)].copy()
        df_g11 = df_g11[df_g11["Costo por beneficiario"] > 0]

        # Tamaño pseudo-log: comprime la escala sin perder el orden relativo
        df_g11["Tamaño (log)"] = np.log1p(df_g11["Total Beneficiarios"].clip(lower=0))

        colores_identidad = {
            "Salamandra": COLOR_ROJO_PROFUNDO,
            "Axolote con rendimiento de Salamandra": COLOR_AZUL_PRUSIA,
            "Axolote": COLOR_ROJO_OXIDO,
            "Crisálida": COLOR_GRIS_GRAFITO,
            "No clasificada": "#C9C9C9",
        }

        # Translucidez: cada burbuja tiene relleno muy transparente y borde un poco más marcado.
        # Donde se enciman muchas, el color se acumula y se ve más intenso; una burbuja sola se ve tenue.
        ALPHA_RELLENO = 0.18
        ALPHA_BORDE = 0.55
        TAMANO_MAX = 26          # antes 40: burbujas más chicas = menos encimadas

        # Dibujar primero las burbujas grandes para que las chicas queden encima y no se pierdan
        df_g11 = df_g11.sort_values("Tamaño (log)", ascending=False)

        fig11 = px.scatter(
            df_g11,
            x="Total Ingresos Anio Fiscal",
            y="Costo por beneficiario",
            size="Tamaño (log)",
            color="Identidad organizacional",
            color_discrete_map=colores_identidad,
            log_x=True,
            log_y=True,
            size_max=TAMANO_MAX,
            hover_name="Rfc",
            hover_data={"Total Beneficiarios": ":,.0f", "Tamaño (log)": False,
                        "Total Ingresos Anio Fiscal": ":$,.0f", "Costo por beneficiario": ":$,.2f"},
            title=f"Identidad organizacional ({anio_sel})",
            labels={
                "Total Ingresos Anio Fiscal": "Total de ingresos ($MXN)",
                "Costo por beneficiario": "Costo por beneficiario"
            }
        )

        def translucir(t):
            base = colores_identidad.get(t.name, "#C9C9C9")
            t.update(
                marker=dict(
                    color=hex_a_rgba(base, ALPHA_RELLENO),
                    line=dict(color=hex_a_rgba(base, ALPHA_BORDE), width=0.6),
                    opacity=1,
                ),
            )
        fig11.for_each_trace(translucir)

        fig11 = estilizar_figura(fig11, altura=390)
        # Ningún punto puede tener costo por beneficiario mayor que sus ingresos (beneficiarios ≥ 1),
        # así que la esquina superior izquierda siempre está vacía: ahí va la leyenda.
        fig11 = leyenda_compacta(
            fig11,
            [(t.name, colores_identidad.get(t.name, "#C9C9C9")) for t in fig11.data],
        )

        st.plotly_chart(fig11, width="stretch")
# ---------------------------------------------------------
# TAB 2 — Indicadores 5, 6, 7, 8, 9 (grid 2x2 + fila completa)
# ---------------------------------------------------------
# RFCs que pasan todos los filtros en el año seleccionado.
# sin_ingresos viene del bloque del KPI de organizaciones activas
# (si no lo agregaste, quita ese término).
rfcs_validos = set(df_filtrado["Rfc"]) | set(sin_ingresos["Rfc"])

def filtrar_wide(df):
    return df.loc[df.index.isin(rfcs_validos)]

with tab2:
    fila1_col1, fila1_col2 = st.columns(2)
    fila2_col1, fila2_col2 = st.columns(2)
    st.caption(f"{len(rfcs_validos):,} organizaciones con los filtros actuales ({anio_sel})")

    # --- Gráfico 5: Total de fuerza laboral ---
    with fila1_col1:
        fig5 = px.histogram(
            filtrar_wide(fl_total_df),
            x=anio_sel,
            nbins=30,
            title=f"Distribución de la fuerza laboral en el año {anio_sel}",
            text_auto=True,
            labels={"count": "Cantidad de asociaciones", "year": "Fuerza laboral total"}
        )
        fig5.update_traces(xbins=dict(start=0, end=300, size=10))
        fig5.update_xaxes(title_text="Fuerza laboral total")
        fig5.update_yaxes(title_text="Cantidad de asociaciones")

        fig5 = estilizar_figura(fig5, altura=390)

        st.plotly_chart(
            fig5,
            width="stretch",
            config={"displayModeBar": False}
        )

    # --- Gráfico 6: Costo por empleado ---
    with fila1_col2:
        fig6 = px.histogram(
            filtrar_wide(sp_df),
            x=anio_sel,
            title=f"Salario promedio por empleado en el año {anio_sel}",
            text_auto=True
        )
        fig6.update_xaxes(title_text="Salario promedio $MXN")
        fig6.update_yaxes(title_text="Cantidad de asociaciones")
        fig6.update_traces(xbins=dict(start=0, end=500000, size=2000))

        fig6.add_vrect(x0=0, x1=50000, annotation_text="Precario", annotation_position="top left",
                        fillcolor="red", opacity=0.25, line_width=0)
        fig6.add_vrect(x0=50000, x1=150000, annotation_text="Básico", annotation_position="top left",
                        fillcolor="red", opacity=0.15, line_width=0)
        fig6.add_vrect(x0=150000, x1=300000, annotation_text="Profesional", annotation_position="top left",
                        fillcolor="yellow", opacity=0.15, line_width=0)
        fig6.add_vrect(x0=300000, x1=500000, annotation_text="Consolidado", annotation_position="top left",
                        fillcolor="green", opacity=0.25, line_width=0)

        fig6 = estilizar_figura(fig6, altura=390)

        st.plotly_chart(fig6, width="stretch")

    # --- Gráfico 7: Dependencia de voluntariado ---
    with fila2_col1:
        fig7 = px.histogram(
            filtrar_wide(dv_df) * 100, 
            x=anio_sel,
            log_y=True,
            title=f"Dependencia del voluntariado en el año {anio_sel}"
        )

        fig7.add_vrect(x0=0, x1=20, annotation_text="Profesionalizada", annotation_position="top left",
                        fillcolor="green", opacity=0.15, line_width=0)
        fig7.add_vrect(x0=20, x1=50, annotation_text="Mixta", annotation_position="top left",
                        fillcolor="yellow", opacity=0.15, line_width=0)
        fig7.add_vrect(x0=50, x1=80, annotation_text="Dependiente", annotation_position="top left",
                        fillcolor="red", opacity=0.15, line_width=0)
        fig7.add_vrect(x0=80, x1=100, annotation_text="Casi exclusivamente voluntaria", annotation_position="top left",
                        fillcolor="red", opacity=0.25, line_width=0)

        fig7.update_traces(xbins=dict(start=0, end=100))
        fig7.update_xaxes(title_text="Dependencia de voluntariado (%)")
        fig7.update_yaxes(title_text="Número de asociaciones")
        fig7 = estilizar_figura(fig7, altura=390)

        st.plotly_chart(fig7, width="stretch")

    # --- Gráfico 8: Costo del órgano de gobierno ---
    with fila2_col2:
        fig8 = px.histogram(
            filtrar_wide(cog_df) * 100, 
            x=anio_sel,
            title=f"Costo del órgano de gobierno (% del ingreso total) en el año {anio_sel}",
            text_auto=True,
            log_y=True
        )

        fig8.add_vrect(x0=0, x1=5, annotation_text="Bajo", annotation_position="top right",
                        fillcolor="green", opacity=0.15, line_width=0)
        fig8.add_vrect(x0=5, x1=15, annotation_text="Moderado", annotation_position="top right",
                        fillcolor="yellow", opacity=0.15, line_width=0)
        fig8.add_vrect(x0=15, x1=30, annotation_text="Alto", annotation_position="top right",
                        fillcolor="red", opacity=0.15, line_width=0)
        fig8.add_vrect(x0=30, x1=100, annotation_text="Muy alto", annotation_position="top right",
                        fillcolor="red", opacity=0.25, line_width=0)

        fig8.update_traces(xbins=dict(start=0, end=100, size=5))
        fig8.update_yaxes(title_text="Número de asociaciones")
        fig8.update_xaxes(title_text="%")
        fig8 = estilizar_figura(fig8, altura=390)

        st.plotly_chart(fig8, width="stretch")

    # --- Gráfico 9: Costo por beneficiario (fila completa, ancho total) ---
    fig9 = px.histogram(
        filtrar_wide(cpb_df)[anio_sel],
        log_y=True,
        title=f"Histograma de costo por beneficiario {anio_sel}",
        text_auto=True
    )
    fig9.update_traces(xbins=dict(start=0, end=500000, size=5000))
    fig9.update_xaxes(title_text="Costo por beneficiario $MXN (escala logarítmica)")
    fig9.update_yaxes(title_text="Número de asociaciones")
    fig9.update_layout(showlegend=False)
    fig9 = estilizar_figura(fig9, altura=390)

    st.plotly_chart(fig9, width="stretch")

with tab3:
    @st.cache_data
    def cargar_html(path, mtime):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    ruta_sankey = BASE / "sankey.html"
    if ruta_sankey.exists():
        html_sankey = cargar_html(str(ruta_sankey), ruta_sankey.stat().st_mtime)
        st.iframe(html_sankey, height=800)
    else:
        st.warning("No se encontró sankey.html. Genéralo con: python generar_sankey.py --anios 2025")

# ---------------------------------------------------------
# TAB 4 — Acerca de (fuente, hojas del Excel, variables e indicadores)
# ---------------------------------------------------------
with tab4:
    mostrar_acerca_de(generales)
