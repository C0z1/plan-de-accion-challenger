Plan (Opus, turno 7 iteración 3): vista Perfil en la app web local (http.server, stdlib).
El servidor calcula score.resumen(20) y score.tilt() (leen ~280 JSON de disco) en un hilo al arrancar y tras cada revisión de partida,
y lo deja en el estado que la página sondea cada 2 s. Un botón del nav alterna Companion/Perfil; fuera de champ select y partida se ve Perfil.
Tarjetas: score últimas 20, WR últimas 20, tendencia, componentes que más bajan, tilt hoy, cuenta y campeones.
