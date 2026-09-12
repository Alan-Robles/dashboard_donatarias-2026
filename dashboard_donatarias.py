import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import plotly.io as pio

# =========================================================
# IDENTIDAD VISUAL
# =========================================================
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
div[data-testid="stMetricLabel"] {
    font-family: 'Montserrat', sans-serif !important;
    color: #2C2C2C !important;
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
</style>
""", unsafe_allow_html=True)

# =========================================================
# CARGA DE DATOS
# =========================================================
RUTA = "/Users/alanrobles/Documents/ALAN/GEOSTATS/dontarias/dataet"

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
    return generales, donativos, relacionados, no_relacionados, gastos, identidad, fl_total_df, sp_df, dv_df, cog_df, cpb_df

generales, donativos, relacionados, no_relacionados, gastos, identidad, fl_total_df, sp_df, dv_df, cog_df, cpb_df = cargar_datos()

LLAVE = ["Año", "Rfc"]  # ajustar 'ID' a la llave real

# =========================================================
# PREPARACIÓN DE INDICADORES BASE 
# =========================================================
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

total_ingresos = total_ingresos.groupby("Año", group_keys=False).apply(asignar_quintil)
total_ingresos = total_ingresos[total_ingresos["Año"] != 2026]  # sin datos aún

total_ingresos = total_ingresos.merge(
    identidad[["Año", "Rfc", "Identidad organizacional", "Total Beneficiarios", "Costo por beneficiario"]],
    on=["Año", "Rfc"], how="left"
)
total_ingresos["Identidad organizacional"] = total_ingresos["Identidad organizacional"].fillna("No clasificada")

# =========================================================
# SIDEBAR — FILTROS GLOBALES
# =========================================================
st.sidebar.header("Filtros")

anios_disponibles = sorted(total_ingresos["Año"].unique())
anio_sel = st.sidebar.selectbox("Año", anios_disponibles, index=len(anios_disponibles) - 1)

quintiles_sel = st.sidebar.multiselect(
    "Quintil de ingresos",
    ["Q1", "Q2", "Q3", "Q4", "Q5"],
    default=["Q1", "Q2", "Q3", "Q4", "Q5"]
)

identidades_disponibles = sorted(total_ingresos["Identidad organizacional"].dropna().unique())
identidad_sel = st.sidebar.multiselect(
    "Identidad organizacional",
    identidades_disponibles,
    default=identidades_disponibles
)

df_anio = total_ingresos[total_ingresos["Año"] == anio_sel]
df_filtrado = df_anio[
    df_anio["Quintil de ingresos"].isin(quintiles_sel)
    & df_anio["Identidad organizacional"].isin(identidad_sel)
]

# =========================================================
# TÍTULO Y KPIs (Indicadores 2 y 3)
# =========================================================
st.title("Dashboard Donatarias")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

with col_kpi1:
    total_kpi = df_filtrado["Total Ingresos Anio Fiscal"].sum()
    st.metric("Total de ingresos año fiscal (Indicador 2)", f"${total_kpi:,.0f} MXN")

with col_kpi2:
    dependencia_prom = df_filtrado["Dependencia de donativos"].mean()
    st.metric("Dependencia de donativos promedio (Indicador 3)", f"{dependencia_prom:.1%}")

with col_kpi3:
    n_orgs = df_filtrado["Rfc"].nunique()
    st.metric("Organizaciones activas", f"{n_orgs:,}")

# =========================================================
# TABS
# =========================================================
tab1, tab2 = st.tabs(["Estructura financiera", "Fuerza laboral y eficiencia"])

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
            title=f"1. Monto de ingresos por quintil ({anio_sel})"
        )
        fig1.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", textfont_size=14)
        st.plotly_chart(fig1, use_container_width=True)

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
            title="4. Origen de donativo por identidad fiscal (monto por año)"
        )
        fig4.update_layout(yaxis_title="Monto (MXN)", legend_title="Tipo de donante")
        st.plotly_chart(fig4, use_container_width=True)

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
            title=f"10. Sustentabilidad de flujo presupuestal ({anio_sel})",
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
        fig10.update_layout(showlegend=False, xaxis_title="", yaxis_title="Número de organizaciones")
        st.plotly_chart(fig10, use_container_width=True)
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

        fig11 = px.scatter(
            df_g11,
            x="Total Ingresos Anio Fiscal",
            y="Costo por beneficiario",
            size="Tamaño (log)",
            color="Identidad organizacional",
            color_discrete_map=colores_identidad,
            log_x=True,
            log_y=True,
            size_max=40,
            opacity=0.75,
            hover_data={"Total Beneficiarios": True, "Tamaño (log)": False},  # mostrar el valor real en hover
            title=f"11. Identidad organizacional ({anio_sel})",
            labels={
                "Total Ingresos Anio Fiscal": "Total de ingresos (MXN, escala log)",
                "Costo por beneficiario": "Costo por beneficiario (MXN, escala log)"
            }
        )
        fig11.update_traces(marker=dict(line=dict(width=0)))  # sin borde en las burbujas
        st.plotly_chart(fig11, use_container_width=True)
# ---------------------------------------------------------
# TAB 2 — Indicadores 5, 6, 7, 8, 9 (grid 2x2 + fila completa)
# ---------------------------------------------------------
with tab2:
    fila1_col1, fila1_col2 = st.columns(2)
    fila2_col1, fila2_col2 = st.columns(2)

    # --- Gráfico 5: Total de fuerza laboral ---
    with fila1_col1:
        fig5 = px.histogram(
            fl_total_df,
            x=anio_sel,
            nbins=30,
            title=f"Distribución de la fuerza laboral en el año {anio_sel}",
            text_auto=True,
            labels={"count": "Cantidad de asociaciones", "year": "Fuerza laboral total"}
        )
        fig5.update_traces(xbins=dict(start=0, end=300, size=10))
        fig5.update_xaxes(title_text="Fuerza laboral total")
        fig5.update_yaxes(title_text="Cantidad de asociaciones")
        st.plotly_chart(fig5, use_container_width=True)

    # --- Gráfico 6: Costo por empleado ---
    with fila1_col2:
        fig6 = px.histogram(
            sp_df,
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

        st.plotly_chart(fig6, use_container_width=True)

    # --- Gráfico 7: Dependencia de voluntariado ---
    with fila2_col1:
        fig7 = px.histogram(
            dv_df * 100,
            x=anio_sel,
            log_y=True,
            title="Histograma de dependencia del voluntariado"
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
        st.plotly_chart(fig7, use_container_width=True)

    # --- Gráfico 8: Costo del órgano de gobierno ---
    with fila2_col2:
        fig8 = px.histogram(
            cog_df * 100,
            x=anio_sel,
            title="Costo de órgano de gobierno (% del ingreso total)",
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
        st.plotly_chart(fig8, use_container_width=True)

    # --- Gráfico 9: Costo por beneficiario (fila completa, ancho total) ---
    fig9 = px.histogram(
        cpb_df[anio_sel],
        log_y=True,
        title=f"Histograma de costo por beneficiario {anio_sel}",
        text_auto=True
    )
    fig9.update_traces(xbins=dict(start=0, end=500000, size=5000))
    fig9.update_xaxes(title_text="Costo por beneficiario $MXN (escala logarítmica)")
    fig9.update_yaxes(title_text="Número de asociaciones")
    fig9.update_layout(showlegend=False)
    st.plotly_chart(fig9, use_container_width=True)