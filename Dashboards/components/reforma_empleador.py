"""Bloques de la reforma de la cotización del empleador (Ley 21.735) compartidos por las páginas final y extendida del KPI 1.3.

  - render_destinos_empleador(): «¿Adónde va la cotización del empleador?» (Scripts/15 -> kpi_reforma_empleador.csv): gráfico por escalón y la tabla
    «cuenta individual frente a Seguro Social». Todo lo que dice la tabla sale de la Nota Técnica de la ley (Data raw/_external/ley_21735/).
  - render_flujo_con_variantes(todo, ver_sis): KPI 1.3, la línea del flujo comisionable con un selector entre las variantes del salario y las de la reforma.
  - render_escenarios_reforma(pc_serie): KPI 1.2, la base y dos escenarios con el efecto de la reforma en el empleo formal (Scripts/15 y Scripts/30 ->
    kpi_reforma_empleo_factor.csv, kpi_pc_escenarios_reforma.csv). `pc_serie` es la función de la página que corre el motor del punto crítico.
"""
import pandas as pd
import streamlit as st
from utils import load_csv, es_cl, cargar_escenarios
from utils import subtitulo_visible as _subtitulo_visible
from components import critical_point as cp
from components.numeracion import etiqueta
from components.charts import _pct_exacto, mostrar, estilo_kpi, employer_destination_chart, fixed_scenarios_chart, commissionable_share_line, PANELES_REFORMA


def _pp(x: float) -> str:
    """0.045 -> '4,5', 0.0188 -> '1,88' (puntos porcentuales con coma decimal, hasta dos decimales)."""
    return es_cl(_pct_exacto(100 * x))


def render_destinos_empleador():
    st.divider()
    st.markdown("#### ¿Adónde va la cotización del empleador?")
    d = load_csv("kpi_reforma_empleador.csv")
    antes, hoy, fin = d[d.anio == 2024].iloc[0], d[d.anio == 2026].iloc[0], d[d.anio == 2033].iloc[0]
    largo = d[d.anio == 2054].iloc[0]
    mostrar(employer_destination_chart(d), num="1.3/destinos")
    _subtitulo_visible(
        f"Qué muestra: antes de la reforma el empleador solo pagaba el seguro de invalidez y sobrevivencia ({_pp(antes.total_empleador)} %). La ley lo sube cada agosto hasta "
        f"{_pp(fin.total_empleador)} % en 2033 (+{_pp(fin.aumento_vs_antes)} puntos). Hoy (agosto de 2026 a julio de 2027) es {_pp(hoy.total_empleador)} %, y solo {_pp(hoy.cuenta_individual)} "
        f"punto llega a la cuenta individual, la única parte que cobra comisión. En 2033 son {_pp(fin.cuenta_individual)} puntos a la cuenta individual y "
        f"{_pp(fin.seguro_social_sin_sis + fin.sis)} al Seguro Social; hacia 2054 la cuenta individual llega a {_pp(largo.cuenta_individual)} %.")
    tabla = pd.DataFrame({
        "Cuenta individual": [
            f"{_pp(fin.cuenta_individual)} puntos en 2033 ({_pp(largo.cuenta_individual)} desde 2054)",
            "Las administradoras de fondos de pensiones",
            "La pensión del propio afiliado: entra en las mismas condiciones que la cotización del trabajador",
            "Sí: es su saldo, con rentabilidad",
            "Sí: es la base de su comisión"],
        "Seguro Social permanente": [
            f"2,5 puntos (incluye el seguro de invalidez y sobrevivencia, {_pp(fin.sis)} puntos)",
            "Fondo Autónomo de Protección Previsional (FAPP): patrimonio independiente y administrador propio",
            "La compensación por las diferencias de expectativa de vida entre hombres y mujeres y parte del seguro de invalidez y sobrevivencia",
            "No: es un fondo común",
            "No"],
        "Seguro Social transitorio": [
            "1,5 puntos durante 30 años; después pasa a la cuenta individual, de forma gradual",
            "Fondo Autónomo de Protección Previsional (FAPP)",
            "El Beneficio por Años Cotizados: hasta 0,1 UF al mes por cada 12 meses cotizados (máximo 2,5 UF), para quienes se pensionan en los próximos 30 años",
            "No: se calcula por años cotizados, no por saldo",
            "No"],
    }, index=["Cuánto del empleador", "Quién lo administra", "Qué paga", "¿Tiene saldo propio?", "¿Cobra comisión la administradora?"])
    st.table(tabla.map(es_cl))
    st.caption(es_cl(
        "Fuente: Subsecretaría de Previsión Social, Nota Técnica «Reforma de Pensiones, Ley N°21.735» (agosto de 2025), Tabla 1 y secciones 1, 2.1 y 3, copia en "
        "Data raw/_external/ley_21735/; escalones leídos del PDF con Scripts/15 (kpi_reforma_empleador.csv). Los 1,88 puntos del seguro de invalidez y sobrevivencia son la tasa "
        "de la nota *; la nota no separa qué parte del 2,5 % es el seguro, así que se supone constante. La cuenta individual cobra comisión como las demás cotizaciones "
        "a cuentas individuales (supuesto del KPI 1.3). Los 1,5 puntos transitorios se entregan como cotización con rentabilidad protegida: se suman a la pensión del afiliado "
        "cuando se jubila, pero no forman un saldo propio en la cuenta individual."))


def render_escenarios_reforma(pc_serie):
    """KPI 1.2: ¿cambia el punto crítico si la cotización del empleador cuesta empleo formal? Dos escenarios frente a la base (tope de 10 %, cotizantes como hoy)."""
    st.divider()
    st.markdown("#### Con la reforma del empleador: dos escenarios frente a la base")
    cfg = cargar_escenarios()
    esc = load_csv("kpi_pc_escenarios_reforma.csv")
    fac = load_csv("kpi_reforma_empleo_factor.csv")
    series = {}
    for r in esc.itertuples():
        ruta = tuple((int(a), float(f)) for a, f in fac[fac.escenario == r.clave][["anio", "factor_vs_2025"]].to_numpy())  # vacío en la base
        series[r.clave] = pc_serie("pais", 0, 0, cp.Escenario(crec_salarial=cfg["crecimiento_salario_real"]["base"], pgu_250=cfg["pgu_250"],
                                                               carga_max=float(r.carga_max), cobertura_ruta=ruta))
    meses = {c: round(12 * (series[c][1]["anio_exacto"] - series["base"][1]["anio_exacto"])) for c in series}
    peor = min(meses.values())
    anio = {c: series[c][1]["anio"] for c in series}
    mostrar(estilo_kpi(fixed_scenarios_chart(
        esc, series, paneles=PANELES_REFORMA, titulo=f"Aunque la reforma costara empleo formal, el punto crítico se adelantaría {abs(peor)} meses como máximo",
        detalle="Costo y capacidad del Pilar Solidario de vejez, billones de pesos de 2025; el punto crítico es donde se cruzan (año bajo el eje)"), 420), num="1.2/reforma_esc")
    por = esc.set_index("clave")
    _subtitulo_visible(
        f"Qué muestra: la reforma sube el costo de contratar con contrato formal de {_pp(0.0188)} % a 8,5 % del sueldo, pero la capacidad de pago cambia poco. Si el empleador traspasa todo a los "
        f"sueldos, nada cambia (la base: {anio['base']}). Si por cada 1 % más de costo contrata {abs(por.loc['reforma_baja', 'elasticidad']):.1f} % menos, los cotizantes bajan "
        f"{abs(por.loc['reforma_baja', 'cotizantes_2033_vs_2025_pct']):.1f} % y el cruce llega {abs(meses['reforma_baja'])} meses antes; si contrata {abs(por.loc['reforma_alta', 'elasticidad']):.1f} % menos, "
        f"bajan {abs(por.loc['reforma_alta', 'cotizantes_2033_vs_2025_pct']):.1f} % y llega {abs(meses['reforma_alta'])} meses antes ({anio['reforma_alta']}). Lo que mueve el punto crítico es la demografía, no este canal.")
    filas = []
    for r in esc.itertuples():
        d, pc = series[r.clave]
        f50 = cp.fila_anio(d, 2050)
        filas.append({"Escenario": r.nombre, "Qué supone": r.descripcion,
                      "Punto crítico": str(pc["anio"]) if pc["estado"] == "cruza" else f"no antes de {int(d.anio.max())}",
                      "Frente a la base": "base" if r.clave == "base" else f"{meses[r.clave]:+d} meses".replace("-", "−"),
                      "Cotizantes en 2033 frente a 2025": f"{r.cotizantes_2033_vs_2025_pct:+.1f} %".replace("-", "−") if r.clave != "base" else "sin cambio",
                      "Carga requerida en 2050 (% del sueldo)": f"{100 * f50.carga_requerida:.1f} %",
                      "Cotizantes por persona de 65+ en 2050": f"{f50.razon_soporte:.2f}"})
    etiqueta("1.2/reforma_tabla")
    st.table(pd.DataFrame(filas).set_index("Escenario").map(es_cl))
    st.caption(es_cl(
        "Fuente: mismo motor del simulador (país, base cotizantes, ingreso promedio, sueldo real +1 % anual, PGU de $250.000, pesos reales de 2025) con la trayectoria de cotizantes de "
        "Scripts/15 (kpi_reforma_empleo_factor.csv). **La elasticidad es un supuesto**, no una estimación: no hay ninguna para esta reforma. El caso base (traspaso total a los sueldos, sin efecto en el "
        "empleo) sigue a Gruber (1997, NBER w5053), que encontró en Chile traspaso total a los sueldos y ningún efecto en el empleo cuando bajaron las cotizaciones; para una subida "
        "puede no valer. Solo reaccionan los cotizantes dependientes (99 % de los cotizantes): los independientes no pagan cotización del empleador. El costo laboral sube lo que sube la cotización "
        "frente a antes de la reforma, sin contar otras cargas del empleador. El efecto se mide desde 2025 (el escalón de agosto de 2025 ya está en los datos) y se mantiene desde 2033. "
        "**El Seguro Social no se suma a la capacidad:** sus ingresos pagan el Beneficio por Años Cotizados, la compensación a las mujeres y el seguro de invalidez y sobrevivencia, no el Pilar Solidario; "
        "el aporte del Estado a su fondo se ve en el KPI 2.2."))


def render_flujo_con_variantes(todo: pd.DataFrame, ver_sis: bool):
    """KPI 1.3: línea del % del flujo que pasa por cuentas individuales. Un selector cambia las dos variantes punteadas (salario real o efecto de la reforma en el
    empleo formal): el gráfico muestra como máximo 4 líneas. todo = kpi_flujo_comisionable.csv."""
    cfg = cargar_escenarios()
    el = dict(zip(("baja", "alta"), sorted(cfg["reforma_empleador"]["elasticidad_empleo_formal"]["variantes"], key=abs)))
    vista = st.radio("Variantes del escenario", ["Crecimiento del salario real", "Efecto de la reforma en el empleo formal"], horizontal=True, key="s13_variantes",
                     help="La reforma sube el costo de contratar con contrato formal; si el empleador contrata menos, bajan los cotizantes dependientes. La elasticidad es un supuesto, no una estimación.")
    reforma = vista.startswith("Efecto")
    mostrar(commissionable_share_line(todo, cfg["crecimiento_salario_real"]["base"], ver_sis, "reforma" if reforma else "salario", el),
            num="1.3/flujo_reforma" if reforma else "1.3/flujo_salario")
    if reforma:
        f = todo[(todo.variante == "sin_sis") & (todo.anio == 2033)].set_index("tipo")
        base = f.loc["escenario"]
        partes = []
        for k in ("baja", "alta"):
            v = f.loc[f"escenario_reforma_{k}"]
            partes.append(f"con el efecto {'bajo' if k == 'baja' else 'alto'} (elasticidad {el[k]:+.1f}), {100 * (v.cuentas_individuales / base.cuentas_individuales - 1):+.1f} % de flujo a cuentas individuales "
                          f"y {v.kpi_1_3_pct - base.kpi_1_3_pct:+.2f} puntos en el porcentaje".replace("-", "−"))
        st.caption(es_cl("En 2033, frente al escenario base: " + "; ".join(partes) + ". El porcentaje casi no se mueve porque la pérdida de cotizantes también reduce lo que va al Seguro Social: "
                         "lo que cambia es el monto, no la participación. La elasticidad es un supuesto (config/escenarios.yaml)."))
