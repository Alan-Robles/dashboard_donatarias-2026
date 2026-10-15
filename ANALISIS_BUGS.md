# Análisis de Fallos en dashboard_donatarias.py

## Resumen
Se detectaron y corrigieron **3 problemas críticos** relacionados con la variable `anio_sel` (selección de año) que causaban que el dashboard no funcionara correctamente.

---

## 🔴 Problema 1: Coma faltante en `filtro_multiselect()` (Línea ~385)

### Descripción
La función `filtro_multiselect()` tenía una coma faltante en la llamada a `st.sidebar.multiselect()`.

### Código original (INCORRECTO)
```python
return st.sidebar.multiselect(
    " ",
    opciones,
    default=st.session_state[key]  # ❌ FALTA COMA
    key=key,
    label_visibility="collapsed"
)
```

### Impacto
- Error de sintaxis Python
- El código no podía ni compilarse
- Esta era la falla principal alrededor de la línea 689

### Solución
```python
return st.sidebar.multiselect(
    " ",
    opciones,
    key=key,  # ✅ Se eliminó default y se añadió coma
    label_visibility="collapsed"
)
```

---

## 🔴 Problema 2: Lógica de validación incorrecta (Línea ~428)

### Descripción
La condición de validación usaba `or` cuando debería usar `and`. Esto causaba que el dashboard siempre se detuviera, incluso cuando había años disponibles.

### Código original (INCORRECTO)
```python
if not anio_sel or anios_disponibles:  # ❌ LÓGICA INVERTIDA
    st.warning("Selecciona al menos un año en los filtros.")
    st.stop()
```

**Problema de lógica:**
- `or anios_disponibles` siempre es `True` si hay años disponibles
- Entonces el `if` siempre entra en el bloque y detiene la ejecución
- El dashboard nunca podía mostrar datos

### Solución
```python
if not anios_disponibles:  # ✅ Primero validar que existan años
    st.warning("No hay años disponibles en los datos.")
    st.stop()
if not anio_sel:  # ✅ Luego validar que el usuario haya seleccionado alguno
    st.warning("Selecciona al menos un año en los filtros.")
    st.stop()
```

---

## 🟠 Problema 3: Uso incorrecto de `anio_sel` como nombre de columna (Línea ~699)

### Descripción
El código pasaba `anio_sel` (una lista como `[2025, 2024]`) directamente como nombre de columna en los dataframes de gráficos 5-9. Esto es incorrecto porque:
- `anio_sel` es una **lista de años seleccionados**, no un nombre de columna
- Los dataframes (`fl_total_df`, `sp_df`, etc.) tienen **años como columnas** (ej: `2024`, `2025`)

### Código original (INCORRECTO)
```python
# Gráfico 5
fig5 = px.histogram(
    fl_total_df,
    x=anio_sel,  # ❌ anio_sel es [2024, 2025], no es nombre de columna
    nbins=30,
    title=f"Distribución de la fuerza laboral en el año {anio_sel}",
)

# Gráfico 8
fig8 = px.histogram(
    cog_df * 100,
    x=anio_sel,  # ❌ IDEM ERROR
    title="Costo de órgano de gobierno (%)"
)

# Gráfico 9
fig9 = px.histogram(
    cpb_df[anio_sel],  # ❌ Intenta acceder con lista como índice
    log_y=True,
    title=f"Histograma de costo por beneficiario {anio_sel}",
)
```

### Por qué `anio_sel` está vacío
El problema descrito ocurría porque:
1. El código no compilaba (falta de coma)
2. Incluso si compilara, la lógica de validación lo detenía
3. `anio_sel` nunca llegaba a estos gráficos con valor real

### Impacto
- KeyError: Las columnas año no existen en los dataframes
- Los gráficos 5-9 no se mostraban
- El dashboard se detenía

### Solución
Se creó una función helper `preparar_metricas_por_anio()` que:
1. Mapea años a nombres de columna correctos
2. Filtra solo los años seleccionados
3. Convierte el dataframe a formato largo (tidy data)
4. Permite usar años en los ejes X sin confundir con nombres de columna

```python
def preparar_metricas_por_anio(df, anios, nombre_valor="Valor"):
    """Convierte dataframe con años como columnas a formato largo."""
    columnas_por_anio = {str(columna).strip(): columna for columna in df.columns}
    anios_seleccionados = [(str(anio).strip(), str(anio).strip()) for anio in anios]
    
    # Validar que los años existan
    columnas_faltantes = [
        anio for anio, _ in anios_seleccionados if anio not in columnas_por_anio
    ]
    if columnas_faltantes:
        raise KeyError(
            f"No hay columnas para los años {columnas_faltantes} "
            f"en los datos de {nombre_valor}."
        )
    
    # Seleccionar columnas y convertir a formato largo
    datos = df[[columnas_por_anio[anio] for anio, _ in anios_seleccionados]].copy()
    datos.columns = [anio for anio, _ in anios_seleccionados]
    return datos.melt(var_name="Año", value_name=nombre_valor).dropna(subset=[nombre_valor])
```

**Uso:**
```python
# Gráfico 5 (CORREGIDO)
datos_fl_total = preparar_metricas_por_anio(fl_total_df, anio_sel, "Fuerza laboral total")
fig5 = px.histogram(
    datos_fl_total,
    x="Fuerza laboral total",  # ✅ Nombre de columna real
    color="Año",                # ✅ Años como variable categórica
    nbins=30,
    title=f"Distribución de la fuerza laboral en el año {anio_sel}",
)
```

---

## Resumen de Cambios

| Línea | Problema | Solución |
|-------|----------|----------|
| ~385 | Coma faltante en multiselect | Se añadió coma y se removió parámetro `default` redundante |
| ~428 | Lógica `or` invertida | Se dividió en dos condiciones separadas con lógica correcta |
| ~633-755 | `anio_sel` usado como columna | Se creó función helper + se aplicó a gráficos 5-9 |

---

## Validación

✅ **El código ahora:**
1. Compila sin errores de sintaxis
2. Valida correctamente que existan años disponibles
3. Valida que el usuario seleccione al menos un año
4. Convierte correctamente los años seleccionados a datos para los gráficos
5. Permite múltiples años en los histogramas con diferenciación por color

---

## Próximas mejoras recomendadas
- Agregar logging para debugging
- Validar que todos los años estén presentes en todos los datasets
- Considerar usar un estado centralizado para los filtros (Redux, etc.)
