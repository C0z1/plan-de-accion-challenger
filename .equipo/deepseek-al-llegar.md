# Qué mirar al llegar

1. Tienes instalada la versión 0.14.2 de Racha, solo en tu PC (sin publicar). Ábrela y confirma la versión en Ajustes.
2. Para volver a la 0.14.1: baja el instalador del release v0.14.1 en la página Releases de GitHub del repo y ejecútalo encima.
3. Abre una terminal en la carpeta del repo y deja corriendo `python scripts/salud.py --cada 60 --foto`.
4. Juega 1 partida normal con ese chequeo corriendo; no hace falta tocar nada, solo juega.
5. FPS con la franja prendida: en la partida pulsa Ctrl+F, anota el número tras unos minutos de juego en la misma zona.
6. FPS con la franja apagada: apaga la franja en Ajustes, repite la medición en la misma fase de la partida y anota el número.
7. Diferencia de 1-2 FPS es ruido; si pierdes más de 5, avísale a Opus.
8. La franja se ve con LoL en «sin bordes»; en pantalla completa exclusiva no.
9. Mira que no haya franja en la carga y que salga pocos segundos después de empezar.
10. Que no tape el minimapa, el marcador de arriba a la derecha ni tu barra de habilidades.
11. Que el Dragón coincida con el reloj del juego (±2 s) cuando muera uno.
12. Al morir, la franja debe quedarse con tu regla y el siguiente objetivo.
13. Al terminar: fase correcta en Racha, sin cartel «Error» y un solo archivo nuevo en `datos/vivo`.
14. Manda a Opus lo que haya en `datos/salud/` (el log y las capturas de falla) junto con tus dos cifras de FPS.
