"""Matchups de muchas partidas (PLAN-MATCHUPS.md, Fable + DeepSeek): de partidas Master+ de mains de un campeón, quién
gana cada ventana de nivel en la línea, el oro por minuto, el WR del matchup y las runas y el primer ítem que más ganan.
  python scripts/matchups.py --pool                 rastrea tu pool (necesita RIOT_KEY; reanudable)
  python scripts/matchups.py --campeon Zeri --pos BOTTOM --jugadores 60
  python scripts/matchups.py --agregar              rehace datos/meta/matchups.json desde las filas
Solo se guardan filas de ~1 KB por partida (sin crudos ni nombres de jugadores). Las frases son datos históricos, nunca
órdenes (Riot: no dictar decisiones)."""
import argparse, collections, json, math, os, pathlib, statistics as st, sys, time

DIR = pathlib.Path(__file__).resolve().parent
META = pathlib.Path(os.environ.get("META_DIR") or DIR.parent / "datos" / "meta")
FILAS, SALIDA = META / "matchups-filas.jsonl", META / "matchups.json"
VENTANAS = (("1-3", 1, 3), ("4-5", 4, 5), ("6-8", 6, 8), ("9-10", 9, 10), ("11+", 11, 18))
LINEA_MS = 14 * 60000  # muertes de línea: antes del minuto 14
MIN_PARTIDAS, MIN_MUERTES = 100, 50  # DeepSeek: con menos, no hay frase (cae a lo de siempre)
Z_VENTANAS = 2.576  # Wilson al 99 %: Bonferroni por las 5 ventanas (0,05 / 5)
REMAKE_S = 300


def wilson(k, n, z=1.96):
    if not n: return (0.0, 1.0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def _nivel_en(ups, t):
    """Nivel de un participante en el instante t (ms), desde sus LEVEL_UP (empieza en 1)."""
    return 1 + sum(1 for x in ups if x <= t)


def fila(match, timeline, puuid):
    """Una fila por partida para el jugador `puuid` (lado A) contra su rival de línea (B); None si no aplica (remake, otro
    modo, sin posición o sin rival). Muerte de línea: antes del 14, víctima de una línea (en bot: tirador o support) y el
    otro lado en el asesinato (asesino o asistente). Nivel de A y B en cada muerte, desde los LEVEL_UP del timeline."""
    try:
        info = match["info"]
        if info.get("gameMode", "CLASSIC") != "CLASSIC" or (info.get("gameDuration") or 0) < REMAKE_S: return None
        ps = info["participants"]; a = next(p for p in ps if p["puuid"] == puuid); pos = a.get("teamPosition") or ""
        if not pos: return None
        b = next((p for p in ps if p.get("teamPosition") == pos and p["teamId"] != a["teamId"]), None)
        if not b: return None
        linea = lambda eq: {p["participantId"] for p in ps if p["teamId"] == eq and p.get("teamPosition") in (("BOTTOM", "UTILITY") if pos in ("BOTTOM", "UTILITY") else (pos,))}
        la, lb = linea(a["teamId"]), linea(b["teamId"])
        fr = timeline["info"]["frames"]; ev = [e for f in fr for e in f.get("events", ())]
        ups = collections.defaultdict(list)
        for e in ev:
            if e.get("type") == "LEVEL_UP": ups[e.get("participantId")].append(e["timestamp"])
        muertes = []
        for e in ev:
            if e.get("type") != "CHAMPION_KILL" or e.get("timestamp", 0) >= LINEA_MS: continue
            mata = {e.get("killerId"), *(e.get("assistingParticipantIds") or [])}
            if e.get("victimId") in lb and mata & la: gana = "A"
            elif e.get("victimId") in la and mata & lb: gana = "B"
            else: continue
            t = e["timestamp"]
            nivel = lambda pid: _nivel_en(ups[pid], t) if ups[pid] else ((fr[min(len(fr) - 1, t // 60000)]["participantFrames"].get(str(pid)) or {}).get("level") or 1)  # sin LEVEL_UP (timeline del cliente): el del fotograma
            muertes.append({"t": t // 1000, "gana": gana, "na": nivel(a["participantId"]), "nb": nivel(b["participantId"]),
                            "solo": not e.get("assistingParticipantIds")})
        pf = lambda m, pid, k: fr[m]["participantFrames"][str(pid)][k] if len(fr) > m else None
        dif = lambda m, f: (f(m, a["participantId"]) - f(m, b["participantId"])) if len(fr) > m else None
        oro, xp = (lambda m, pid: pf(m, pid, "totalGold")), (lambda m, pid: pf(m, pid, "xp"))
        cs = lambda m, pid: (pf(m, pid, "minionsKilled") or 0) + (pf(m, pid, "jungleMinionsKilled") or 0)
        s6 = [sorted(ups[x["participantId"]])[4] if len(ups[x["participantId"]]) >= 5
              else next((i * 60000 for i, f_ in enumerate(fr) if ((f_["participantFrames"].get(str(x["participantId"])) or {}).get("level") or 0) >= 6), None) for x in (a, b)]  # 5.º LEVEL_UP = nivel 6; si no, el primer fotograma en 6
        st_ = a.get("perks", {}).get("styles") or [{}, {}]
        return {"parche": ".".join(str(info.get("gameVersion", "")).split(".")[:2]), "A": a["championName"], "B": b["championName"], "pos": pos,
                "win": bool(a.get("win")), "gd": {m: dif(m, oro) for m in (5, 10, 14)}, "xpd14": dif(14, xp), "csd10": dif(10, cs),
                "primero6": None if None in s6 else s6[0] < s6[1], "muertes": muertes,
                "runa": (st_[0].get("selections") or [{}])[0].get("perk"),
                "pagina": [st_[0].get("style"), st_[1].get("style")] + [s.get("perk") for x in st_[:2] for s in x.get("selections") or []]
                          + [a.get("perks", {}).get("statPerks", {}).get(k) for k in ("offense", "flex", "defense")],
                "items": [a.get(f"item{i}") for i in range(6) if a.get(f"item{i}")]}
    except (KeyError, TypeError, StopIteration, IndexError):
        return None


def agregar(filas, legendarios=None):
    """{«A|POS|B»: resumen} con n, wr, wr_base de A y de B en la muestra, ventanas [kA, kB], primero6, oro, wr si sale abajo,
    runa clave y primer legendario más usados con su WR, y la página de runas más usada con esa runa."""
    filas = [f for f in filas if f]
    base_a = collections.defaultdict(lambda: [0, 0]); base_b = collections.defaultdict(lambda: [0, 0])
    for f in filas:
        base_a[f["A"]][0] += f["win"]; base_a[f["A"]][1] += 1
        base_b[f["B"]][0] += not f["win"]; base_b[f["B"]][1] += 1  # B como rival de mains: su WR en esta muestra
    grupos = collections.defaultdict(list)
    for f in filas: grupos[f"{f['A']}|{f['pos']}|{f['B']}"].append(f)
    out = {"_parches": sorted({f["parche"] for f in filas}, reverse=True)[:2]}
    for k, fs in grupos.items():
        n, v = len(fs), sum(f["win"] for f in fs)
        ven = {nom: [0, 0] for nom, *_ in VENTANAS}
        for f in fs:
            for m in f["muertes"]:
                nom = next(nom for nom, lo, hi in VENTANAS if lo <= min(m["na"], 18) <= hi)
                ven[nom][0 if m["gana"] == "A" else 1] += 1
        p6 = [f["primero6"] for f in fs if f["primero6"] is not None]
        g14 = [f["gd"].get(14) if isinstance(f["gd"], dict) else None for f in fs]
        abajo = [f for f, g in zip(fs, g14) if g is not None and g < 0]
        med = lambda xs: round(st.median(xs)) if xs else None
        runa = _mas_ganadora([(f["runa"], f["win"]) for f in fs if f.get("runa")])
        leg = legendarios or set()
        primer = _mas_ganadora([(next((i for i in f["items"] if str(i) in leg), None), f["win"]) for f in fs if leg]) if leg else None
        pag = collections.Counter(tuple(f["pagina"]) for f in fs if runa and f.get("runa") == runa["id"] and len(f.get("pagina") or []) == 11)
        a, _, b = k.split("|")
        out[k] = {"n": n, "wr": round(v / n, 3), "wr_base_a": round(base_a[a][0] / base_a[a][1], 3), "wr_base_b": round(base_b[b][0] / base_b[b][1], 3),
                  "ventanas": ven, "primero6": round(sum(p6) / len(p6), 3) if p6 else None,
                  "gd": {m: med([f["gd"].get(m) if isinstance(f["gd"], dict) else None for f in fs if isinstance(f["gd"], dict) and f["gd"].get(m) is not None]) for m in (5, 10, 14)},
                  "wr_si_abajo": [sum(f["win"] for f in abajo), len(abajo)], "runa": runa, "primer": primer,
                  "pagina_ids": list(pag.most_common(1)[0][0]) if pag else None}
    return out


def _mas_ganadora(pares, minimo=30, uso=0.2):
    """La opción más usada (≥ 20 % de uso y n ≥ 30) con su WR; «alternativa» solo si el piso de Wilson de otra supera ese WR."""
    pares = [(x, w) for x, w in pares if x is not None]
    if not pares: return None
    c = collections.Counter(x for x, _ in pares); tot = len(pares)
    stats = {x: (sum(w for y, w in pares if y == x), m) for x, m in c.items() if m >= minimo and m / tot >= uso}
    if not stats: return None
    top = max(stats, key=lambda x: stats[x][1]); v, m = stats[top]
    alt = next((x for x, (vv, mm) in sorted(stats.items(), key=lambda kv: -kv[1][0] / kv[1][1]) if x != top and wilson(vv, mm)[0] > v / m), None)
    return {"id": top, "wr": round(v / m, 3), "n": m, **({"alternativa": alt, "wr_alt": round(stats[alt][0] / stats[alt][1], 3)} if alt else {})}


def frases(m, a, b, nombre=lambda x: x, maximo=3):
    """Hasta 3 frases de dato histórico (nunca órdenes), ordenadas por lo lejos del 50 % que está el intervalo. Cada una
    lleva su n. Ventanas: solo si hay ≥ 50 muertes y el piso de Wilson (99 %, por las 5 ventanas) no cruza el 50 %."""
    if not m or m.get("n", 0) < MIN_PARTIDAS: return []
    cand = []
    for nom, (ka, kb) in (m.get("ventanas") or {}).items():
        n = ka + kb
        if n < MIN_MUERTES: continue
        lo, hi = wilson(ka, n, Z_VENTANAS)
        if lo > .5: cand.append((lo - .5, f"{a} gana el nivel {nom} contra {b}: {round(ka / n * 100)} % de las muertes de línea (n={n})"))
        elif hi < .5: cand.append((.5 - hi, f"{b} manda en el nivel {nom}: {round(kb / n * 100)} % de las muertes de línea (n={n})"))
    g, (va, na) = (m.get("gd") or {}).get(14), m.get("wr_si_abajo") or (0, 0)
    if g is not None and na >= 30:
        cand.append((.01, f"Oro al 14: {g:+d} de mediana; aun abajo, {a} gana {round(va / na * 100)} % (n={na})"))
    if (r := m.get("runa")): cand.append((.005, f"Runa más usada aquí: {nombre(r['id'])} {round(r['wr'] * 100)} % (n={r['n']})"))
    return [t for _, t in sorted(cand, key=lambda x: -x[0])[:maximo]]


def guardado(a, pos, b, archivo=None):
    """El resumen del matchup (sin red), o None si falta, está cortado o tiene pocas partidas."""
    try: d = json.loads(pathlib.Path(archivo or SALIDA).read_text(encoding="utf-8"))
    except (OSError, ValueError): return None
    m = d.get(f"{a}|{pos}|{b}") if isinstance(d, dict) else None
    return m if m and m.get("n", 0) >= MIN_PARTIDAS else None


def rastrear(campeon, pos, jugadores=60, partidas=40, regiones=None):
    """Baja partidas ranked de mains Master+ del campeón (league-v4 → maestría → match-v5 + timeline) y añade una fila
    por partida a FILAS. Reanudable: salta las partidas ya vistas. Necesita RIOT_KEY. Devuelve cuántas filas agregó."""
    import builds
    vistas = set()
    if FILAS.exists():
        for l in FILAS.read_text(encoding="utf-8").splitlines():
            try: vistas.add(json.loads(l).get("id"))
            except ValueError: pass
    cid = builds.ddragon()[2][builds.norm(campeon)][1]; nuevas = 0
    META.mkdir(parents=True, exist_ok=True)
    for plat, ruta in (regiones or builds.REGIONES).items():
        lad = []
        for liga in ("challengerleagues", "grandmasterleagues", "masterleagues"):
            lad += (builds.get(f"https://{plat}.api.riotgames.com/lol/league/v4/{liga}/by-queue/RANKED_SOLO_5x5", ttl=builds.DIA, riot=True) or {}).get("entries", [])
        mains = 0
        for e in sorted(lad, key=lambda e: -e["leaguePoints"]):
            if mains >= jugadores: break
            mae = builds.get(f"https://{plat}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/{e['puuid']}/by-champion/{cid}", ttl=builds.DIA, riot=True)
            if not mae or (mae.get("championPoints") or 0) < 100000: continue  # main: 100 mil puntos o más con el campeón
            mains += 1
            ids = builds.get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/by-puuid/{e['puuid']}/ids?queue=420&count={partidas}", ttl=builds.DIA, riot=True) or []
            for mid in ids:
                if mid in vistas: continue
                m = builds.get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/{mid}", riot=True, guardar=False)
                yo = next((p for p in (m or {}).get("info", {}).get("participants", []) if p["puuid"] == e["puuid"]), None)
                if not yo or yo["championName"].lower() != campeon.lower() or yo.get("teamPosition") != pos: vistas.add(mid); continue
                t = builds.get(f"https://{ruta}.api.riotgames.com/lol/match/v5/matches/{mid}/timeline", riot=True, guardar=False)
                f = fila(m, t, e["puuid"]) if t else None
                vistas.add(mid)
                if f:
                    with FILAS.open("a", encoding="utf-8") as h: h.write(json.dumps({"id": mid, **f}, ensure_ascii=False) + "\n")
                    nuevas += 1
    return nuevas


def rehacer():
    """Recalcula matchups.json desde todas las filas (parche actual y anterior)."""
    filas = []
    if FILAS.exists():
        for l in FILAS.read_text(encoding="utf-8").splitlines():
            try: filas.append(json.loads(l))
            except ValueError: pass
    parches = sorted({f.get("parche") for f in filas}, key=lambda p: [int(x) for x in p.split(".") if x.isdigit()], reverse=True)[:2]
    try:
        import builds; leg = {k for k, v in builds.ddragon()[0].items() if builds.legendario(v)}
    except Exception: leg = None
    d = agregar([f for f in filas if f.get("parche") in parches], leg)
    SALIDA.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(); p.add_argument("--campeon"); p.add_argument("--pos", default="MIDDLE")
    p.add_argument("--jugadores", type=int, default=60); p.add_argument("--pool", action="store_true"); p.add_argument("--agregar", action="store_true")
    a = p.parse_args(argv)
    if a.pool or a.campeon:
        import draft
        objetivos = [(a.campeon, a.pos)] if a.campeon else [(c, a.pos) for c in draft.pool(a.pos)]
        for c, pos in objetivos: print(c, pos, "filas nuevas:", rastrear(c, pos, a.jugadores), flush=True)
    d = rehacer(); print(len(d) - 1, "matchups en", SALIDA)


if __name__ == "__main__": main()
