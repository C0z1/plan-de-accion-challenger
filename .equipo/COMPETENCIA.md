# Racha frente a la competencia (Fable, 2026-11-12)

Fuentes de competidores: casi todas escritas por rivales (iTero, Hexgate) o fichas de Overwolf. Sin datos de Reddit ni de jugadores Master+; sin precios de iTero, Porofessor y U.GG.

## 1. Competidores
| App | Qué hace bien | Gratis / pago | Quejas |
|---|---|---|---|
| iTero | Draft con IA, «Macro Coach» (3 cosas a mejorar), 500+ stats por elo y pool, scouting, 2.º monitor | Gratis con anuncio chico; suscripción (precio sin dato). Versión sin Overwolf | ~650 MB RAM; abruma |
| Porofessor | Scouting con etiquetas por jugador; 16 M instalaciones | Gratis con anuncios; pago sin anuncios | Overwolf, ~1.000 MB, errores recientes; el anonimato le quita valor |
| Mobalytics | GPI, post-partida de los 10, retos, LP, power spikes | Anuncios grandes; Plus $7.99–9.99/mes | Overwolf, ~1.400–2.000 MB, se congela, lo bueno es de pago |
| Blitz | Importa runas/builds, benchmarks, timers, ruta de jungla; Electron | Anuncios; Premium desde $3.99/mes | Peores anuncios, RAM alta, caídas de FPS; Trustpilot 2.3/5 |
| U.GG | Builds y tier lists por rol y elo, overlay | Sin dato | Overlay cuesta FPS |
| OP.GG Desktop | Overlay de CS y oro, tier lists | Anuncios; Premium | Sin dato |
| Hexgate | Nativa (Tauri, < 100 MB), sin anuncios; oro por línea, scouting en carga, clips de muertes | 3 partidas/día gratis; €9.99–14.99/mes | Sin timers, LP ni perfiles |
| IA (YOUR.GG, Mobalytics AI Coach, Overwolf AI Suite) | Reportes y VOD | Mixto | Solo marketing |

Fuentes: itero.gg/articles/what-is-the-best-league-of-legends-companion-app-in-2025 · hexgate.pages.dev/blog/hexgate-vs-blitz-vs-mobalytics/ · overwolf.com/app/iTero_Gaming-iTero_Drafting_Coach · opgg.helpscoutdocs.com/article/398-op-gg-premium-guide-desktop-app · exitlag.com/blog/best-league-of-legends-reviews-stats-sites/ · wombocombo.gg/blog/game-analytics/blitz-gg-overlay-review

## 2. Lo que tienen y Racha no (útil para Master→Challenger)
Benchmark contra mids Challenger/GM con tus campeones · LP por partida y sesión, distancia al corte de Challenger LAN · scouting en pantalla de carga (nunca en champ select) · diferencia de oro por línea con ítems visibles · draft según composición · builds de OTP por matchup · clips de tus muertes.
No vale: importar runas (rompe «solo lee»), orden de habilidades, tier lists, ruta de jungla, retos, chat con LLM.

## 3. Comodidades de escritorio
| Comodidad | Racha | Cómo |
|---|---|---|
| Inicio con Windows | Sí (`autoarranque()`) | — |
| Segundo plano al cerrar | Sí con `--fondo` | — |
| Ícono en la bandeja | No: hoy no hay forma visible de salir ni reabrir | ctypes `Shell_NotifyIconW` en un hilo con bucle de mensajes; menú Abrir / Franja / Salir (~80 líneas) |
| Instancia única | Sí (`otro_htc()`) | Verificar que reabrir no duplique la ventana de Edge |
| Auto-actualización | Sí (sha256, fuera de partida) | Falta firma digital |
| Notificaciones | No | Globo del ícono (`NIF_INFO`), nunca en partida |
| Sonido | No | `winsound` asíncrono, apagado por defecto |
| Atajos globales | No (F7 en espera por Vanguard) | Menú de bandeja primero |
| Consumo | CPU 0,3–0,8 % | Medir RAM de Edge antes de presumir |
| Modo compacto | No (1440×1024 fijo) | CSS < 600 px + botón con `SetWindowPos` |
| Multi-monitor | Parcial | Guardar rectángulo en ajustes; `--window-position` |

## 4. Límites de Riot
developer.riotgames.com/docs/lol: nada «previously unknown to the player»; no «dictate player decisions» (sí resaltar); no analizar jugadores ocultos; no calculadoras de MMR/ELO; aprobado: stats propias, datos estáticos previos, leaderboards oficiales. LCU sin soporte oficial.
support.riotgames.com/en-us/riot/events/third-party-applications: no exponer info ofuscada, no actuar por ti, no sacar conclusiones en partida.
Recientes: timers de ultis enemigas prohibidos (13-mar-2025); anuncios en overlays prohibidos (29-may-2025); timers de hechizos y campamentos «en revisión» (prensa); lectura de memoria bloqueada desde 6-oct-2026 (Racha nunca la usó).
Choques: nada de timers enemigos; scouting solo en carga; avisos como dato + tu regla, no en imperativo (también la franja de muertes sin objetivo); no presentar score como MMR; timer de dragón/barón es zona gris ya anotada.

## 5. Dónde gana Racha
Sin Overwolf, sin anuncios, ligera · coaching con tu historial y tus reglas · limpia por diseño (sin memoria ni inyección) · local y gratis · una sola meta (Master→Challenger, mid).

## 6. Top 8
| # | Qué | Tam. | Quién |
|---|---|---|---|
| 1 | Prueba real 5 con cozi#1134 (+FPS y RAM) | S | Usuario; Opus lee `datos/salud` |
| 2 | `unir_eventos` sin `EventTime` exacto | S–M | Opus; DeepSeek pruebas |
| 3 | Mismo `.jsonl` al reabrir a media partida | S | Opus; DeepSeek |
| 4 | Franja «muertes sin objetivo 14–25» (redactada como dato) | M | Opus; DeepSeek anchos; usuario |
| 5 | Ícono de bandeja con menú y globos (+ limpieza `salir`, capturas en serie) | M | Opus; DeepSeek; usuario |
| 6 | LP por partida/sesión y distancia al corte Challenger LAN | S–M | Opus; DeepSeek |
| 7 | Benchmark contra mids Challenger/GM con tus campeones | M | Opus; DeepSeek estadística |
| 8 | Scouting en pantalla de carga (rival de línea y jungla) | M–L | Opus; DeepSeek política; usuario |

Decisión del usuario: importar runas (lo más usado de la competencia) escribe en el cliente; Fable recomienda no hacerlo.
No revisado: `replay.py`, `aviso_pico`, RAM real de Racha.
