"""
Pestaña "Acerca de" del Dashboard Donatarias.

Explica de dónde salen los datos, qué contiene cada hoja del informe de transparencia del SAT,
qué significa cada variable y cómo se construyen los indicadores del dashboard.

Uso (desde dashboard_donatarias.py):
    from acerca_de import mostrar_acerca_de
    with tab4:
        mostrar_acerca_de(generales)
"""
import re

import streamlit as st

URL_FUENTE = "https://eu2-por-pro-don-net-cons.azurewebsites.net/Consulta/Acceso?ReturnUrl=%2FConsulta%2FTransparencia"

# ---------------------------------------------------------------------------
# Diccionario de datos: una entrada por hoja del Excel
#   (nombre, ¿la usa el dashboard?, descripción, [(columna, significado), ...])
# Las columnas comunes (Año, Rfc, Razón social, Folio) se explican una sola vez.
# ---------------------------------------------------------------------------
COLUMNAS_COMUNES = [
    ("Año", "Ejercicio fiscal que se reporta (lo agregamos al unir los archivos de cada año). "
            "El informe de 2020 se presentó en 2021, por eso su folio termina en “/2021”."),
    ("Rfc", "Registro Federal de Contribuyentes: la clave única de la organización ante el SAT. "
            "Es lo que permite unir la información de todas las hojas."),
    ("Razón social", "Nombre legal de la organización (AC = Asociación Civil, IAP / IBP = Institución de Asistencia / Beneficencia Privada, SC = Sociedad Civil)."),
    ("Folio", "Número del informe de transparencia presentado (TRANS######/AAAA)."),
]

HOJAS = [
    ("Carátula", True,
     "Datos de identificación del informe: quién lo presentó, cuándo y su situación ante el SAT. Hay un renglón por informe.",
     [("Fecha de envío", "Día y hora en que la organización presentó el informe (la mayoría en mayo del año siguiente)."),
      ("Entidad federativa", "Estado del domicilio fiscal de la organización. En el dashboard es el **estado donador**."),
      ("Desconcentrada", "Oficina regional del SAT que le corresponde a la organización."),
      ("Situación fiscal", "Estado del RFC: **Activo**, **Suspendido** (dejó de operar temporalmente) o **Inactivo**. Es un filtro del dashboard."),
      ("Autorización extranjero", "Si también puede recibir donativos deducibles desde el extranjero."),
      ("Rubro", "Tipo de autorización (asistencial, educativa, cultural, ecológica, etc.)."),
      ("Estatus", "Situación de la autorización: **Autorizada**, **Pérdida de vigencia** (no cumplió alguna obligación), "
                  "**Revocada** (el SAT se la retiró), **Transmisión de patrimonio** (está cerrando y entrega sus bienes a otra donataria), "
                  "**No autorizada omisa**, **Suspendida**.")]),

    ("Generales", True,
     "Perfil de la organización y un resumen de su balance financiero al cierre del año.",
     [("Misión / Valores / Url", "Textos y sitio web que la propia organización declara."),
      ("Actividad", "Actividad principal autorizada (Asistenciales, Educativa, Culturales, Desarrollo social, Ecológicos...). Es un filtro del dashboard."),
      ("Actividades adicionales", "Otras actividades autorizadas además de la principal."),
      ("Activo circulante", "Recursos que se convierten en dinero en menos de un año: efectivo, bancos, cuentas por cobrar."),
      ("Activo fijo", "Bienes duraderos: inmuebles, vehículos, mobiliario, equipo."),
      ("Activo diferido", "Pagos hechos por adelantado (seguros, rentas) que se irán usando con el tiempo."),
      ("Total del estado de ingresos", "⚠️ Pese al nombre, **no son los ingresos del año**: en los datos es la suma de los tres activos. "
                                       "El dashboard calcula los ingresos con otras hojas (ver Indicadores)."),
      ("Pasivo", "Deudas y obligaciones de pago de la organización."),
      ("Patrimonio", "Lo que realmente le pertenece: activos menos pasivo."),
      ("Dictamina", "Si sus estados financieros fueron revisados (dictaminados) por un contador público registrado. Pocas lo hacen (~3 %)."),
      ("Rfc CP / Nombre CP / Número CP", "Datos del contador público que dictaminó.")]),

    ("Ingreso por donativos", True,
     "Donativos que **recibió** la organización, separados por tipo de donante. Base del Gráfico 4.",
     [("Donante", "Quién dio el donativo: **Persona Física** (un individuo), **Persona Moral** (una empresa o asociación) "
                  "o **Sector Público** (gobierno), cada uno **Nacional** o **Extranjero**."),
      ("Monto efectivo", "Donativos en dinero (MXN)."),
      ("Monto especie", "Donativos en bienes (alimentos, ropa, equipo...), valuados en pesos.")]),

    ("Donativos otorgados", True,
     "Donativos que la organización **entregó** a otras organizaciones. Se usa en la tarjeta del Sankey (pestañas Razón social, Actividad y Estado).",
     [("Rfc destinatario / Razón social destinatario", "Organización que recibió el donativo."),
      ("Sin datos", "Indica si la organización declaró no tener información del destinatario."),
      ("Monto efectivo / Monto especie / Total", "Monto entregado en dinero, en bienes y la suma de ambos.")]),

    ("Transmisión de patrimonio", False,
     "Cuando una donataria pierde su autorización o se disuelve, debe entregar su patrimonio a otra donataria autorizada. Aquí se registra a quién y cuánto.",
     [("Rfc destinatario / Razón social destinatario", "Organización que recibió el patrimonio."),
      ("Monto efectivo / Monto especie / Total", "Valor transmitido en dinero, en bienes y total.")]),

    ("Órgano de gobierno", True,
     "Integrantes del consejo directivo o patronato (presidente, secretario, tesorero, vocales). Un renglón por persona.",
     [("Nombre integrante / Puesto", "Persona y cargo que ocupa."),
      ("Monto salario", "Remuneración anual que recibió por ese cargo (muchos cargos son honorarios, sin pago)."),
      ("Tipo integrante", "Nacional o Extranjero.")]),

    ("Nómina", True,
     "Personal que trabaja en la organización. Base de los gráficos 5, 6 y 7.",
     [("Plantilla laboral", "Número de empleados con sueldo."),
      ("Voluntarios", "Número de personas que colaboran sin sueldo."),
      ("Monto salarios", "Total pagado en sueldos durante el año.")]),

    ("Ingresos relacionados", True,
     "Ingresos que **no son donativos** pero vienen de actividades propias de su objeto social.",
     [("Concepto", "Tipo de ingreso: **cuotas de recuperación** (lo que pagan los beneficiarios por un servicio, normalmente simbólico), "
                   "intereses, apoyos o estímulos de gobierno, cuotas de sus integrantes, renta de inmuebles, venta de activos, regalías..."),
      ("Monto", "Monto del ingreso (MXN)."),
      ("Especifique", "Detalle libre cuando el concepto es “Otros”.")]),

    ("Ingresos no relacionados", True,
     "Ingresos por actividades **ajenas** a su fin social (por ejemplo, vender productos sin relación con su causa). La ley les permite tenerlos solo de forma limitada.",
     [("Concepto libre", "Descripción escrita por la organización."),
      ("Monto", "Monto del ingreso (MXN).")]),

    ("Inversiones financieras", False,
     "Dinero que la organización tiene invertido (fondos, pagarés, acciones...).",
     [("Concepto / Especifique", "Tipo de inversión y su detalle."),
      ("Monto nacional / Monto extranjero", "Monto invertido en México y fuera del país.")]),

    ("Destino de donativos", True,
     "En qué se usaron los donativos: cada proyecto o programa, dónde se aplicó y a cuántas personas benefició. "
     "Base del Sankey, del costo por beneficiario y del filtro de estado receptor.",
     [("Concepto", "Descripción del proyecto o actividad."),
      ("Sector beneficiado", "A quién se dirigió (niños, adultos mayores, personas con discapacidad...). Es texto libre, por eso hay muchas variantes."),
      ("Monto", "Monto aplicado en ese proyecto (MXN)."),
      ("Número de beneficiados", "Personas atendidas, según la organización. Una misma persona puede contarse en varios proyectos."),
      ("Entidad federativa / Municipio", "Dónde se aplicó el donativo. En el dashboard es el **estado receptor**.")]),

    ("Actividades legislación", False,
     "Solo para organizaciones que intentaron influir en leyes o políticas públicas (cabildeo). Son muy pocas.",
     [("Materia objeto de estudio / Legislación que se pretende promover", "Tema y ley que buscaban promover o modificar."),
      ("Legisladores con quienes se realice las actividades de promoción", "Con qué legisladores trabajaron."),
      ("Sector beneficiaria / Grupos promoventes", "A quién beneficiaría y quién impulsó el estudio."),
      ("Materiales, datos o información / Otra información / Conclusiones", "Evidencia usada y resultado.")]),

    ("Actividad apoyo prod-artesano", False,
     "Apoyos económicos entregados directamente a productores agrícolas o artesanos.",
     [("Razón social beneficiario / Nacionalidad / Tipo beneficiario", "Quién recibió el apoyo y si es artesano o productor agrícola."),
      ("Apoyo otorgado", "Monto entregado (MXN)."),
      ("Ingreso anterior", "Ingreso que tenía la persona antes del apoyo."),
      ("Entidad federativa / Municipio", "Dónde vive el beneficiario.")]),

    ("Gastos", True,
     "En qué gastó la organización durante el año. Se usa para calcular la sustentabilidad.",
     [("Concepto / Especifique", "Tipo de gasto (sueldos, renta, electricidad, teléfono, otros...)."),
      ("Monto nacional operación", "Gasto en México para **cumplir su misión** (programas, apoyos, materiales)."),
      ("Monto nacional admin", "Gasto en México para **administrar** la organización (oficina, contabilidad, servicios)."),
      ("Monto extranjero operación / admin", "Lo mismo, pero gastado fuera del país.")]),

    ("Control de donativos", False,
     "Seguimiento de los donativos en especie (bienes): cuánto se recibió y qué pasó con ello.",
     [("Id de donativo especie", "Identificador del donativo; une esta hoja con “Sector beneficiado” y “Donatarias destino”."),
      ("Bienes recibidos / Cantidad recibida", "Qué bienes llegaron y cuántas unidades."),
      ("Cant cuotas de recuperación / Monto de Cuotas de recuperación", "Unidades entregadas cobrando una cuota y lo que se recaudó."),
      ("Cantidad en destrucción / Fecha de destrucción", "Bienes que se destruyeron (caducados, dañados) y cuándo."),
      ("Remanente", "Unidades que quedaron sin entregar.")]),

    ("Sector beneficiado", False,
     "A qué grupos de personas se entregaron los bienes en especie (por cada Id de donativo).",
     [("Sector beneficiado", "Grupo atendido (texto libre)."),
      ("Cantidad", "Unidades entregadas a ese grupo.")]),

    ("Donatarias destino", False,
     "Bienes en especie que la organización pasó a otras donatarias.",
     [("Rfc donataria destino / Donataria destino", "Organización que recibió los bienes (“PUBLICO EN GENERAL” cuando se repartieron directamente)."),
      ("Cantidad", "Unidades entregadas.")]),
]

# ---------------------------------------------------------------------------
# Indicadores construidos por el dashboard
# ---------------------------------------------------------------------------
INDICADORES = [
    ("Total de ingresos del año",
     "Donativos en efectivo + donativos en especie + ingresos relacionados + ingresos no relacionados.",
     "KPI superior, Gráfico 1, Gráfico 11"),
    ("Dependencia de donativos",
     "Donativos recibidos ÷ total de ingresos. 100 % = vive solo de donativos; 0 % = se financia con otras fuentes.",
     "KPI superior"),
    ("Quintil de ingresos",
     "Cada año se ordenan las organizaciones por ingresos y se dividen en 5 grupos del mismo tamaño. "
     "**Q1** = el 20 % con más ingresos; **Q5** = el 20 % con menos.",
     "Gráfico 1, filtro"),
    ("Sustentabilidad",
     "(Ingresos − gastos) ÷ ingresos. Positivo = le sobró dinero (superávit); negativo = gastó más de lo que ingresó (déficit). "
     "Categorías: déficit crítico (< −30 %), significativo (−30 a −10 %), moderado (−10 a 0 %), superávit moderado (0 a 10 %), saludable (> 10 %).",
     "Gráfico 10"),
    ("Fuerza laboral total",
     "Empleados con sueldo + voluntarios.",
     "Gráfico 5"),
    ("Salario promedio",
     "Total pagado en sueldos ÷ número de empleados (anual). Rangos: precario (< $50 mil), básico ($50–150 mil), "
     "profesional ($150–300 mil), consolidado (> $300 mil).",
     "Gráfico 6"),
    ("Dependencia del voluntariado",
     "Voluntarios ÷ fuerza laboral total. Profesionalizada (< 20 %), mixta (20–50 %), dependiente (50–80 %), casi exclusivamente voluntaria (> 80 %).",
     "Gráfico 7"),
    ("Costo del órgano de gobierno",
     "Remuneraciones pagadas al consejo directivo ÷ total de ingresos. Bajo (< 5 %), moderado (5–15 %), alto (15–30 %), muy alto (> 30 %).",
     "Gráfico 8"),
    ("Costo por beneficiario",
     "Total de ingresos ÷ número de beneficiados. Cuánto “cuesta” atender a una persona; más bajo = más alcance con los mismos recursos.",
     "Gráfico 9, Gráfico 11"),
    ("Organizaciones activas",
     "Organizaciones que presentaron informe en el año y cumplen los filtros, incluidas las que no reportaron ingresos.",
     "KPI superior"),
]

IDENTIDADES = [
    ("Crisálida", "#2C2C2C",
     "Organizaciones pequeñas o en formación: ingresos bajos y operación todavía limitada. Como la crisálida, están en una etapa de transformación."),
    ("Axolote", "#B15E2E",
     "Organizaciones de tamaño medio que se mantienen en esa escala, con un costo por beneficiario relativamente alto. "
     "El ajolote conserva rasgos juveniles toda su vida."),
    ("Axolote con rendimiento de Salamandra", "#003153",
     "Organizaciones de tamaño medio que logran **mucho alcance**: atienden a muchas personas con un costo por beneficiario bajo, "
     "comparable al de las organizaciones grandes."),
    ("Salamandra", "#8B2C1A",
     "Organizaciones grandes y consolidadas: los mayores ingresos, programas de mayor escala y costo por beneficiario alto."),
    ("No clasificada", "#C9C9C9",
     "Organizaciones que no pudieron clasificarse porque no reportaron ingresos (o fueron menores a $100) o no reportaron beneficiarios."),
]

GLOSARIO = [
    ("Donataria autorizada", "Organización civil o fideicomiso sin fines de lucro al que el SAT autoriza a recibir donativos que el donante puede deducir de sus impuestos."),
    ("Deducible", "Que el donante puede restar de sus ingresos al calcular su impuesto. Por eso el Estado exige transparencia: es dinero por el que se dejó de cobrar impuestos."),
    ("Ejercicio fiscal", "El año que se reporta (enero a diciembre)."),
    ("Persona física / moral", "Física = un individuo. Moral = una entidad con personalidad jurídica propia (empresa, asociación, fundación)."),
    ("Efectivo / especie", "Efectivo = dinero. Especie = bienes o servicios, valuados en pesos."),
    ("Cuota de recuperación", "Pago, normalmente simbólico, que hace un beneficiario por un servicio o bien."),
    ("Objeto social", "La finalidad para la que se constituyó la organización (su “misión” legal)."),
    ("Patrimonio", "Lo que le pertenece a la organización una vez descontadas sus deudas."),
]

NOTAS = [
    "**La información es autodeclarada.** Cada organización llena su propio informe; el SAT lo publica tal cual. Solo una minoría tiene estados financieros dictaminados.",
    "**Montos nominales.** Las cifras están en pesos de cada año, sin ajustar por inflación; las comparaciones entre años incluyen ese efecto.",
    "**Beneficiarios.** El número de beneficiados lo reporta cada organización por proyecto, así que una persona puede contarse más de una vez y el costo por beneficiario puede salir subestimado.",
    "**Nombres de estados.** Carátula y Destino escriben los estados distinto (“NUEVO LEON” vs “Nuevo León”, “MEXICO” vs “Estado de México”); el dashboard los unifica en un solo catálogo.",
    "**Dos fuentes de flujos.** Los montos del Sankey vienen de “Destino de donativos” (dónde se aplicó el dinero) y su tarjeta de detalle usa también “Donativos otorgados” (a quién se le dio); son hojas distintas, por eso sus totales no coinciden.",
    "**Texto libre.** Campos como “Sector beneficiado” o “Concepto” los escribe cada organización, con variaciones de ortografía y formato.",
]


def _md(texto):
    """Escapa '$' para que Streamlit no lo interprete como fórmula matemática (LaTeX)."""
    return texto.replace("$", r"\$")


def _html(texto):
    """Para bloques HTML: **negritas** → <b> y '$' como entidad HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", texto).replace("$", "&#36;")


def _tabla(filas):
    """Tabla markdown de 2 columnas sin romperse con caracteres especiales."""
    cuerpo = "\n".join(f"| **{_md(a)}** | {_md(b).replace('|', '/')} |" for a, b in filas)
    return "| Variable | Qué significa |\n|---|---|\n" + cuerpo


def mostrar_acerca_de(generales=None):
    st.header("Acerca de este dashboard")

    # -----------------------------------------------------------------------
    st.subheader("¿De dónde salen los datos?")
    st.markdown(f"""
Los datos provienen de la **[Consulta pública de transparencia de Donatarias Autorizadas]({URL_FUENTE})** del
**Servicio de Administración Tributaria (SAT)**.

Las **donatarias autorizadas** son organizaciones sin fines de lucro (asociaciones civiles, fundaciones, instituciones de
asistencia privada, fideicomisos) a las que el SAT permite recibir **donativos deducibles de impuestos**. A cambio, la
**Ley del Impuesto sobre la Renta (artículo 82, fracción VI)** les obliga a presentar cada año, normalmente en mayo,
una **Declaración informativa de transparencia** sobre su patrimonio y el uso y destino de los donativos que recibieron.
Esa información queda a disposición del público en general; no presentarla puede costarles la autorización.

El SAT publica un archivo de Excel por año con **17 hojas**. Este dashboard usa los ejercicios **2020 a 2025**:
los archivos de cada año se unieron hoja por hoja, agregando una columna **Año**.
""")

    if generales is not None and "Año" in generales.columns:
        conteo = (generales.drop_duplicates(["Año", "Rfc"]).groupby("Año").size()
                  .rename("Organizaciones que presentaron informe").to_frame().T)
        conteo.columns = [str(c) for c in conteo.columns]
        conteo = conteo.map(lambda v: f"{v:,}")
        st.dataframe(conteo, width="stretch")

    # -----------------------------------------------------------------------
    st.subheader("Cómo usar el dashboard")
    st.markdown("""
- **Filtros (barra lateral):** año, quintil de ingresos, identidad organizacional, actividad, estado donador, estado receptor,
  situación fiscal y organización. Los indicadores de corte anual muestran el año más reciente de tu selección.
- **Estructura financiera:** de dónde vienen los ingresos, de quién vienen los donativos, si las organizaciones cubren sus
  gastos y qué perfil (identidad) tienen.
- **Fuerza laboral y eficiencia:** cuántas personas trabajan, cuánto ganan, qué tanto dependen de voluntarios, cuánto cuesta
  su órgano de gobierno y cuánto cuesta atender a cada beneficiario.
- **Sankey de movimiento de recursos:** cómo se mueve el dinero del **estado donde está la organización** al **estado y
  municipio donde se aplicó**. Haz clic en un flujo para ver el detalle de quién donó a quién.
""")

    # -----------------------------------------------------------------------
    st.subheader("Qué contiene cada hoja del Excel")
    st.markdown("Las hojas marcadas con 📊 se usan en el dashboard. Todas comparten estas columnas:")
    st.markdown(_tabla(COLUMNAS_COMUNES))
    st.write("")
    for nombre, usada, descripcion, columnas in HOJAS:
        etiqueta = f"{'📊 ' if usada else ''}{nombre}"
        with st.expander(etiqueta):
            st.markdown(_md(descripcion))
            st.markdown(_tabla(columnas))

    # -----------------------------------------------------------------------
    st.subheader("Indicadores que calcula el dashboard")
    st.markdown("Estas variables no vienen tal cual en el Excel: se construyen combinando hojas.")
    st.markdown(
        "| Indicador | Cómo se calcula | Dónde aparece |\n|---|---|---|\n"
        + "\n".join(f"| **{n}** | {_md(f)} | {d} |" for n, f, d in INDICADORES)
    )

    # -----------------------------------------------------------------------
    st.subheader("Identidad organizacional")
    st.markdown("""
Es una clasificación propia, hecha con un algoritmo de agrupamiento (**K-Means**) que reúne a las organizaciones con un
perfil parecido según seis variables: quintil de ingresos, total de ingresos, total de beneficiarios, costo por beneficiario,
dependencia de donativos y sustentabilidad. Los nombres son una metáfora del ciclo de vida de una organización:
""")
    for nombre, color, texto in IDENTIDADES:
        st.markdown(
            f"<div style='display:flex;gap:10px;align-items:flex-start;margin:4px 0'>"
            f"<span style='color:{color};font-size:20px;line-height:1.1'>●</span>"
            f"<div><b>{nombre}.</b> {_html(texto)}</div></div>",
            unsafe_allow_html=True,
        )
    st.caption("En el Gráfico 11 cada círculo es una organización: eje horizontal = total de ingresos, "
               "eje vertical = costo por beneficiario, tamaño = número de beneficiarios.")

    # -----------------------------------------------------------------------
    st.subheader("Glosario")
    st.markdown("\n".join(f"- **{t}:** {d}" for t, d in GLOSARIO))

    # -----------------------------------------------------------------------
    st.subheader("Notas y limitaciones")
    st.markdown("\n".join(f"- {n}" for n in NOTAS))
