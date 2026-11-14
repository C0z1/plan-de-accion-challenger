"""Partidas desde tu propio cliente de LoL, sin key ni invitación (pedido del usuario: «que bajen sus partidas desde su
launcher»). La API local del cliente da tus últimas 20 partidas con el detalle de los 10 jugadores y su timeline, en el
formato antiguo de Riot (estilo match-v4); aquí se traducen al formato match-v5 que usa el resto de Racha.

Límites (probados con el cliente real, 2026-11-10): solo las últimas 20 partidas (la paginación no pasa de ahí); el
timeline no trae compras de ítems ni subidas de habilidad (la «tu build» por compras no sale de aquí); el lane/role del
cliente es la clasificación vieja y no sirve, así que la posición se deduce: Castigo = jungla; el resto por dónde estuvo
en el mapa del minuto 2 al 10; de los dos de abajo, el de menos minions es el support."""
import json, os, pathlib, statistics as st

import companion

SMITE = 11
MARGEN_LINEA = 3500  # unidades del mapa (0–15 000): más arriba de la diagonal = top, más abajo = bot, cerca = mid


def posiciones(game, timeline):
    """{participantId: TOP/JUNGLE/MIDDLE/BOTTOM/UTILITY} deducidas; un jugador sin datos de posición queda fuera."""
    frames, out = (timeline or {}).get("frames") or [], {}
    for team in (100, 200):
        ps = [p for p in game.get("participants") or [] if p.get("teamId") == team]
        jg = [p for p in ps if SMITE in (p.get("spell1Id"), p.get("spell2Id"))]
        if jg: out[jg[0]["participantId"]] = "JUNGLE"
        zona = {}
        for p in ps:
            if p["participantId"] in out: continue
            pid = str(p["participantId"])
            xs = [f["participantFrames"][pid]["position"] for f in frames[2:11] if pid in (f.get("participantFrames") or {}) and f["participantFrames"][pid].get("position")]
            if not xs: continue
            x, y = st.mean(a["x"] for a in xs), st.mean(a["y"] for a in xs)
            zona[p["participantId"]] = "TOP" if y - x > MARGEN_LINEA else "BOTTOM" if x - y > MARGEN_LINEA else "MIDDLE"
        bots = [pid for pid, z in zona.items() if z == "BOTTOM"]
        if len(bots) == 2 and frames:
            f = frames[min(10, len(frames) - 1)]["participantFrames"]
            zona[min(bots, key=lambda pid: (f.get(str(pid)) or {}).get("minionsKilled", 0))] = "UTILITY"
        out.update(zona)
    return out


def nombres_campeones():
    """{championId: nombre de Data Dragon (el que usa match-v5, p. ej. MonkeyKing)}; {} sin Data Dragon."""
    try:
        import builds
        return {key: cid for cid, key, _ in builds.ddragon()[2].values()}
    except Exception: return {}


def a_v5(game, timeline, plataforma, campeones=None, puuids=None):
    """(match_v5, timeline_v5) con los campos que usa Racha; lo que el cliente no trae, no se inventa.
    puuids: {puuid del cliente: puuid de tu perfil} (Riot cifra el puuid distinto para cada key: es la misma persona)."""
    campeones, puuids = nombres_campeones() if campeones is None else campeones, puuids or {}
    ids = {i["participantId"]: {**(i.get("player") or {}), "puuid": puuids.get((i.get("player") or {}).get("puuid"), (i.get("player") or {}).get("puuid"))}
           for i in game.get("participantIdentities") or []}
    pos = posiciones(game, timeline)
    equipo = {p["participantId"]: p.get("teamId") for p in game.get("participants") or []}
    ps = []
    for p in game.get("participants") or []:
        s, pid, j = p.get("stats") or {}, p["participantId"], ids.get(p["participantId"], {})
        ps.append({
            "participantId": pid, "puuid": j.get("puuid"), "riotIdGameName": j.get("gameName"), "riotIdTagline": j.get("tagLine"),
            "championId": p.get("championId"), "championName": campeones.get(p.get("championId"), str(p.get("championId"))),
            "teamId": p.get("teamId"), "teamPosition": pos.get(pid, ""), "win": bool(s.get("win")),
            **{k: s.get(k, 0) for k in ("kills", "deaths", "assists", "goldEarned", "totalDamageDealtToChampions", "damageDealtToObjectives",
                                         "visionScore", "totalMinionsKilled", "neutralMinionsKilled", "champLevel")},
            **{f"item{i}": s.get(f"item{i}", 0) for i in range(7)},
            "summoner1Id": p.get("spell1Id"), "summoner2Id": p.get("spell2Id"),
            "perks": {"styles": [{"style": s.get("perkPrimaryStyle"), "selections": [{"perk": s.get(f"perk{i}")} for i in range(4)]},
                                 {"style": s.get("perkSubStyle"), "selections": [{"perk": s.get(f"perk{i}")} for i in (4, 5)]}],
                      "statPerks": {"offense": s.get("statPerk0"), "flex": s.get("statPerk1"), "defense": s.get("statPerk2")}},
        })
    match = {"metadata": {"matchId": f"{plataforma.upper()}_{game.get('gameId')}", "participants": [p["puuid"] for p in ps]},
             "info": {"gameId": game.get("gameId"), "gameCreation": game.get("gameCreation"), "gameDuration": game.get("gameDuration"),
                      "mapId": game.get("mapId"), "queueId": game.get("queueId"), "gameMode": game.get("gameMode"),
                      "platformId": plataforma.upper(), "participants": ps}}
    frames = []
    for f in (timeline or {}).get("frames") or []:
        evs = []
        for e in f.get("events") or []:
            e = dict(e)
            if e.get("type") == "ELITE_MONSTER_KILL" and "killerTeamId" not in e: e["killerTeamId"] = equipo.get(e.get("killerId"))
            evs.append(e)
        frames.append({"timestamp": f.get("timestamp"), "events": evs,
                       "participantFrames": {k: dict(v) for k, v in (f.get("participantFrames") or {}).items()}})
    tl = {"metadata": {"matchId": match["metadata"]["matchId"]},
          "info": {"frames": frames, "participants": [{"participantId": p["participantId"], "puuid": p["puuid"]} for p in ps]}}
    return match, tl


_UNO = __import__("threading").Lock()  # guardado al salir de la partida y puesta al día al conectar: nunca a la vez (DeepSeek)


def unificar(raw=None):
    """Repara una carpeta con dos puuid tuyos (el del cliente en las partidas guardadas desde él y el de la Riot API en las
    bajadas: el puuid cambia según quién lo emite; bug de 0.26–0.27). El de perfil.json manda: en las partidas sin él,
    el participante con tu Riot ID (único) revela el otro puuid, y ese texto se reemplaza por el tuyo en todas las partidas
    y timelines que lo traigan (cubre tus nombres viejos: el puuid no cambia con el nombre). Devuelve cuántos archivos reparó."""
    raw = pathlib.Path(raw or os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
    try: a = json.loads((raw / "perfil.json").read_text(encoding="utf-8"))["account"]
    except (OSError, ValueError, KeyError, TypeError): return 0
    yo, nombre = a.get("puuid"), (str(a.get("gameName") or "").lower(), str(a.get("tagLine") or "").lower())
    if not yo or not all(nombre): return 0
    partidas = sorted(raw.glob("*_*.json"))
    alias, textos = set(), {}
    for f in partidas:  # las partidas revelan el alias; luego se reparan también los timelines
        t = textos[f] = f.read_text(encoding="utf-8")
        if yo in t: continue
        try: ps = json.loads(t)["info"]["participants"]
        except (ValueError, KeyError, TypeError): continue
        c = [p.get("puuid") for p in ps if isinstance(p, dict) and (str(p.get("riotIdGameName") or "").lower(), str(p.get("riotIdTagline") or "").lower()) == nombre]
        if len(c) == 1 and c[0] and c[0] != yo: alias.add(c[0])
    n = 0
    for f in partidas + sorted((raw / "timeline").glob("*_*.json")):
        t = textos.get(f) or f.read_text(encoding="utf-8")
        if yo in t or not any(x in t for x in alias): continue  # ya está bien (nunca dos identidades tuyas en un archivo)
        for x in alias: t = t.replace(x, yo)
        tmp = f.with_suffix(".tmp"); tmp.write_text(t, encoding="utf-8"); tmp.replace(f); n += 1
    return n


def descargar(raw=None, leer=None, n=20):
    with _UNO: return _descargar(raw, leer, n)


def _descargar(raw=None, leer=None, n=20):
    """Baja del cliente tus últimas n partidas (máx. 20) que aún no estén en datos/raw. Devuelve (nuevas, mensaje)."""
    leer = leer or companion.lcu
    raw = pathlib.Path(raw or os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
    s = leer("/lol-summoner/v1/current-summoner") or {}
    if not s.get("puuid"): return 0, "Abre el cliente de LoL y entra a tu cuenta."
    h = leer("/lol-match-history/v1/products/lol/current-summoner/matches?begIndex=0&endIndex=20") or {}
    plat = str(h.get("platformId") or "la1").upper()
    raw.mkdir(parents=True, exist_ok=True); (raw / "timeline").mkdir(exist_ok=True)
    perfil = raw / "perfil.json"
    try: viejo = json.loads(perfil.read_text(encoding="utf-8"))["account"]
    except (OSError, ValueError, KeyError): viejo = None
    nombre = lambda a: (str(a.get("gameName") or "").lower(), str(a.get("tagLine") or "").lower())
    if viejo and viejo.get("puuid") != s["puuid"] and nombre(viejo) != nombre(s):  # el puuid cambia según la key: se compara el Riot ID
        return 0, "Esta PC guarda el historial de otra cuenta: para el tuyo, usa Racha en tu PC."
    puuids = {s["puuid"]: viejo["puuid"]} if viejo and viejo.get("puuid") else {}  # tus partidas del cliente quedan con el puuid de tu perfil
    if not viejo: perfil.write_text(json.dumps({"account": {"puuid": s["puuid"], "gameName": s.get("gameName"), "tagLine": s.get("tagLine")}, "league": []}, indent=1), encoding="utf-8")
    campeones, nuevas = nombres_campeones(), 0
    for g in (((h.get("games") or {}).get("games")) or [])[:n]:
        gid = g.get("gameId"); f = raw / f"{plat}_{gid}.json"
        if not gid or f.exists(): continue
        game, tl = leer(f"/lol-match-history/v1/games/{gid}"), leer(f"/lol-match-history/v1/game-timelines/{gid}")
        if not isinstance(game, dict) or not isinstance(tl, dict): continue  # cliente a medias: nunca guardar basura
        m, t = a_v5(game, tl, plat, campeones, puuids)
        for destino, datos in ((raw / "timeline" / f.name, t), (f, m)):  # la partida al final: sin timeline no se da por bajada
            tmp = destino.with_suffix(".tmp"); tmp.write_text(json.dumps(datos), encoding="utf-8"); tmp.replace(destino)
        nuevas += 1
    return nuevas, (f"{nuevas} partida{'s' if nuevas != 1 else ''} nueva{'s' if nuevas != 1 else ''} desde tu cliente." if nuevas else "Tus partidas del cliente ya estaban bajadas.")
