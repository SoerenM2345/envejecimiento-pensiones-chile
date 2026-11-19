"""Numeración de gráficos y tablas del dashboard: cada uno lleva el número de su KPI y un orden dentro del KPI (1.3.1, 1.3.2, ...).

Cada vista de un mismo selector cuenta como gráfico propio: por ejemplo «Nivel», «Tendencia» y «Brecha» de las regiones prioritarias
y «Caída más fuerte» tienen cada una su número, esté o no elegida en pantalla. Así un número identifica siempre lo mismo
y se puede citar («ver 1.1.9»).

Cómo funciona
  - ORDEN dice, por KPI, las claves en el orden en que aparecen en la página. Es la única lista que hay que mantener.
  - Una clave con «+» delante solo existe en la versión extendida; en la versión final se salta y la numeración queda sin huecos.
  - En el código, `mostrar(fig, num="1.1/mapa")` dibuja el gráfico con su número encima y `etiqueta("1.1/tabla_x")` hace lo mismo para una tabla.
  - Varias pestañas con el mismo gráfico (una por región) comparten el número y se distinguen con una letra: «1.1/composicion_region:b» → 1.1.6b.
"""
import streamlit as st

ORDEN = {
    "1.1": [
        "mapa", "barras_region", "barras_region_personas",                                    # cobertura por región
        "composicion", "composicion_tabla", "composicion_region", "tipo_trabajo",             # quién cotiza y por qué no cotiza el resto
        "prio_nivel", "prio_tendencia", "prio_brecha",                                        # regiones prioritarias: lista recomendada (tres factores)
        "prio_bp_brecha", "prio_bp_cotizantes", "prio_mayor_brecha", "prio_caida", "prio_peso",  # y las otras listas
        "largo_nivel", "largo_caida",                                                         # Chile, la prioritaria y la mejor desde 2002
        "paneles_2019", "paneles_2002",                                                       # región por región
        "tabla_rangos", "tabla_prioritarias",                                                 # tabla de las regiones prioritarias (según la lista elegida)
        "+corr_ingreso", "+corr_pobreza", "+corr_urbano",                                     # extendida: ¿por qué cotizan más en unas regiones?
        "matriz",
        "def_ejemplo", "def_confusiones",                                                     # definiciones de las tres piezas de la cobertura
        "desc_nivel", "desc_cambio_2023", "desc_cambio_2019",                                 # descomposición, una por comparación
        "razones_tabla", "factores", "factores_tabla",
        "+todos_factores_tabla", "+contraste_aafp_tabla", "+asignacion_tabla", "+pendularidad_tabla", "+sexo",
        "palancas_dispersion", "palancas_tabla", "acciones_tabla",
    ],
    "1.2": [
        "razon_region", "razon_region_personas", "razon_proyeccion",
        "rs_pais", "rs_regiones_criticas", "rs_regiones_todas",
        "pc_dinero", "pc_razon", "pc_cascada", "+pc_sensibilidad_tabla", "+pc_comunas_tabla",
        "esc_fijos", "esc_fijos_tabla", "reforma_esc", "reforma_tabla",
    ],
    "1.3": ["flujo_barras", "flujo_salario", "flujo_reforma", "destinos"],
    "2.1": [
        "total_obs", "total_esc",
        "def_ejemplo", "def_confusiones",
        "indice_obs", "indice_esc", "drivers", "razones_tabla",
        "costo_persona", "costo_pibpc",
        "+componentes", "+gasto_vs_poblacion", "+beneficiarios",
        "carga_mediana", "carga_promedio", "+proyeccion",
    ],
    "2.2": ["gasto_pib", "peso_fiscal", "fuentes", "calendario_fapp", "reservas", "sensibilidad_tabla", "+fapp_hoy", "dependencia"],
    "2.3": ["mapa", "barras", "barras_personas", "pobreza_cobertura"],
    "2.4": ["+afp_costos", "+afp_cascada", "+afp_venta_it", "+afp_por_administradora", "+afp_estres"],  # extendida: costos y economía de las administradoras
    "P": ["piramide", "alemania", "envejecimiento", "pico"],                                  # página del problema
}


def _claves(kpi: str, extendida: bool) -> list:
    return [c.lstrip("+") for c in ORDEN[kpi] if extendida or not c.startswith("+")]


def _es_extendida() -> bool:
    from utils import es_extendida
    return es_extendida()


def numero(clave: str, extendida: bool = None) -> str:
    """«1.1/mapa» -> «1.1.1»; con sufijo («1.1/composicion_region:b») -> «1.1.6b». Falla (ValueError) si la clave no está en ORDEN.
    Una clave exclusiva de la extendida solo se dibuja en páginas extendidas, así que se numera siempre con la lista extendida."""
    extendida = _es_extendida() if extendida is None else extendida
    ref, _, sufijo = clave.partition(":")
    kpi, _, nombre = ref.partition("/")
    extendida = extendida or ("+" + nombre) in ORDEN[kpi]
    return f"{kpi}.{_claves(kpi, extendida).index(nombre) + 1}{sufijo}"


def etiqueta(clave: str):
    """Dibuja el número sobre el gráfico o la tabla. Fondo claro y texto oscuro propios: se lee igual en tema claro y oscuro."""
    st.markdown(f"<div style='display:inline-block;background:#e7eef7;color:#0B2A40;font-weight:700;font-size:0.85rem;line-height:1;"
                f"padding:0.3rem 0.65rem;border-radius:999px;margin:0.3rem 0 0.2rem 0'>{numero(clave)}</div>", unsafe_allow_html=True)
