#IMPORTAMOS LAS HERRAMIENTAS
import pandas as pd
import os

#PASAMOS LA RUTA 
RUTA_ALEX="C:\\Users\\Diego\\Downloads\\proyecto geostat\\dashboard_donatarias-2026\\files"

#LOS ARCHIVOS 
archivos= {
    "Generales.xlsx": "Generales.parquet",
    "Ingreso por donativos.xlsx": "Ingreso_por_donativos.parquet",
    "Ingresos relacionados.xlsx": "Ingresos_relacionados.parquet",
    "Ingresos no relacionados.xlsx": "Ingresos_no_relacionados.parquet",
    "Gastos.xlsx": "Gastos.parquet",
    "Identidad organizacional.xlsx": "Identidad_organizacional.parquet",
    "flota_laboral_total.xlsx": "flota_laboral_total.parquet",
    "Salario promedio.xlsx": "Salario_promedio.parquet",
    "dependencia_voluntariado.xlsx": "dependencia_voluntariado.parquet",
    "costo_órgano_gubernamental.xlsx": "costo_organo_gubernamental.parquet",
    "costo por beneficiario.xlsx": "costo_por_beneficiario.parquet"
}
for xlsx,parquet in archivos.items():
    path_xlsx=os.path.join(RUTA_ALEX,xlsx)
    path_parquet=os.path.join(RUTA_ALEX,parquet)
    #LEEMOS EL ARCHIVO EXCEL 
    df_excel=pd.read_excel(path_xlsx)
    df_excel.to_parquet(path_parquet, engine="pyarrow", index=False)
    print(f"Archivo {xlsx} convertido a {parquet} exitosamente.")
print("¡CONVERSIÓN A PAQUETE TERMINADA CON ÉXITO!")