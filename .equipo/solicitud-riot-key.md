# Solicitud de Personal API Key a Riot (para copiar en developer.riotgames.com)

Dónde: developer.riotgames.com → inicia sesión con tu cuenta de Riot → **Register Product** → **Personal API Key**.

**Product name:** Racha

**Product URL:** https://racha.gg (repo: https://github.com/C0z1/racha.gg)

**Product description (en inglés, como lo piden):**

> Racha is a free, ad-free desktop companion for League of Legends used by me and a small private group of friends. It helps a player improve by analyzing their own match history and aggregated matchup statistics from high-elo games.
>
> With this key I want to:
> 1. Download my own ranked matches and timelines (match-v5) to compute personal stats (CS at 10, gold at 14, deaths between minutes 14 and 25, level 6 timing).
> 2. Aggregate anonymous statistics per lane matchup from Master+ ranked games (league-v4 ladder → match-v5 + timeline): winrate, gold/XP difference by minute, which champion wins lane fights at each level window, and the most successful runes and first items per matchup. Only aggregates are stored (about 1 KB per match); raw matches and player identities are not kept or shown.
>
> Policy compliance: Racha only shows the player's own stats and aggregate pre-game data. In game it shows the player's own numbers and static, pre-computed matchup facts (no enemy cooldown/ultimate/summoner timers, no hidden information, no MMR or ELO calculation, no instructions that dictate decisions, no memory reading or injection, no automation of game actions). Rune pages are only written to the client when the user clicks "Import". The key stays on my PC and is never shipped in the app or exposed to users.

**Notas para ti:**
- La key personal no caduca, pero Riot puede revocarla si no se cumple lo de arriba. Todo lo descrito ya es así en Racha.
- Cuando llegue, guárdala con: `setx RIOT_KEY "RGAPI-..."` (o pásamela y la guardo yo en la variable, nunca en archivos).
- Mientras tanto, para probar, regenera la key de desarrollo (dura 24 h).
