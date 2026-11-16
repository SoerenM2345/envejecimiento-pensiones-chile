# Auditoría de datos contra las fuentes originales (2026-11-16)

Revisión hecha como agente externo: sin usar los scripts ni la lógica del proyecto, se recalcularon valores desde `Data raw/` y se compararon con los puntos que **realmente dibuja** cada gráfico (se ejecutaron las páginas final y extendida con `streamlit.testing.AppTest` y se leyeron los datos de cada figura de Plotly). Se hizo en las dos direcciones: de la fuente al gráfico (recalcular y buscar el punto) y del gráfico a la fuente (tomar el punto y rastrearlo hasta el archivo original). Versión revisada: `d2f25a0` (`main` = `origin/main`).

**Resultado: no hay datos mal ingresados.** Más de 1.300 valores comparados; las únicas diferencias son decisiones de método (tabla de abajo), ninguna cambia una conclusión. Cuando un valor no calzaba al primer intento se siguió buscando hasta explicarlo (unidad, fecha, ponderador o definición); todas las diferencias iniciales eran de ese tipo.

## Qué se comparó, por fuente

| Fuente | Valores comparados | Resultado |
|---|---|---|
| INE, Censo 2024 (microdatos) | 172 (pirámide: 86 edades × 2 sexos), 64 (16 regiones: 15-64, 65+, % 65+, cotizantes) y las tarjetas 14,0 % / 17,7 % / 68,3 % | Exacto |
| INE, proyecciones 1992-2070 (base 2024) | 159 (% 65+ 1992-2070 y población 15-64) + 5 puntos del escenario de razón de soporte (2030-2070) | Exacto; usa la población al 30 de junio |
| Destatis | 200 (pirámide de Alemania) + 22,7 % de 65+ | Diferencia máxima 0,0002 puntos (el denominador es la suma de las edades 0-99) |
| Superintendencia de Pensiones, cotizantes por región | 16 regiones × (cobertura, razón de soporte, burbuja) + 16 × 6 años + país 2002-2024 | Exacto |
| INE, proyecciones base 2017 por comuna | Serie de cobertura 16 regiones × 6 años (2019-2024) y 2002-2024 para dos regiones | Exacto con el factor Censo/INE 2024 |
| Superintendencia, cuadro 04A (+ IPC del Banco Central) | 16 años de masa imponible (capacidad de pago 2010-2025) | Exacto |
| Superintendencia, cuadro 32C | 248 ingresos por región × año (2010-2025) | Exacto |
| Superintendencia, Fichas Previsionales 136-159 | 22 meses × (cotizantes, ingreso) contra el 04A | 43 de 44 iguales; ficha 157 trae 110 cotizantes más que el 04A de octubre 2025 (revisión de la propia Superintendencia) |
| Subsecretaría de Previsión Social, Pilar Solidario | 16 años de costo de vejez (2010-2025), 10 de la barra apilada, 4 de la PGU por persona, 16 regiones «sin pensión propia» | Exacto (suma mensual nominal deflactada con el IPC) |
| DIPRES, gasto «Edad avanzada» | 10 (pesos 2025) + 10 (% PIB) + 10 (residual) | Exacto |
| Banco Central, PIB | 13 (Pilar en % PIB) + 10 (costo por persona en % del PIB por habitante) | Exacto (la razón se calcula con precios corrientes de cada año) |
| INE, ESI y ENE nacional | 10 (10 % del ingreso mediano) + 10 (pago por ocupado) | Exacto |
| INE, ENE regional | 16 brechas de informalidad por sexo; correlaciones de informalidad (−0,83) y desocupación (−0,32); 21 aportes de la descomposición | Exacto con el trimestre nov-ene 2023-24 |
| Asociación de AFP (PDF) | 96 valores transcritos a mano; cobertura de ocupados 2019 y 2024 | 0 diferencias; la cobertura publicada calza con la de la Superintendencia (≤ 0,05 puntos) |
| CASEN 2022 | 16 tasas de pobreza 65+ y 16 conteos; correlación −0,68; ingreso per cápita de 16 regiones | Pobreza exacta; el ingreso exige el factor comunal (ver observaciones) |
| Fondo de Reserva de Pensiones (PDF) y SII | 4 retiros anuales, saldo de cierre y dólar implícito 2022-2025; UTM 2025 (promedio 68.640) | Exacto: el dólar implícito (873,2 / 839,8 / 943,7 / 951,3) es el promedio de los meses del SII; el saldo usa 911,18 del 30-dic-2025 |
| FAPP, estados financieros (PDF) | 11 cifras de ambos estados y 3 barras de la caja del semestre | Exacto |
| Ley 21.735, Nota Técnica | 10 aportes anuales de la Tabla 2 (2028-2037) | Exacto (millones de UTM × 68.640) |
| Superintendencia, costos de administración (PDF) | 10 razones gasto/comisiones, 16 razones por administradora (2022 y 2025), ganancia 2025, encaje 19,0 % | Exacto |
| Superintendencia, pensiones pagadas jul-2026 | Pensionados (466.781) y monto anual (2,03 billones) | Exacto |

No se auditaron las curvas de escenario más allá de sus puntos de partida y de la razón de soporte 2030-2070 (son salidas de un modelo, no datos). El PIB regional del Banco Central no se dibuja en ningún gráfico de la versión final ni de la extendida.

## Observaciones (decisiones de método, no errores de datos)

1. **Cobertura del país 2002-2009.** La serie es la suma de las regiones con la población base 2017; desde 2010 es la del KPI 1.2 (base 2024). La unión deja el tramo 2002-2009 hasta 0,19 puntos sobre la serie coherente (30,00 % frente a 29,84 % en 2002). Está en el docstring del script 24, no en el dashboard: ya se agregó a las limitaciones de la página.
2. **Ingreso per cápita regional (CASEN).** El gráfico pondera con el factor comunal (`expc`) de un extracto de terceros. Los ingresos del extracto son idénticos, persona a persona, a la base oficial, pero la nota de uso de la CASEN pide el factor regional (`expr`): con él, el ingreso regional sube entre 1 % y 4,7 % y la correlación con la cobertura pasa de 0,770 a 0,779. No cambia el mensaje.
3. **Informalidad nov-ene 2023-24.** La ENE llega a mar-may 2024; con ese trimestre la correlación sería −0,85 en vez de −0,83. Es la elección «diciembre» de la descomposición y está anotada.
4. **Dólar y UTM sin copia local.** Los valores del SII calzan hoy, pero la página puede cambiar: conviene guardar las tablas en `Data raw/_external/sii/` (ya señalado en `Data raw/INVENTARIO_FUENTES.md`, punto 12).
5. **Dos grafías de Biobío** en los informes del Pilar Solidario («Bío-Bío» y «Bíobío»): el procesamiento los une bien (30,26 % calza).

## Cómo repetirla

Las páginas se ejecutaron con `AppTest.from_file(...)`, se leyó `el.proto.spec` de cada `plotly_chart` y se decodificó el formato binario de Plotly (`bdata`). Cada fuente se recalculó con DuckDB (Censo), pandas (Excel, CSV, HTML de la Superintendencia, XML de la ENE) y un lector de PDF aparte para el Fondo de Reserva, el FAPP, las fichas, la Asociación de AFP y los costos de administración.
