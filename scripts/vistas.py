"""Datos de las ventanas nuevas de HTC (artboards *_Vino del Diseñador): Campeones, Draft, reglas «Cumples N/20» y Errores.
Todo sale de datos/raw (sin red) y va en la caché de rendimiento de companion_web.
  python scripts/vistas.py   imprime el JSON (para revisar)"""
import json, statistics as st, sys, time
from collections import Counter, defaultdict

import draft, score

R_KP = dict(texto="Únete a las peleas del 14 en adelante", por_que="Tu participación en kills es lo que más te baja el score",
            metrica="kp", minuto="14+")


def _forma(rs, k=5): return [g["win"] for g in rs[-k:]]


def _vs(rs, minimo=3):
    """(mejores, peores) rivales de línea por WR con ese campeón (3+ partidas cada uno)."""
    por = defaultdict(list)
    for g in rs:
        if g["opp"] != "?": por[g["opp"]].append(g["win"])
    xs = sorted(((sum(w) / len(w), len(w), o) for o, w in por.items() if len(w) >= minimo), key=lambda x: (-x[0], -x[1]))
    return [o for wr, _, o in xs if wr > .5][:2], [o for wr, _, o in reversed(xs) if wr < .5][:3]


def etiqueta(n, wr, forma, base):
    if n < 8: return "Pocas partidas"
    if wr >= base + .05: return "Pickéalo"
    if len(forma) == 5 and sum(forma) <= 1: return "Bajando"
    return "Estable" if wr >= base - .03 else "Evítalo vs sus counters"


def campeones(minimo=3):
    """Tu pool de la temporada: por campeón (más jugado primero) n, rol, WR, forma (V/D de las últimas 5),
    etiqueta, mejor/peor contra, CS al 14 contra cada counter y sus reglas con «cumples» en sus últimas 20."""
    by = defaultdict(list)
    for g in sorted(draft.games, key=lambda g: g["t"]): by[g["champ"]].append(g)
    out = []
    for c, rs in sorted(by.items(), key=lambda x: -len(x[1])):
        if len(rs) < minimo: continue
        pos = Counter(g["pos"] for g in rs).most_common(1)[0][0]
        w = sum(g["win"] for g in rs) / len(rs); mejor, peor = _vs(rs)
        cs = []
        for o in peor:
            v = [g["cs14"] for g in rs if g["opp"] == o and g.get("cs14") is not None]
            cs.append(dict(rival=o, cs14=round(st.mean(v)) if v else None, n=sum(g["opp"] == o for g in rs)))
        out.append(dict(champ=c, pos=pos, n=len(rs), wr=round(w, 3), forma=_forma(rs), etiqueta=etiqueta(len(rs), w, _forma(rs), draft.base),
                        mejor=mejor, peor=peor, counters=cs, reglas=cumple(draft.reglas(c, pos), rs[-20:]), build=_build(c, pos)))
    return out


def _build(campeon, pos):
    """La build guardada de builds.py (sin red) para «Tu build» de Campeones_Vino; None si no hay o si builds.py truena."""
    try: import builds; return builds.guardado_dict(campeon, pos)
    except Exception: return None


def cumple(rs_reglas, gs):
    """Cada regla del PLAN con cuántas de gs la cumplen (solo las partidas con dato): {texto, numero, minuto, metrica, ok, n}."""
    out = []
    for r in rs_reglas:
        v = [g[r["campo"]] for g in gs if r.get("campo") and g.get(r["campo"]) is not None]
        out.append(dict(texto=r["texto"], numero=r["numero"], minuto=r.get("minuto"), metrica=r.get("metrica"),
                        ok=sum(map(r["ok"], v)) if v else None, n=len(v)))
    return out


def reglas_perfil(comp20):
    """«Qué cambiar» (Perfil_Vino): las 4 reglas del plan con cumples en tus últimas 20, la que más cuesta primero.
    comp20 = [comp de score.resumen] para la de KP (cumple = KP en o sobre lo típico de tu rol)."""
    gs = sorted(draft.games, key=lambda g: g["t"])[-20:]
    sylas = [g for g in sorted(draft.games, key=lambda g: g["t"]) if g["champ"] == "Sylas"][-20:]
    rs = cumple([draft.R_NIVEL6, draft.R_MUERTES], gs)
    rs += cumple([r for r in draft.REGLAS_CHAMP.get("Sylas", []) if r.get("campo") == "min10"], sylas)
    k = [c.get("kp") for c in comp20 if c.get("kp") is not None]
    rs.append(dict(texto=R_KP["texto"], numero=R_KP["por_que"], minuto="14+", metrica="kp", ok=sum(z >= 0 for z in k) if k else None, n=len(k)))
    return sorted(rs, key=lambda r: (r["ok"] / r["n"]) if r["n"] else 2)


def draft_rol(pos, dias=90):
    """Draft_Vino: a quién banear en el rol (peor WR contra él, 3+ partidas, con el porqué medido), rivales frecuentes
    de los últimos `dias` y tu pool del rol (5+ partidas)."""
    rol = [g for g in draft.games if g["pos"] == pos]
    por = defaultdict(list)
    for g in rol:
        if g["opp"] != "?": por[g["opp"]].append(g)
    ref = draft.medidas(rol)
    bans = []
    for o, rs in por.items():
        if len(rs) < 3: continue
        v = sum(g["win"] for g in rs); m = draft.medidas(rs)
        if m.get("cs14") is not None and ref.get("cs14") is not None and m["cs14"] - ref["cs14"] <= -10:
            pq = f"Te niega el farm: {m['cs14'] - ref['cs14']:+.0f} CS al 14 contra tu media del rol"
        elif m.get("muertes6") is not None and ref.get("muertes6") is not None and m["muertes6"] > ref["muertes6"] + .3:
            pq = f"Mueres antes del 6: {m['muertes6']:.1f} por partida (tu media {ref['muertes6']:.1f})"
        else: pq = f"Vas {v}-{len(rs) - v} contra él en el rol"
        bans.append(dict(rival=o, v=v, n=len(rs), est=round(draft.shrink(v, len(rs), draft.base), 3), por_que=pq.replace("-", "−")))
    bans.sort(key=lambda b: b["est"])
    desde = (time.time() - dias * 86400) * 1000
    rec = Counter(g["opp"] for g in rol if g["t"] >= desde and g["opp"] != "?")
    frec = [dict(rival=o, v=sum(g["win"] for g in por[o]), n=len(por[o]), recientes=k) for o, k in rec.most_common(4)]
    pool = [dict(champ=c, n=len(rs), wr=round(sum(g["win"] for g in rs) / len(rs), 3)) for c, rs in
            sorted(draft.pool(pos).items(), key=lambda x: -len(x[1]))][:3]
    return dict(pos=pos, bans=bans[:3], frecuentes=frec, pool=pool)


def errores(gs, n=20):
    """Errores_Vino: los 3 errores repetidos en tus últimas n partidas con timeline, cada uno con sus momentos
    [{campeon, rival, minuto «mm:ss», archivo}]. gs = score.partidas()[0].
    sin_objetivo: tu muerte del 14 al 25 sin dragón/heraldo/barón/torre de tu equipo en el minuto antes ni en el siguiente.
    abajo_6: kill en la que participas (o mueres) del 5:30 al 7:00 con menos nivel que tu rival al minuto 6.
    sin_pelea: pelea del 14 en adelante (3+ muertes en 30 s) que tu equipo pierde (más muertes suyas), sin kill, asistencia ni muerte tuya."""
    mm = lambda ms: f"{ms // 60000}:{ms // 1000 % 60:02d}"
    out = {k: [] for k in ("sin_objetivo", "abajo_6", "sin_pelea")}
    vistos = 0
    for g in reversed(gs):
        if vistos >= n: break
        tf = g["f"].parent / "timeline" / g["f"].name
        try:
            fr = json.loads(tf.read_text())["info"]["frames"]; info = json.loads(g["f"].read_text())["info"]
        except (OSError, ValueError, KeyError): continue
        vistos += 1
        yo = g["pid"]; me = next(p for p in info["participants"] if p["participantId"] == yo); eq = me["teamId"]
        opp = next((p for p in info["participants"] if p["teamPosition"] == me["teamPosition"] and p["teamId"] != eq), None)
        equipo = {p["participantId"]: p["teamId"] for p in info["participants"]}
        base = dict(campeon=g["champ"], rival=opp["championName"] if opp else None, archivo=g["f"].stem)
        ev = [e for f in fr for e in f["events"]]
        kills = [e for e in ev if e["type"] == "CHAMPION_KILL"]
        mio = lambda e: yo in (e.get("killerId"), e.get("victimId")) or yo in (e.get("assistingParticipantIds") or [])
        obj = [e["timestamp"] for e in ev if (e["type"] == "ELITE_MONSTER_KILL" and e.get("killerTeamId") == eq)
               or (e["type"] == "BUILDING_KILL" and e.get("teamId") not in (None, eq))]
        for e in kills:
            if e.get("victimId") == yo and 14 * 60000 <= e["timestamp"] < 25 * 60000 and not any(-60000 <= t - e["timestamp"] <= 60000 for t in obj):  # ±60 s: morir asegurando o robando no cuenta (scripts/sin_objetivo.py)
                out["sin_objetivo"].append({**base, "minuto": mm(e["timestamp"])})
        if opp and len(fr) > 6:
            pf = fr[6].get("participantFrames") or {}
            nv = lambda pid: (pf.get(str(pid)) or {}).get("level")
            if None not in (nv(yo), nv(opp["participantId"])) and nv(yo) < nv(opp["participantId"]):
                e = next((e for e in kills if 330000 <= e["timestamp"] < 420000 and mio(e)), None)
                if e: out["abajo_6"].append({**base, "minuto": mm(e["timestamp"])})
        i, tarde = 0, [e for e in kills if e["timestamp"] >= 14 * 60000]
        while i < len(tarde):  # peleas: kills encadenadas a menos de 30 s
            j = i
            while j + 1 < len(tarde) and tarde[j + 1]["timestamp"] - tarde[j]["timestamp"] <= 30000: j += 1
            pelea = tarde[i:j + 1]
            caen = sum(equipo.get(e.get("victimId")) == eq for e in pelea)  # muertes de tu equipo
            if len(pelea) >= 3 and caen > len(pelea) - caen and not any(mio(e) for e in pelea): out["sin_pelea"].append({**base, "minuto": mm(pelea[0]["timestamp"])})
            i = j + 1
    cuenta = {k: len({m["archivo"] for m in v}) for k, v in out.items()}
    return dict(n=vistos, partidas=cuenta, momentos=out)


def todo(resumen):
    """Lo que necesitan las ventanas, para guardarlo junto a rendimiento()."""
    gs = score.partidas()[0]
    pos = Counter(g["pos"] for g in draft.games[-50:]).most_common(1)[0][0]
    return dict(campeones=campeones(), reglas=reglas_perfil([p["comp"] for p in resumen["partidas"]]),
                draft={p: draft_rol(p) for p in ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY")}, pos=pos, errores=errores(gs),
                total=len(draft.games), ultima=max(g["t"] for g in draft.games))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(todo(score.resumen(20)), ensure_ascii=False, indent=1, default=str)[:6000])
