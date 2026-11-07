# Plan de acción v1 (2026-11-07)

Basado en 282 partidas de Solo/Duo (abril a octubre 2026, Riot API). Detalle: [`datos/analisis-2026-11-07.md`](datos/analisis-2026-11-07.md).

## Dónde estás y cuánto falta

| | LP |
|---|---|
| Tú | Master 15 |
| Corte Grandmaster LAN (hoy) | 1,154 |
| Corte Challenger LAN (hoy) | 1,732 |

En Master se ganan y pierden unos 18–20 LP por partida (estimado; depende de tu MMR). Partidas aproximadas para llegar a ~1,750 LP:

| Win rate | LP netos por partida | Partidas para llegar a Challenger |
|---|---|---|
| 54% (tu temporada) | ~1.5 | ~1,200 (no es viable) |
| 58% | ~3 | ~600 |
| 62% | ~4.5 | ~390 |
| 65% | ~5.5 | ~320 |

**La conclusión es clara:** con 54% no llegas. Lo que te va a llevar a Challenger es subir el win rate, no jugar más partidas. Si en lo que queda de temporada no alcanza, el plan sirve para arrancar la próxima con ventaja.

## Virtudes (con datos)
- **Escalas rápido.** Pasaste de Gold 3 (S2025) a Master 346 LP.
- **Yone:** 65 partidas, 58% WR y +411 de oro sobre tu rival de línea. Es tu campeón más sólido en mid.
- **Mordekaiser top:** 22 partidas con 68% WR. En top, en general, llevas 58% (60 partidas), mejor que tu 54% en mid.
- **Ekko** gana la línea: +410 de oro.
- **Kills en solitario:** 2.09 por partida. Mecánicamente le ganas a tu rival.
- **No hay patrón de tilt:** después de una derrota tienes 55% WR.

## Defectos (con datos)
1. **Mala racha actual:** 44% en las últimas 50 y 35% en las últimas 20, con −443 de oro contra tu rival. Últimamente estás perdiendo las líneas.
2. **Sylas es tu campeón más jugado y el que peor rinde:** 92 partidas, 52% WR, −511 de oro contra tu rival.
3. **Mueres mucho:** 6.5 muertes por partida, 7.4 en las derrotas.
4. **Poca presencia en el mapa:** 41% de KP y 0.83 de visión por minuto jugando mid. Ekko gana la línea (+410) pero solo tiene 52% WR, o sea, la ventaja no se convierte en victorias.
5. **Matchups que pierdes:** Viktor 1/8, Malzahar 2/7, Diana 2/7, Fizz 2/6, Qiyana 4/9.
6. **La 3.ª partida de cada sesión:** 43% WR, contra 57% en la 1.ª (muestra chica, 35 partidas).

## Prioridades (máximo 3)

### 1. Cerrar el champion pool
- **Mid:** Yone (principal) y Ekko (secundario).
- **Top / flexible:** Mordekaiser.
- **Sylas** solo cuando el matchup sea claramente bueno, no por costumbre.
- **Ban fijo:** Viktor.
- Métrica: más del 80% de tus partidas con esos 3 campeones.

### 2. Bajar a 5 muertes o menos por partida
- Antes de cada pelea o tradeo, pregúntate: ¿dónde está el jungla rival?, ¿tengo flash?, ¿cuánta vida tengo?
- Después de cada derrota, revisa en la repetición tus primeras 2 muertes: ¿fueron por estar sin visión, por pelear sin ventaja o por quedarte de más?
- Métrica: promedio semanal de muertes menor a 5.

### 3. Convertir las líneas ganadas en victorias
- Si vas ganando la línea con Ekko o Yone: empuja la oleada y luego rota o invade con tu jungla. No te quedes farmeando en mid.
- Métricas: KP de 50% o más y visión de 1.0 o más por minuto (compra control wards en cada regreso a base).

## Reglas de sesión
- Máximo 2 o 3 partidas por sesión. Tu WR baja en la 3.ª.
- No juegues ranked de 8 a 12 de la mañana (36% WR, muestra chica).
- Sí juega de 16:00 a 04:00, que es tu mejor horario.

## Metas semanales
- Semana 1: cortar la racha. 55% o más de WR, ≤ 5.5 muertes, pool cerrado.
- Después: 58% o más sostenido. Revisa los números cada domingo con `scripts/analizar.py`.
