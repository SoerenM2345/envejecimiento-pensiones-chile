# Selección de las regiones críticas: la regla de dos preguntas

Reemplaza a la regla de rangos de `docs/SHORTLIST_REGIONES.md` (nivel, tendencia y brecha; unión de los cinco peores de cada uno, con el nivel contado dos veces). **El documento anterior no se borra**: describe la regla con que se construyó el dashboard.
Se calcula con `Scripts/35_seleccion_dos_preguntas.py` → `Data processed/kpi_seleccion_dos_preguntas.csv` y `kpi_seleccion_sensibilidad.csv`.

## La regla

1. **Tendencia: ¿quién perdió puestos en el ranking de cobertura desde 2007?** Ranking de 15 territorios (Biobío y Ñuble unidos, como en `kpi_cobertura_tendencia.csv`), 1.º = mayor cobertura, diciembre de 2007 y de 2024. Entra quien perdió puestos **y** está bajo Chile en 2024. 2007 es el año de partida porque la serie salta entre 2006 y 2007 (documentado, sin explicación).
2. **Brecha: ¿dónde faltan más cotizantes?** Para las regiones bajo Chile (10 de 16): brecha = (cobertura de Chile − cobertura de la región) ÷ 100 × población de 15 a 64 años. Se ordena de mayor a menor y entran todas hasta que la participación acumulada llega al 80 %, incluida la que cruza el corte.
3. **Selección = unión de las dos respuestas.** Columna `motivo`: brecha, tendencia, ambas o ninguna.

El factor «nivel» se quita: es redundante, porque las regiones de menor nivel ya son las de mayor brecha.

## Resultado: 8 regiones

| Región | Motivo | Brecha 2024 (personas) | % acumulado |
|---|---|---:|---:|
| La Araucanía | brecha | 67.220 | 23 |
| Valparaíso | **ambas** | 53.659 | 41 |
| Biobío | brecha | 34.037 | 52 |
| Coquimbo | brecha | 33.342 | 64 |
| Ñuble | brecha | 29.346 | 74 |
| Los Ríos | brecha (cruza el 80 %) | 22.315 | 81 |
| Los Lagos | ninguna | 19.099 | 88 |
| Maule | ninguna | 18.034 | 94 |
| Arica y Parinacota | tendencia | 10.346 | 97 |
| Tarapacá | tendencia | 7.932 | 100 |

Las 8 elegidas suman **258.197 de 295.330** cotizantes que faltan (**87,4 %**) y son el **36,6 %** de la población de 15 a 64 años. Son las mismas 8 del dashboard: la lista actual no cambia.

**Tendencia.** Chile pasó de 37,1 % a 46,5 % (+9,4 puntos, +25,3 %). Bajo Chile pierden puestos solo Arica y Parinacota (10.º a 13.º), Tarapacá (7.º a 9.º) y Valparaíso (8.º a 10.º). Metropolitana, Atacama y Aysén también bajan de puesto, pero siguen sobre Chile y no entran.

**Valparaíso, la nota honesta.** Entra por las dos preguntas. Pero sube *más* que Chile en porcentaje (+26,5 % frente a +25,3 %) y *menos* en puntos (+8,8 frente a +9,4): pierde puestos porque otros subieron más, no porque su cobertura caiga. La nota va dentro de la figura N.5a.

## Sensibilidad (se informa; la regla no se ajusta a ella)

| Corte de la brecha | Regiones | % de la brecha | % de la población |
|---|---:|---:|---:|
| 70 % | 7 (sale Los Ríos) | 79,9 | 34,4 |
| **80 %** | **8** | **87,4** | **36,6** |
| 90 % | 10 (entran Maule y Los Lagos) | 100 | 47,4 |

Con año de partida 2007, 2008, …, 2018 el resultado es **idéntico** en cada corte (a partir de 2018 el ranking tiene 16 regiones separadas). La lista de 8 no depende del año de partida; sí del corte.

## Descomposición de las 8 regiones (diapositiva 14)

Cobertura = participación × empleo × cotización de los ocupados. Los aportes en puntos usan la media logarítmica y suman exacto la diferencia con Chile. Ponderando por población, de los ≈ 258 mil cotizantes que faltan: **70 %** ocupados que no cotizan (≈ 180 mil), **28 %** participación (≈ 72 mil), **2 %** empleo (≈ 6 mil). En 7 de 8 regiones la etapa 3 (cotización) es la mayor; en Biobío lidera la participación. El «69 / 28 / 3 %» anterior venía de una corrida con 7 regiones.

## Figuras

N.5a (tabla de puestos), N.5b y N.5b-v2 (cobertura de Chile), N.5c (brecha por motivo) y N.5d (descomposición) en `Outputs/figuras_pptx/` (diapositivas 13 y 14). La N.5 anterior (tres paneles) queda con estado `superseded`.

## Pendiente

- El nombre `kpi_cobertura_siete_vs_chile.csv` dice «siete» pero contiene las 8 regiones; no se renombró.
- ¿Llevar al dashboard la tabla de puestos y las barras de brecha coloreadas (junto a 1.1.8-1.1.10)? Requiere claves nuevas en `components/numeracion.py`; no se hizo sin confirmación.
