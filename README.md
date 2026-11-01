# Dashboard Donatarias

Dashboard en Streamlit sobre los informes de transparencia de las **donatarias autorizadas** que publica el SAT
([consulta pública](https://eu2-por-pro-don-net-cons.azurewebsites.net/Consulta/Acceso?ReturnUrl=%2FConsulta%2FTransparencia)),
ejercicios 2020–2025.

## Estructura

```
dashboard_donatarias.py   App de Streamlit (archivo principal para el deploy)
acerca_de.py              Pestaña "Acerca de": fuente, hojas, variables e indicadores
generar_sankey.py         Genera sankey.html (pestaña 3) a partir de data/
sankey_template.html      Plantilla HTML/JS del Sankey y su tarjeta de detalle
sankey.html               Sankey ya generado (lo lee el dashboard)
data/                     Excel unidos por hoja (columna "Año") e indicadores derivados
notebooks/                Preparación de datos y análisis de clusters
requirements.txt          Dependencias para Streamlit Cloud
```

## Correr en local

```bash
pip install -r requirements.txt
streamlit run dashboard_donatarias.py
```

Para leer los datos desde otra carpeta: `DONATARIAS_DATA="/ruta/a/dataet" streamlit run dashboard_donatarias.py`

## Actualizar el Sankey

```bash
python generar_sankey.py --anios 2025      # lee data/ y escribe sankey.html
```

## Flujo de preparación de datos (notebooks/)

1. `denue.ipynb`
2. `dontarias.ipynb` — une los Excel de cada año por hoja (agrega la columna `Año`)
3. `dashboard_dontarias.ipynb` — indicadores derivados e identidad organizacional (K-Means)
4. `busqueda_clusters.ipynb` — comparación de combinaciones de variables para los clusters
