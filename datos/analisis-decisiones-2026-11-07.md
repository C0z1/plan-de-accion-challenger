# Revisión de decisiones: derrotas con la línea ganada (2026-11-07)

Fuente: `scripts/partida.py --ultimas 8` (replay en datos, minuto 12–26) → [`analisis-partidas-2026-11-07.md`](analisis-partidas-2026-11-07.md), y controles sobre todas las partidas. No hay replays `.rofl` en el disco; todo sale del timeline (posiciones por minuto, eventos exactos).

## Las 8 derrotas más recientes con oro ≥ 0 al 14

| Partida | Campeón | Rival | Oro @14 | Lo que pasó del 14 al 25 |
|---|---|---|---|---|
| LA1_1759103806 | Yone mid | Viktor | +620 | 4 muertes del 13 al 19, 3 en el río contra 3–4 rivales; 2 justo antes de un dragón (13:27 → dragón 13:36; 18:07 → dragón 19:01). El equipo pasa de +2444 a −3490. |
| LA1_1759092560 | Zeri bot | Lucian | +2134 | Fuera del pool y del rol. Peleas de equipo perdidas; muerte en el río 30 s antes del barón rival. |
| LA1_1759076415 | Sylas mid | Annie | +2062 | Muere solo a la jungla rival (14:04 río, 19:36 jungla propia, 0 aliados cerca). A los 18 s del 19:36 el equipo pelea 4 contra 5, caen 3 y se pierden 2 torres de mid. |
| LA1_1758483175 | Locke mid | Sylas | +257 | Fuera del pool. 3 muertes en la jungla rival con el equipo +2000 a +3800. |
| LA1_1757603689 | Sylas mid | Yasuo | +278 | 16:13 muere en su jungla contra Yasuo + Evelynn (0 aliados); 17:18 otra vez en mid → torre de mid y heraldo perdidos; de +931 a −1719. 23:45 muere solo en la jungla rival contra 5 → 2 torres de mid. |
| LA1_1757404563 | Rakan support | Swain | +311 | Fuera del pool y del rol. |
| LA1_1756914787 | Zeri bot | Hwei | +598 | Fuera del pool. 3 muertes sin aliados cerca; el equipo va +5435 al 26 y pierde después. |
| LA1_1756077760 | Sylas top | Mordekaiser | +716 | 1 muerte del 14 al 25; equipo +8939 al 26. Se pierde después del 26. |

**Lectura:** 4 de 8 son fuera del pool y 3 con Sylas; solo 1 con Yone o Ekko. **Pero no basta para culpar al pool** (revisión de DeepSeek: son derrotas seleccionadas). Contra las victorias, en las últimas 50: pool (Yone/Ekko/Morde) 12/25 = 48% (30–67%), Sylas 7/15 = 47%, otros 3/10 = 30%. En la temporada: pool 57%, Sylas 52%, otros 47%. Fuera del pool rindes peor, pero en la racha **el pool también cayó**: hay algo más que el pick.

## Controles sobre todas las partidas (20+ min)

- **Morir sin aliados a < 2500** (posición interpolada entre frames) **no separa V/D** una vez que cuentas cuántas veces mueres: con 1 muerte del 14 al 25, 80% contra 68%; con 2, 56% contra 60%; con 3, 43% contra 42%. Lo que pesa es **cuántas veces mueres**, no si estabas solo (coincide con "pick-off no separa" de `midgame.py`).
- **Ventaja grande que se pierde:** con el equipo ≥ +3000 de oro al 25 ganas 67/80 = 84% (74–90%). En las 13 derrotas el rival toma 0.92 barones del 25 en adelante (0.13 en las victorias) y mueres 3.26 veces por 10 min (1.97 en las victorias).
- En esas 13, de 27 dragones y barones rivales del 25 en adelante, **24 llegan después de una pelea perdida** (aliado muerto en los 60 s previos); tú moriste antes de 9. El throw es de pelea de equipo antes del objetivo, no solo tuyo.

## Qué cambia en las reglas

1. Nada nuevo para el 14–25: la regla sigue siendo "≤ 2 muertes y no pelear antes de un objetivo".
2. **Regla nueva para el late (pista):** con ventaja grande pasado el 25, **no pelees antes de barón o dragón si no lo tienes asegurado**; agrupa y que el rival venga a ti. Un throw empieza en una pelea perdida 1 minuto antes del objetivo (24 de 27 veces).
   Precisión de DeepSeek: antes del objetivo pon visión y empuja oleadas; no pelees 4 contra 5 ni sin flash/ulti; pelea solo con ventaja numérica o posicional, o si el objetivo decide la partida (barón, alma, anciano). Esperar no vale si con eso regalas el objetivo gratis.
3. Fuera del pool rindes menos (47% contra 57%), pero la racha no es solo de pick: el pool también va 48% en las últimas 50.

## Límites (revisión de DeepSeek)
- La posición de los aliados es interpolada entre fotos por minuto: "aliados a < 2500" es aproximado.
- n = 13 throws; las muertes del 25 en adelante en derrotas también son consecuencia de ir perdiendo.
- El timeline no ve visión real, cooldowns (flash, ulti), estado de oleadas ni llamadas del equipo. **Para eso hace falta el video:** empezar por la muerte de Yone a las 18:07 antes del dragón en LA1_1759103806 (wards, flash/ulti, oleadas, quién inició).
