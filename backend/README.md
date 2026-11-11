# Backend de Racha (mínimo, $0/mes)

Un Cloudflare Worker (plan gratis: 100,000 peticiones al día) que hace de intermediario de solo lectura entre la app y la Riot API:

- Tu key de Riot vive como **secreto** del Worker. Nunca va en el `.exe` ni en el repo.
- Solo entra quien tiene un **código de acceso** (secreto `ACCESOS`). Es una comunidad pequeña y privada, como pide Riot para una Personal API Key.
- Solo pasan las 4 consultas que usa la app: cuenta, ids de partidas, partida y timeline, y liga.
- Las partidas y los timelines no cambian, así que se guardan en la caché de Cloudflare y casi no gastan tu key.
- Sin base de datos: las partidas y el análisis se quedan en la PC de cada jugador.

## Pruebas

```bash
cd backend && node --test
```

## Desplegar (una vez)

```bash
cd backend
npx wrangler login                 # abre el navegador: entra o crea tu cuenta de Cloudflare (gratis)
npx wrangler d1 execute racha --remote --file schema.sql   # tablas (base nueva); en una base que ya existe, cada migraciones/00X_*.sql UNA vez y ANTES del deploy
npx wrangler deploy                # publica https://racha-api.<tu-subdominio>.workers.dev
npx wrangler secret put RIOT_KEY   # pega tu Personal API Key de Riot (no queda en ningún archivo)
npx wrangler secret put ACCESOS    # nombre:código,nombre:código  (uno por amigo; para quitar a alguien, vuelve a ponerlo sin él)
```

Luego pon la URL del Worker en `API_DEF` (`scripts/companion.py`) y compila una versión nueva. Cada amigo pega su código en **Ajustes → Cuenta → Código de acceso** y le da a **Descargar**.

## Límites

Una Personal API Key permite 20 peticiones por segundo y 100 cada 2 minutos. La primera descarga de un amigo (100 partidas, unas 200 peticiones) tarda unos minutos; el Worker y la app esperan solos cuando Riot pide calma (429). Para más de 20 o 30 personas, o para abrirla al público, hace falta la production key.
