# Cómo usar Racha

Racha es una app de escritorio para Windows que, con tus propias partidas de League of Legends, te dice qué te hace perder y qué cuidar en cada partida. Es gratis, de código abierto y solo lee datos del cliente: no pickea, no banea y no actúa por ti.

## Instalar

1. Baja `Racha-Setup-0.10.0.exe` de la [última release](https://github.com/C0z1/racha.gg/releases/latest) y ejecútalo. Se instala solo para tu usuario, sin administrador, y se actualiza encima de la versión anterior.
2. Si Windows dice «Windows protegió su PC», dale a **Más información → Ejecutar de todas formas** (el instalador todavía no tiene firma digital).
3. Abre League of Legends. Racha se abre sola y detecta la fase en la que estás.

## Entrar: con Google o con código

Para ver tu historial necesitas una de estas dos cosas (las dos se configuran en **Ajustes → Cuenta**):

- **Continuar con Google**: guarda tu cuenta en la nube (tu Riot ID, tus ajustes y el resumen de tus partidas) y, si te invitaron, te da acceso.
- **Código de acceso**: te lo da quien administra Racha. Sirve para bajar tus partidas por el servidor de Racha, sin key de desarrollador.

Con cualquiera de las dos, la primera vez Racha baja tu historial sola (puede tardar unos minutos). Después puedes usar **Descargar** o **Recargar** en Ajustes.

## Qué ves en cada pantalla

- **Inicio**: el estado del cliente, tu racha del día, **tu pick de hoy**, **tu racha de oro al 14** y **tu regla de hoy** (la que más te cuesta). A la derecha, tu cuenta, tu rango y tu win rate contra la meta.
- **Draft**: antes de que se vea el rival, a quién banear y tu pool del rol.
- **Selección**: cuando ya se ve tu rival de línea, tu récord contra él, tu win rate, tu plan con el campeón (3 reglas) y la build, con **«Tú contra ellos»**: en qué difiere tu build de la de los onetricks del top.
- **En vivo**: durante la partida, tu nivel y CS contra tu rival, tus muertes desde el 14, los objetivos y los timers de dragón y barón. Al terminar, la línea final y la **revisión post-partida con 3 momentos clave**.
- **Perfil**: tu score, tu win rate, tus errores, qué cambiar y **tu semana** (récord contra la anterior, oro al 14, 2 derrotas seguidas, mejor campeón, peor rival).
- **Partidas**: tus últimas partidas en tabla, con score, reglas cumplidas y el error de cada una; al elegir una, los detalles.
- **Campeones**: tu pool con win rate, forma reciente, mejores y peores matchups y reglas por campeón.
- **Errores**: los 3 errores que repites, con el minuto exacto para buscarlos en el replay.
- **Ajustes**: cuenta, apariencia, avisos en partida, reportes, glosario y (si administras Racha) invitar amigos.

## Ajustes

- **Cuenta**: entrar con Google o con código, bajar o recargar partidas, sincronizar, cerrar sesión o borrar tus datos de la nube.
- **Apariencia**: reducir movimiento, franja siempre encima en partida, arrancar con Windows.
- **Avisos en partida**: nivel 6 con nivel abajo, minions al 10, muertes del 14 al 25 y **plan de regreso** (del 10 al 14, si vas abajo de nivel).
- **Ayuda**: mandar reporte y métricas anónimas (apagadas por defecto).
- **Tabla del grupo** (apagada por defecto, necesita la cuenta de Google): si la activas, tus amigos de Racha ven tu Riot ID, tu win rate y tu score en su Inicio, y tú los suyos. Nunca el correo.
- **Glosario**: qué significan pick, ban, tradear, score, estimado, oro al 14 y demás.

## Cómo reportar

En **Ajustes → Ayuda → Mandar reporte**. Escribe qué hacías y qué pasó; lo lee solo quien administra Racha, sin tu Riot ID ni tu correo. Si algo se ve raro (un pick de hoy que no cuadra, una build vacía, la actualización que falla), reporta desde ahí o abre un issue en [GitHub](https://github.com/C0z1/racha.gg/issues).

## Cómo se actualiza

La versión instalada se actualiza sola: cuando hay una versión nueva, baja el instalador, comprueba su huella sha256 contra la que publica GitHub (el instalador aún no tiene firma digital) y lo corre cuando no estás en selección ni en partida; al terminar, vuelve a abrir Racha. Si prefieres, baja la release a mano desde [releases](https://github.com/C0z1/racha.gg/releases/latest). Desde el código fuente solo te avisa, no instala nada.

## Preguntas frecuentes

<details>
<summary>¿Me pueden banear por usarla?</summary>

Racha solo **lee** la información que el propio cliente de LoL ofrece a las apps (la misma que ya ves en tu pantalla) y la que devuelve la Riot API. No pickea, no banea, no acepta partidas, no mueve el cursor y no modifica el juego. Cumple las políticas de Riot: es gratis, no calcula MMR ni ELO y su contenido es un análisis propio de tus partidas.
</details>

<details>
<summary>¿Qué datos guarda?</summary>

En tu computadora: tus partidas y sus líneas de tiempo, las fotos en vivo de cada partida, tus ajustes y la caché de imágenes. En la nube (solo si entras con Google): tu Riot ID, tus ajustes y un resumen por partida (campeón, rival, resultado, KDA, score y fecha), nunca la partida completa. Nada de MMR, ELO ni tu contraseña. Los detalles están en la [política de privacidad](https://c0z1.github.io/racha.gg/privacidad.html).
</details>

<details>
<summary>¿Por qué Windows dice «Windows protegió su PC»?</summary>

Porque el instalador todavía no tiene firma digital; es normal en apps nuevas. Dale a **Más información → Ejecutar de todas formas**. El código está publicado en [GitHub](https://github.com/C0z1/racha.gg), a la vista de todos.
</details>

<details>
<summary>¿Funciona en mi servidor?</summary>

Sí: LAN, LAS, NA, EUW, KR y el resto de servidores de Riot.
</details>

---

## Para desarrolladores

Racha corre un servidor local en `127.0.0.1` y muestra la ventana con Edge en modo app. Solo lee de tres fuentes: la Riot API (con tu key o tu código de acceso), la API local del cliente (LCU) y la Live Client Data API.

```bash
python scripts/companion_web.py --demo      # la app con datos de ejemplo, sin cliente
python -m unittest discover scripts         # pruebas: sin red, sin key, sin partidas
```

### Configuración

Variables de entorno (Windows: `setx NOMBRE valor` y reabre la terminal):

| Variable | Qué es | Por defecto |
|---|---|---|
| `RIOT_KEY` | Tu key de desarrollador de Riot (caduca ~24 h). Nunca se guarda en archivos. | — (obligatoria para la Riot API local) |
| `RIOT_ID` | `"Nombre#TAG"` de la cuenta a analizar. | la cuenta con sesión en el cliente |
| `RIOT_REGION` | Plataforma: `na1`, `la1`, `la2`, `br1`, `euw1`, `eun1`, `tr1`, `ru`, `me1`, `kr`, `jp1`, `oc1`, `sg2`, `tw2`, `vn2`. | `la1` |
| `DATOS_DIR` | Carpeta alternativa para leer/escribir `datos/raw`. | `<repo>/datos/raw` |
| `META_DIR` | Carpeta alternativa para la caché de Riot API y Data Dragon. | `<repo>/datos/meta` |
| `LOL_LOCKFILE` | Ruta al lockfile del cliente. | `C:\Riot Games\League of Legends\lockfile` |

Opcional: copia `docs/config.ejemplo.json` a `config.json` (no se sube a git) para fijar tu pool y tu meta de minions al 10.

### Scripts

| Script | Qué hace |
|---|---|
| `descargar.py` | Baja partidas y timelines de Solo/Duo de la Riot API a `datos/raw/`. `[N]` partidas (por defecto 100). |
| `companion.py` | Companion de consola, solo lectura del cliente. |
| `companion_gui.py` | Companion con ventana tkinter (respaldo de la app web). `--demo`. |
| `companion_web.py` | La app Racha: servidor local y ventana con Edge. `--demo`, `--no-abrir`, `--fondo`, `--overlay`. |
| `overlay.py` | Franja en partida siempre encima (timers de dragón y barón, nivel y CS contra tu rival). |
| `humo_exe.py` | Humo de la build: arranca el `.exe`, busca su puerto y comprueba `/api/estado`. |
| `draft.py` | Matchups y recomendación de pick contra tu rival. `<rival> [rol]`. |
| `postpartida.py` | Los 3 momentos clave de una partida. `[match_id]`. |
| `revision.py` | Revisa tus últimas N partidas contra las metas del plan. `[N]`. |
| `score.py` | Score por partida contra tu equipo y la partida (50 = típico de tu rol). `[N]`. |
| `semanal.py` | Tu semana (récord, oro al 14, tilt, regla a cuidar). |
| `comparar.py` | «Tú contra ellos»: tu build contra la de los onetricks del top. `<Campeón> [rol]`. |
| `builds.py` | Build de los mejores (Challenger/GM de la1 y kr) y la tuya. `<Campeón> [rol]` o `--pool`. |
| `vistas.py` | Datos de las ventanas (Campeones, Draft, reglas, errores) sin red. |
| `nube.py` | Cuenta en la nube (Google, sincronización, borrado). |

### Pruebas

```bash
python -m unittest discover scripts
```

Sin red, sin `RIOT_KEY` y sin partidas descargadas. GitHub Actions las corre en Ubuntu y Windows en cada push (`.github/workflows/pruebas.yml`).
