# Análisis con timeline: 282 partidas, 1837 muertes

Intervalos: Wilson 95%. Con menos de ~20 partidas el intervalo es muy ancho: tómalo como pista, no como regla.

## Diferencia contra el rival de línea

| | Oro @10 | Oro @14 | Oro @20 | XP @14 | CS @14 |
|---|---|---|---|---|---|
| Total | -100 | -152 | -75 | -38 | -3.1 |
| Victorias | +9 | +104 | +364 | +216 | +1.2 |
| Derrotas | -229 | -452 | -593 | -335 | -8.2 |
| Últimas 50 | +37 | -51 | +32 | -149 | -2.4 |

## WR según oro contra el rival a los 14 min

| Oro @14 | Partidas | WR (IC 95%) |
|---|---|---|
| ≤ −1000 | 73 | 41% (31%–53%) |
| −1000 a 0 | 79 | 52% (41%–63%) |
| 0 a +1000 | 81 | 57% (46%–67%) |
| ≥ +1000 | 47 | 72% (58%–83%) |

## WR según muertes antes del min 14

| Muertes <14 | Partidas | WR (IC 95%) |
|---|---|---|
| 0 | 25 | 76% (57%–89%) |
| 1 | 70 | 49% (37%–60%) |
| 2 | 75 | 55% (43%–65%) |
| 3 | 65 | 55% (43%–67%) |
| 4+ | 47 | 49% (35%–63%) |

Promedio de muertes antes del 14: 2.12 en victorias, 2.29 en derrotas.

Fuiste la víctima del first blood en 32/282 partidas (11%); WR en esas: 41% (26%–58%).

## Muertes por fase

| Fase | Muertes | Por partida | En victorias | En derrotas |
|---|---|---|---|---|
| 0–14 min | 621 | 2.20 | 2.12 | 2.29 |
| 14–25 min | 746 | 2.65 | 2.29 | 3.06 |
| 25+ min | 470 | 1.67 | 1.34 | 2.05 |

## Muertes por zona del mapa

| Zona | Muertes | % | Antes del 14 | Con el jungla rival |
|---|---|---|---|---|
| mid (lado propio) | 342 | 19% | 182 | 52% |
| río | 330 | 18% | 94 | 65% |
| mid (lado rival) | 240 | 13% | 94 | 56% |
| jungla (lado rival) | 190 | 10% | 36 | 57% |
| top (lado rival) | 150 | 8% | 64 | 43% |
| bot (lado rival) | 147 | 8% | 33 | 52% |
| jungla (lado propio) | 126 | 7% | 24 | 62% |
| top (lado propio) | 120 | 7% | 62 | 46% |
| bot (lado propio) | 106 | 6% | 32 | 43% |
| base propia | 56 | 3% | 0 | 59% |
| base rival | 30 | 2% | 0 | 53% |

## ¿Quién te mata? (enemigos involucrados)

| Enemigos | Muertes | % | Antes del 14 |
|---|---|---|---|
| 1 | 399 | 22% | 221 |
| 2 | 646 | 35% | 282 |
| 3+ | 790 | 43% | 117 |

Muertes antes del 14 con el jungla rival involucrado: 321/621 (52%).
Jugando mid, muertes antes del 14 fuera de la línea de mid: 139/414 ([('río', 62), ('jungla (lado rival)', 32), ('jungla (lado propio)', 15)]).

## Por campeón (8+ partidas)

| Campeón | Partidas | WR (IC 95%) | Oro @14 | Oro @14 en V | Oro @14 en D | Muertes <14 | Muertes totales |
|---|---|---|---|---|---|---|---|
| Sylas | 92 | 52% (42%–62%) | -264 | +64 | -615 | 2.07 | 6.7 |
| Ekko | 71 | 52% (41%–63%) | +177 | +623 | -309 | 1.94 | 6.0 |
| Yone | 65 | 58% (46%–70%) | -234 | -151 | -351 | 2.37 | 6.2 |
| Mordekaiser | 22 | 68% (47%–84%) | -428 | -224 | -836 | 1.95 | 5.5 |
| Pyke | 11 | 73% (43%–90%) | -110 | -97 | -145 | 3.91 | 10.2 |

## Challenges: lo que más separa victorias de derrotas

Efecto = (media en V − media en D) / desviación. Excluye métricas que son consecuencia directa de ganar (torres, oro total, etc. aparecen igual: léelas con criterio).

| Métrica | Efecto | Victorias | Derrotas | Temporada | Últimas 50 |
|---|---|---|---|---|---|
| turretTakedowns | +1.10 | 3.42 | 1.30 | 2.45 | 1.88 |
| maxKillDeficit | +1.05 | 3.92 | 0.00 | 2.13 | 1.50 |
| teamBaronKills | +1.04 | 1.03 | 0.26 | 0.68 | 0.70 |
| turretPlatesTaken | +0.86 | 11.72 | 6.83 | 9.48 | 7.96 |
| baronTakedowns | +0.80 | 0.66 | 0.16 | 0.43 | 0.52 |
| kda | +0.79 | 3.67 | 1.52 | 2.69 | 2.68 |
| maxLevelLeadLaneOpponent | +0.75 | 1.96 | 1.29 | 1.65 | 1.58 |
| goldPerMinute | +0.71 | 436.58 | 388.79 | 414.72 | 407.52 |
| takedowns | +0.70 | 15.50 | 10.80 | 13.35 | 12.24 |
| firstTurretKilled | +0.65 | 0.72 | 0.40 | 0.57 | 0.66 |
| flawlessAces | +0.63 | 0.33 | 0.03 | 0.20 | 0.06 |
| dragonTakedowns | +0.62 | 0.87 | 0.37 | 0.64 | 0.64 |
| killsNearEnemyTurret | +0.61 | 2.05 | 1.02 | 1.58 | 1.34 |
| voidMonsterKill | +0.59 | 0.82 | 0.33 | 0.60 | 0.72 |
| deathsByEnemyChamps | -0.58 | 5.75 | 7.41 | 6.51 | 5.64 |
| lostAnInhibitor | +0.57 | 0.16 | 0.00 | 0.09 | 0.04 |
| perfectDragonSoulsTaken | +0.57 | 0.20 | 0.02 | 0.11 | 0.12 |
| bountyGold | -0.54 | 106.31 | 276.90 | 184.35 | 156.19 |
| damagePerMinute | +0.53 | 899.32 | 731.52 | 822.56 | 752.70 |
| enemyJungleMonsterKills | +0.51 | 3.48 | 1.35 | 2.50 | 2.96 |

### Métricas de early game y hábitos

| Métrica | Efecto | Victorias | Derrotas | Temporada | Últimas 50 |
|---|---|---|---|---|---|
| controlWardsPlaced | +0.13 | 0.21 | 0.10 | 0.16 | 0.40 |
| earlyLaningPhaseGoldExpAdvantage | +0.07 | 0.08 | 0.06 | 0.07 | 0.12 |
| enemyJungleMonsterKills | +0.51 | 3.48 | 1.35 | 2.50 | 2.96 |
| killParticipation | +0.03 | 0.41 | 0.41 | 0.41 | 0.41 |
| killsUnderOwnTurret | -0.31 | 0.46 | 0.77 | 0.60 | 0.46 |
| laneMinionsFirst10Minutes | +0.10 | 67.34 | 65.58 | 66.54 | 66.96 |
| laningPhaseGoldExpAdvantage | +0.20 | 0.10 | 0.05 | 0.07 | 0.04 |
| maxCsAdvantageOnLaneOpponent | +0.26 | 32.19 | 24.41 | 28.63 | 28.02 |
| maxLevelLeadLaneOpponent | +0.75 | 1.96 | 1.29 | 1.65 | 1.58 |
| outnumberedKills | +0.38 | 1.93 | 1.29 | 1.64 | 1.34 |
| skillshotsDodged | -0.02 | 39.94 | 40.84 | 40.35 | 27.38 |
| soloKills | +0.47 | 2.54 | 1.56 | 2.09 | 1.72 |
| survivedSingleDigitHpCount | +0.06 | 0.08 | 0.06 | 0.07 | 0.08 |
| takedownsFirstXMinutes | +0.37 | 4.29 | 3.29 | 3.84 | 3.70 |
| turretPlatesTaken | +0.86 | 11.72 | 6.83 | 9.48 | 7.96 |
| visionScorePerMinute | +0.13 | 1.01 | 0.93 | 0.97 | 0.99 |
| wardTakedownsBefore20M | +0.05 | 0.92 | 0.84 | 0.89 | 1.06 |
