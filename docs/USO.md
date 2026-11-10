# Uso detallado

Aquí va el detalle técnico que no cabe en el `README.md`: configuración, scripts y sus argumentos, y pruebas.

## Configuración

Variables de entorno (Windows: `setx NOMBRE valor` y reabre la terminal):

| Variable | Qué es | Por defecto |
|---|---|---|
| `RIOT_KEY` | Tu key de desarrollador de Riot (caduca ~24 h). Nunca se guarda en archivos. | — (obligatoria para la Riot API) |
| `RIOT_ID` | `"Nombre#TAG"` de la cuenta a analizar. | `cozi#1134` |
| `RIOT_REGION` | Plataforma: `na1`, `la1`, `la2`, `br1`, `euw1`, `eun1`, `tr1`, `ru`, `me1`, `kr`, `jp1`, `oc1`, `sg2`, `tw2`, `vn2`. | `la1` |
| `DATOS_DIR` | Carpeta alternativa para leer/escribir `datos/raw`. | `<repo>/datos/raw` |
| `META_DIR` | Carpeta alternativa para la caché de Riot API y Data Dragon. | `<repo>/datos/meta` |
| `LOL_LOCKFILE` | Ruta al lockfile del cliente de LoL. | `C:\Riot Games\League of Legends\lockfile` |

Opcional:

- **Pool y metas:** copia `config.ejemplo.json` a `config.json` (no se sube a git). Sin `config.json`, el pool son tus 3 campeones más jugados y no hay meta de minions al 10.
- **Otra cuenta sin mezclar:** `DATOS_DIR=<carpeta>` para analizar una cuenta distinta.

## Scripts

Todos corren con `python scripts/<script>.py` desde la raíz del repo y leen `datos/raw/` (o `DATOS_DIR`). Sin red ni key para los que solo leen datos locales.

### Recolección

| Script | Qué hace | Argumentos |
|---|---|---|
| `descargar.py` | Baja partidas y timelines de Solo/Duo de la Riot API a `datos/raw/`. | `[N]` (número de partidas; por defecto 100) |
| `analizar.py` | Resume `datos/raw/*.json` en estadísticas agregadas. | — |
| `companion.py` | Companion de consola: lee el cliente en solo lectura; en champ select corre `draft.py` contra tu rival; en partida graba la Live Client Data cada 30 s y avisa de nivel/minions/muertes; al terminar baja 5 partidas y revisa la nueva. | `--fixture CARPETA` (una pasada con JSON de ejemplo, sin cliente) |
| `companion_gui.py` | Companion con ventana tkinter (respaldo de la app web). | `--demo` |
| `companion_web.py` | La app HTC: servidor local en `127.0.0.1` con la interfaz del `README`, abierta en Edge. | `--demo`, `--no-abrir` |
| `humo_exe.py` | Humo de la build: arranca `HTC.exe --demo --no-abrir`, encuentra su puerto y comprueba `/api/estado`. | `[ruta-del-exe]` |

### Antes y después de la partida

| Script | Qué hace | Argumentos |
|---|---|---|
| `draft.py` | Matchups y recomendación de pick contra tu rival. | `<rival> [rol]` (rol por defecto `mid`) |
| `revision.py` | Revisa tus últimas N partidas contra las metas del plan. | `[N]` (por defecto 20) |
| `score.py` | Score por partida contra tu equipo y la partida (50 = típico de tu rol), tendencia y qué te baja. | `[N]` (por defecto 10) |
| `partida.py` | Replay en datos de una partida, minuto a minuto. | `[id [--early] | --ultimas N]` |
| `recorrido_ficha.py` | Champ select en texto contra tus N rivales más frecuentes de un rol. | `[rol] [N]` (mid, 10 por defecto) |
| `builds.py` | Build de los mejores (Challenger/GM de la1 y kr) y la tuya; necesita `RIOT_KEY`. | `<Campeón> [rol]` o `--pool` |
| `minions10.py` | Meta de minions al 10 (lee `config.json`). | `[campeón] [mínimo]` |

### Análisis profundo (sin argumentos salvo que se indique)

`early.py`, `timeline.py`, `midgame.py`, `linea.py [Campeón]`, `convertir.py [Campeón]`, `xp.py`, `nivel6.py`, `muertes6.py`, `wards.py`, `objetivos.py`, `placas.py`, `castigo.py`, `rol.py`, `corte6.py`, `anticipa.py`, `sin_objetivo.py`. Sin argumento, `linea.py` y `convertir.py` usan tu campeón más jugado.

## Pruebas

```bash
python -m unittest discover scripts
```

Sin red, sin `RIOT_KEY` y sin partidas descargadas: sin `datos/raw` usan `scripts/fixtures/datos`. GitHub Actions las corre en Ubuntu y Windows en cada push (`.github/workflows/pruebas.yml`).
