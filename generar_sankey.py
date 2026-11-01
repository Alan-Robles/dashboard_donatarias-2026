#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_sankey.py — arma `sankey.html` (Sankey de flujo de donativos) CON desglose por flujo.

El HTML final lo carga el dashboard de Streamlit tal cual (components.html), no hay que
cambiar nada en dashboard_donatarias.py. Solo hay que regenerar el archivo cuando cambien los datos.

Uso
    python generar_sankey.py --ruta "/Users/alanrobles/Documents/ALAN/GEOSTATS/dontarias/dataet" --anios 2026
    python generar_sankey.py --ruta ./dataet --anios 2025 2026 --salida sankey.html

Lee los Excel que ya produce tu notebook de unión de años (Carátula.xlsx, Destino de donativos.xlsx,
Generales.xlsx, Ingreso por donativos.xlsx; todos con columna "Año").
Si no existen, usa los archivos por año (2020.xlsx, 2021.xlsx, ...) con sus hojas originales.

Cómo se construye cada flujo
    Estado emisor    = "Entidad federativa" de Carátula (donde está la donataria que reporta)
    Estado receptor  = "Entidad federativa" de Destino de donativos
    Municipio        = "Municipio" de Destino de donativos
    Monto            = "Monto" de Destino de donativos
    Llave de unión   = (Año, Folio)

Todo el desglose del clic por Municipio y Sector sale de las MISMAS filas que los links, así que el
monto de un flujo siempre cuadra con esas tablas.

Pestañas Razón social / Actividad / Estado (quién DONA × quién RECIBE)
    Salen de la hoja "Donativos otorgados" (donante → razón social destinataria, columna "Total").
    Estado y actividad del donante: Carátula / Generales por (Año, Folio).
    Estado y actividad del destinatario: Carátula / Generales por RFC (último año disponible); si el
    destinatario no presenta informe → "Destinatario no declarante".
    Esta hoja NO es la de "Destino de donativos", por eso sus montos no cuadran con los del Sankey.
    Si la hoja no existe, esas pestañas avisan que falta y el resto funciona igual.
"""
import argparse
import json
import re
import unicodedata
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
PLANTILLA = HERE / "sankey_template.html"
TOP_SECTORES = 40          # "Sector beneficiado" es texto libre: se conservan los N más grandes, el resto → "Otros sectores"
OTROS_SECTORES = "Otros sectores"
SIN_DATO = "Sin dato"

_xls_cache = {}


# ───────────────────────────── lectura ─────────────────────────────
def leer_hoja(ruta: Path, hoja: str, anios):
    """Hoja ya unida (RUTA/<hoja>.xlsx con columna Año) o, si no existe, hoja de cada RUTA/<año>.xlsx."""
    f = ruta / f"{hoja}.xlsx"
    if f.exists():
        df = pd.read_excel(f)
        return df if anios is None else df[df["Año"].isin(anios)].copy()
    partes = []
    for a in anios:
        fa = ruta / f"{a}.xlsx"
        if fa not in _xls_cache:
            _xls_cache[fa] = pd.ExcelFile(fa)
        d = _xls_cache[fa].parse(hoja)
        d.insert(0, "Año", a)
        partes.append(d)
    return pd.concat(partes, ignore_index=True)


def anio_mas_reciente(ruta: Path):
    f = ruta / "Carátula.xlsx"
    if f.exists():
        return [int(pd.read_excel(f, usecols=["Año"])["Año"].max())]
    años = sorted(int(p.stem) for p in ruta.glob("*.xlsx") if re.fullmatch(r"\d{4}", p.stem))
    if not años:
        raise FileNotFoundError(f"No encontré Carátula.xlsx ni archivos AAAA.xlsx en {ruta}")
    return [años[-1]]


# ───────────────────────────── limpieza ─────────────────────────────
def titulo(s: pd.Series) -> pd.Series:
    """Mismo criterio que el Sankey original: 'CIUDAD DE MEXICO' → 'Ciudad De Mexico'."""
    return s.fillna("").astype(str).str.strip().str.title().replace("", SIN_DATO)


def sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", t) if not unicodedata.combining(c))


# Carátula y Destino de donativos escriben los estados distinto ("NUEVO LEON" vs "Nuevo León",
# "MEXICO" vs "Estado de México", "COAHUILA DE ZARAGOZA" vs "Coahuila"...). Mismo catálogo que el dashboard.
ESTADOS = [
    "Aguascalientes", "Baja California", "Baja California Sur", "Campeche", "Chiapas", "Chihuahua",
    "Ciudad de México", "Coahuila", "Colima", "Durango", "Estado de México", "Guanajuato", "Guerrero",
    "Hidalgo", "Jalisco", "Michoacán", "Morelos", "Nayarit", "Nuevo León", "Oaxaca", "Puebla",
    "Querétaro", "Quintana Roo", "San Luis Potosí", "Sinaloa", "Sonora", "Tabasco", "Tamaulipas",
    "Tlaxcala", "Veracruz", "Yucatán", "Zacatecas",
]
_clave_estado = lambda t: re.sub(r"\s+", " ", sin_acentos(str(t))).strip().upper()
ALIAS_ESTADOS = {_clave_estado(e): e for e in ESTADOS}
ALIAS_ESTADOS.update({
    "MEXICO": "Estado de México", "COAHUILA DE ZARAGOZA": "Coahuila", "MICHOACAN DE OCAMPO": "Michoacán",
    "VERACRUZ DE IGNACIO DE LA LLAVE": "Veracruz", "DISTRITO FEDERAL": "Ciudad de México", "CDMX": "Ciudad de México",
})


def estado(s: pd.Series) -> pd.Series:
    """Nombre canónico del estado; lo que no esté en el catálogo queda en formato título."""
    return s.map(lambda t: SIN_DATO if pd.isna(t) or not str(t).strip()
                 else ALIAS_ESTADOS.get(_clave_estado(t), str(t).strip().title()))


def agrupar_sectores(sec: pd.Series, monto: pd.Series) -> pd.Series:
    """Unifica variantes de escritura y deja solo los TOP_SECTORES con más monto."""
    clave = sec.fillna("").astype(str).map(lambda t: re.sub(r"\s+", " ", sin_acentos(t)).strip().upper())
    # etiqueta visible = variante más frecuente de cada clave, en formato título
    visible = (pd.DataFrame({"k": clave, "raw": sec.fillna("").astype(str).str.strip()})
               .groupby("k")["raw"].agg(lambda x: x.value_counts().index[0]).str.title())
    top = monto.groupby(clave).sum().sort_values(ascending=False).head(TOP_SECTORES).index
    etiqueta = clave.map(lambda k: SIN_DATO if k == "" else (visible[k] if k in top else OTROS_SECTORES))
    return etiqueta


def monto_sin_destino(car_sin_dest: pd.DataFrame, ruta: Path, anios) -> pd.DataFrame:
    """
    >>> AJUSTA AQUÍ si tu definición de "Monto sin destino" es otra <<<
    Definición usada: donativos RECIBIDOS (efectivo + especie) de las donatarias que presentaron
    Carátula pero no declararon ningún destino de donativos. Devuelve (Año, Folio, monto).
    """
    rec = leer_hoja(ruta, "Ingreso por donativos", anios)
    rec["monto"] = rec["Monto efectivo"].fillna(0) + rec["Monto especie"].fillna(0)
    rec = rec.groupby(["Año", "Folio"], as_index=False)["monto"].sum()
    return car_sin_dest.merge(rec, on=["Año", "Folio"], how="left").fillna({"monto": 0})


# ───────────────────────────── donativos otorgados (donante → destinatario) ─────────────────────────────
NO_DECLARANTE = "Destinatario no declarante"


def construir_otorgados(ruta: Path, anios, car, gen, nombres, llave_des):
    """Filas [estado_dona, estado_recibe, rs_dona, rs_recibe, act_dona, act_recibe, monto, sin_destino].
    Devuelve (dict de diccionarios + filas) o None si la hoja no existe."""
    try:
        ot = leer_hoja(ruta, "Donativos otorgados", anios)
    except Exception as e:                       # hoja o archivo inexistente
        print(f"AVISO: no pude leer 'Donativos otorgados' ({type(e).__name__}); las pestañas Razón social / "
              f"Actividad / Estado mostrarán que falta esa hoja.")
        return None
    ot = ot.copy()
    if "Total" in ot.columns:
        ot["monto"] = ot["Total"].fillna(0).astype(float)
    else:
        ot["monto"] = ot["Monto efectivo"].fillna(0) + ot["Monto especie"].fillna(0)
    ot = ot[ot["monto"] > 0]

    # donante: estado y actividad por (Año, Folio)
    ot = ot.merge(car[["Año", "Folio", "o"]], on=["Año", "Folio"], how="left")
    ot = ot.merge(gen[["Año", "Folio", "act"]], on=["Año", "Folio"], how="left")
    ot["eo"] = ot["o"].fillna(SIN_DATO)
    ot["ao"] = ot["act"].fillna(SIN_DATO)
    # sin destino declarado = el folio del donante no tiene filas en Destino de donativos
    ot = ot.merge(llave_des.assign(_t=1), on=["Año", "Folio"], how="left")
    ot["unk"] = ot["_t"].isna().astype(int)

    # destinatario: estado y actividad por RFC (último año disponible)
    est_rfc = car.sort_values("Año").drop_duplicates("Rfc", keep="last").set_index("Rfc")["o"]
    act_rfc = gen.sort_values("Año").drop_duplicates("Rfc", keep="last").set_index("Rfc")["act"]
    ot["er"] = ot["Rfc destinatario"].map(est_rfc).fillna(NO_DECLARANTE)
    ot["ar"] = ot["Rfc destinatario"].map(act_rfc).fillna(NO_DECLARANTE)

    # razón social por RFC (dona y recibe comparten diccionario); nombre del destinatario si no declara
    nom = nombres.to_dict()
    for r, n in zip(ot["Rfc destinatario"], ot["Razón social destinatario"]):
        nom.setdefault(r, str(n).strip())
    for r, n in zip(ot["Rfc"], ot["Razón social"]):
        nom.setdefault(r, str(n).strip())
    rfcs = sorted(set(ot["Rfc"].dropna()) | set(ot["Rfc destinatario"].dropna()))
    etiquetas = [nom.get(r, r) for r in rfcs]
    dup = pd.Series(etiquetas).duplicated(keep=False)
    R2 = [f"{e} ({r})" if d else e for e, r, d in zip(etiquetas, rfcs, dup)]
    iR2 = {r: i for i, r in enumerate(rfcs)}

    E = sorted(set(ot["eo"]) | set(ot["er"]))
    A2 = sorted(set(ot["ao"]) | set(ot["ar"]))
    iE = {v: i for i, v in enumerate(E)}
    iA2 = {v: i for i, v in enumerate(A2)}
    ot["c_eo"] = ot["eo"].map(iE); ot["c_er"] = ot["er"].map(iE)
    ot["c_ro"] = ot["Rfc"].map(iR2); ot["c_rr"] = ot["Rfc destinatario"].map(iR2)
    ot["c_ao"] = ot["ao"].map(iA2); ot["c_ar"] = ot["ar"].map(iA2)
    g = (ot.groupby(["c_eo", "c_er", "c_ro", "c_rr", "c_ao", "c_ar", "unk"], as_index=False)["monto"].sum())
    filas = [[a, b, c, d, e, f, round(m, 2), u] for a, b, c, d, e, f, u, m in
             zip(g["c_eo"], g["c_er"], g["c_ro"], g["c_rr"], g["c_ao"], g["c_ar"], g["unk"], g["monto"])]
    return {"E": E, "R2": R2, "A2": A2, "ot": filas, "noDecl": NO_DECLARANTE}, float(ot["monto"].sum())


# ───────────────────────────── construcción ─────────────────────────────
def construir_raw(ruta: Path, anios):
    car = leer_hoja(ruta, "Carátula", anios).drop_duplicates(["Año", "Folio"])
    des = leer_hoja(ruta, "Destino de donativos", anios)
    gen = leer_hoja(ruta, "Generales", anios).drop_duplicates(["Año", "Folio"])

    # Carátula: estado emisor por folio
    car["o"] = estado(car["Entidad federativa"])
    gen["act"] = titulo(gen["Actividad"])

    # Filas de detalle (una por renglón de Destino de donativos)
    f = des.merge(car[["Año", "Folio", "o"]], on=["Año", "Folio"], how="left")
    f = f.merge(gen[["Año", "Folio", "act"]], on=["Año", "Folio"], how="left")
    f["o"] = f["o"].fillna(SIN_DATO)
    f["act"] = f["act"].fillna(SIN_DATO)
    f["d"] = estado(f["Entidad federativa"])
    f["m"] = titulo(f["Municipio"])
    f["monto"] = f["Monto"].fillna(0).astype(float)
    f["benef"] = f["Número de beneficiados"].fillna(0).astype(float)
    f["sec"] = agrupar_sectores(f["Sector beneficiado"], f["monto"])

    # Razón social por RFC (la más reciente que aparezca)
    nombres = (pd.concat([des[["Año", "Rfc", "Razón social"]], gen[["Año", "Rfc", "Razón social"]]])
               .dropna().sort_values("Año").drop_duplicates("Rfc", keep="last").set_index("Rfc")["Razón social"]
               .astype(str).str.strip())

    # Folios sin destino declarado (nodo gris "Destino desconocido")
    llave_des = des[["Año", "Folio"]].drop_duplicates().assign(_x=1)
    sin = car.merge(llave_des, on=["Año", "Folio"], how="left")
    sin = sin[sin["_x"].isna()][["Año", "Folio", "Rfc", "o"]]
    sin = monto_sin_destino(sin, ruta, anios).merge(gen[["Año", "Folio", "act"]], on=["Año", "Folio"], how="left")
    sin["act"] = sin["act"].fillna(SIN_DATO)
    sin = sin[sin["monto"] > 0]

    # ── diccionarios (índices enteros → JSON chico)
    def cat(*series, extra=()):
        vals = sorted(set(pd.concat(series).dropna().astype(str)) | set(extra))
        return vals, {v: i for i, v in enumerate(vals)}

    O, iO = cat(f["o"], sin["o"])
    D, iD = cat(f["d"])
    M, iM = cat(f["m"])
    A, iA = cat(f["act"], sin["act"])
    S, iS = cat(f["sec"])
    rfcs = sorted(set(f["Rfc"].dropna()) | set(sin["Rfc"].dropna()))
    iR = {r: i for i, r in enumerate(rfcs)}
    etiquetas = [nombres.get(r, r) for r in rfcs]
    # si dos RFC comparten nombre, desambigua con el RFC
    dup = pd.Series(etiquetas).duplicated(keep=False)
    R = [f"{e} ({r})" if d else e for e, r, d in zip(etiquetas, rfcs, dup)]

    f["io"] = f["o"].map(iO); f["id"] = f["d"].map(iD); f["im"] = f["m"].map(iM)
    f["ir"] = f["Rfc"].map(iR); f["ia"] = f["act"].map(iA); f["is"] = f["sec"].map(iS)
    f["cero"] = 0

    def tabla(col):
        g = (f.groupby(["io", "id", "im", col], sort=True)
               .agg(monto=("monto", "sum"), benef=("benef", "sum"), n=("monto", "size")).reset_index())
        return [list(x) for x in zip(g["io"].tolist(), g["id"].tolist(), g["im"].tolist(), g[col].tolist(),
                                     g["monto"].round(2).tolist(), g["benef"].round().astype(int).tolist(), g["n"].tolist())]

    det = {
        "O": O, "D": D, "M": M, "R": R, "A": A, "S": S,
        "mun": tabla("cero"),   # (emisor, receptor, municipio) → base de KPIs, municipios y emisores
        "rs": tabla("ir"),
        "act": tabla("ia"),
        "sec": tabla("is"),
    }
    su = (sin.assign(io=sin["o"].map(iO), ir=sin["Rfc"].map(iR), ia=sin["act"].map(iA))
             .groupby(["io", "ir", "ia"]).agg(monto=("monto", "sum")).reset_index())
    det["unk"] = [[a, b, c, round(m, 2)] for a, b, c, m in zip(su["io"], su["ir"], su["ia"], su["monto"])]

    # ── Donativos otorgados (donante → destinatario)
    otg = construir_otorgados(ruta, anios, car, gen, nombres, llave_des)
    if otg is not None:
        det.update(otg[0])
        print(f"Donativos otorgados: {len(otg[0]['ot']):,} filas · ${otg[1]:,.2f}")

    # ── links (siempre derivados de las mismas filas)
    l1 = f.groupby(["o", "d"], as_index=False)["monto"].sum()
    l1 = l1[l1["monto"] > 0].sort_values(["o", "d"])
    l2 = f.groupby(["d", "m"], as_index=False)["monto"].sum()
    l2 = l2[l2["monto"] > 0].sort_values(["d", "m"])
    desc = sin.groupby("o", as_index=False)["monto"].sum().sort_values("o")

    n_car = car[["Año", "Folio"]].drop_duplicates().shape[0]
    n_con = car.merge(llave_des, on=["Año", "Folio"])[["Año", "Folio"]].drop_duplicates().shape[0]

    raw = {
        "link1": [{"origen": a, "destino": b, "Monto": round(m, 2)} for a, b, m in zip(l1["o"], l1["d"], l1["monto"])],
        "link2": [{"destino": a, "municipio": b, "Monto": round(m, 2)} for a, b, m in zip(l2["d"], l2["m"], l2["monto"])],
        "desc_por_origen": [{"origen": a, "monto_desc": round(m, 2)} for a, m in zip(desc["o"], desc["monto"])],
        "stats": {"total_folios": int(n_car), "coinciden": int(n_con), "solo_caratula": int(n_car - n_con)},
        "det": det,
    }

    # ── verificación interna: todo cuadra con todo
    t1 = sum(r["Monto"] for r in raw["link1"]); t2 = sum(r["Monto"] for r in raw["link2"])
    tm = sum(r[4] for r in det["mun"]); tr = sum(r[4] for r in det["rs"])
    ta = sum(r[4] for r in det["act"]); ts = sum(r[4] for r in det["sec"])
    assert max(abs(t1 - t2), abs(t1 - tm), abs(t1 - tr), abs(t1 - ta), abs(t1 - ts)) < 5, \
        f"Los totales no cuadran: link1={t1} link2={t2} mun={tm} rs={tr} act={ta} sec={ts}"
    return raw, t1


def main():
    ap = argparse.ArgumentParser(description="Genera sankey.html con desglose por flujo.")
    ap.add_argument("--ruta", default=str(HERE / "data"),
                    help="Carpeta con los Excel (unidos por hoja o por año)")
    ap.add_argument("--anios", nargs="+", type=int, help="Años a incluir (default: el más reciente)")
    ap.add_argument("--salida", default=str(HERE / "sankey.html"))
    ap.add_argument("--plantilla", default=str(PLANTILLA))
    a = ap.parse_args()

    ruta = Path(a.ruta)
    anios = a.anios or anio_mas_reciente(ruta)
    print(f"Años: {anios}")
    raw, total = construir_raw(ruta, anios)

    s = raw["stats"]
    print(f"Folios en Carátula : {s['total_folios']:,}   con destino: {s['coinciden']:,}   sin destino: {s['solo_caratula']:,}")
    print(f"Monto conocido     : ${total:,.2f}")
    print(f"Monto sin destino  : ${sum(r['monto_desc'] for r in raw['desc_por_origen']):,.2f}")
    print(f"Links: {len(raw['link1'])} estado→estado, {len(raw['link2'])} estado→municipio · "
          f"filas de detalle: {sum(len(raw['det'][k]) for k in ('mun','rs','act','sec','unk')):,}")

    payload = json.dumps(raw, ensure_ascii=False, separators=(",", ":"), allow_nan=False).replace("</", "<\\/")
    html = Path(a.plantilla).read_text(encoding="utf-8")
    assert "/*__RAW__*/null" in html, "La plantilla no tiene el marcador /*__RAW__*/null"
    Path(a.salida).write_text(html.replace("/*__RAW__*/null", payload), encoding="utf-8")
    print(f"Listo → {a.salida} ({Path(a.salida).stat().st_size/1e6:.1f} MB)")


if __name__ == "__main__":
    main()