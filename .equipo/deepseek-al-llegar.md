# Qué mirar al llegar

1. Tienes instalada la versión 0.14.4 de Racha, solo en tu PC (sin publicar). Ábrela y confirma la versión en Ajustes.
2. Para volver a la 0.14.1: baja el instalador del release v0.14.1 en la página Releases de GitHub del repo y ejecútalo encima.
3. Entra con cozi#1134 y mira Selección (rival real), Perfil, Partidas y Campeones con tus datos.
4. Abre una terminal en la carpeta del repo y deja corriendo `python scripts/salud.py --cada 60 --foto`.
5. Juega 1 partida normal con ese chequeo corriendo; no hace falta tocar nada, solo juega. Si reconectas, dragones y muertes 14–25 deben seguir contados.
6. FPS con la franja prendida: en la partida pulsa Ctrl+F, anota el número tras unos minutos de juego en la misma zona.
7. FPS con la franja apagada: apaga la franja en Ajustes, repite la medición en la misma fase de la partida y anota el número.
8. Diferencia de 1-2 FPS es ruido; si pierdes más de 5, avísale a Opus.
9. La franja se ve con LoL en «sin bordes»; en pantalla completa exclusiva no.
10. Mira que no haya franja en la carga y que salga pocos segundos después de empezar.
11. Que no tape el minimapa, el marcador de arriba a la derecha ni tu barra de habilidades.
12. Que el Dragón coincida con el reloj del juego (±2 s) cuando muera uno.
13. Al morir, la franja debe quedarse con tu regla y el siguiente objetivo.
14. Al terminar: fase correcta en Racha, sin cartel «Error» y un solo archivo nuevo en `datos/vivo`.
15. Manda a Opus lo que haya en `datos/salud/` (el log y las capturas de falla) junto con tus dos cifras de FPS.
16. Si todo va bien, dale permiso a Opus para publicar la 0.14.4.
