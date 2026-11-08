"""Mid game: ¿por qué pierdes partidas en las que llegas al 14 con oro >= 0 contra tu rival?
Compara victorias y derrotas de ese grupo: oro del equipo, muertes del 14 al 25 (zona, enemigos,
pick-off o pelea, shutdown entregado, objetivo perdido después).
Uso: python scripts/midgame.py > datos/analisis-midgame-AAAA-MM-DD.md"""
import json, os, math, pathlib, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
VENTANA_PELEA, RADIO_PELEA, VENTANA_OBJ = 15_000, 3000, 90_000  # ms, unidades del mapa, ms


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


def wr(rs):
    if not rs: return "-"
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k}/{len(rs)} = {k / len(rs):.0%} ({lo:.0%}–{hi:.0%})"


def zone(x, y, team):  # misma función que scripts/timeline.py
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"


def es_pickoff(e, kills):
    """Sin otra muerte (de nadie) a menos de 15 s y 3000 unidades: te agarraron solo, no fue una pelea."""
    p = e["position"]
    return not any(o is not e and abs(o["timestamp"] - e["timestamp"]) <= VENTANA_PELEA
                   and math.dist((p["x"], p["y"]), (o["position"]["x"], o["position"]["y"])) <= RADIO_PELEA
                   for o in kills)
_k = [dict(timestamp=0, position=dict(x=0, y=0)), dict(timestamp=5000, position=dict(x=100, y=0)),
      dict(timestamp=60000, position=dict(x=0, y=0))]
assert not es_pickoff(_k[0], _k) and es_pickoff(_k[2], _k)


games, deaths = [], []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    fr = json.loads(tf.read_text())["info"]["frames"]
    if not opp or len(fr) <= 14: continue
    pid, team = me["participantId"], me["teamId"]
    aliados = {p["participantId"] for p in ps if p["teamId"] == team}
    oro = lambda mn, i: fr[mn]["participantFrames"][str(i)]["totalGold"]
    eq = lambda mn: sum(oro(mn, p["participantId"]) * (1 if p["teamId"] == team else -1) for p in ps)
    g = dict(win=me["win"], champ=me["championName"], gd14=oro(14, pid) - oro(14, opp["participantId"]),
             tg14=eq(14), tg20=eq(20) if len(fr) > 20 else None, d1425=0, pick=0, shut=0, obj=0)
    evs = [e for f in fr for e in f["events"]]
    kills = [e for e in evs if e["type"] == "CHAMPION_KILL"]
    perdidos = [e for e in evs if (e["type"] == "ELITE_MONSTER_KILL" and e.get("killerTeamId") not in (team, None))
                or (e["type"] == "BUILDING_KILL" and e.get("teamId") == team)]
    for e in kills:
        if e["victimId"] != pid or not 14 <= e["timestamp"] / 60000 < 25: continue
        who = {e["killerId"], *e.get("assistingParticipantIds", [])} - {0} - aliados
        d = dict(win=g["win"], lane_ok=g["gd14"] >= 0, n=len(who), pick=es_pickoff(e, kills),
                 shut=e.get("shutdownBounty", 0) > 0, zona=zone(e["position"]["x"], e["position"]["y"], team),
                 obj=any(0 < o["timestamp"] - e["timestamp"] <= VENTANA_OBJ for o in perdidos))
        deaths.append(d)
        g["d1425"] += 1; g["pick"] += d["pick"]; g["shut"] += d["shut"]; g["obj"] += d["obj"]
    # línea base: en un instante cualquiera del 14 al 25 (cada 30 s), ¿el rival toma un objetivo en los 90 s siguientes?
    fin = min(25 * 60000, m["gameDuration"] * 1000 - VENTANA_OBJ)
    g["base"] = [any(0 < o["timestamp"] - t <= VENTANA_OBJ for o in perdidos) for t in range(14 * 60000, fin, 30000)]
    games.append(g)
assert games and deaths, "sin timelines"

ok = [g for g in games if g["gd14"] >= 0]
W, L = [g for g in ok if g["win"]], [g for g in ok if not g["win"]]
avg = lambda rs, k: st.mean([r[k] for r in rs if r[k] is not None] or [0])
print(f"# Mid game: partidas con oro >= 0 contra tu rival al 14 ({len(ok)} de {len(games)})\n")
print(f"WR de este grupo: {wr(ok)}. Intervalos Wilson 95%. Pick-off = moriste sin otra muerte (de nadie) "
      f"a menos de 15 s y 3000 unidades. Objetivo perdido = el rival tomó dragón/heraldo/barón/torre en los 90 s siguientes.\n")

print("## Victorias contra derrotas (línea ganada al 14)\n\n| | Victorias | Derrotas |\n|---|---|---|")
print(f"| Partidas | {len(W)} | {len(L)} |")
for lbl, k, f in [("Tu oro vs rival @14", "gd14", "+.0f"), ("Oro del equipo @14", "tg14", "+.0f"),
                  ("Oro del equipo @20", "tg20", "+.0f"), ("Muertes 14–25", "d1425", ".2f"),
                  ("…de ellas pick-offs", "pick", ".2f"), ("…entregando shutdown", "shut", ".2f"),
                  ("…seguidas de objetivo perdido", "obj", ".2f")]:
    print(f"| {lbl} | {avg(W, k):{f}} | {avg(L, k):{f}} |")

print("\n## WR (línea ganada al 14) según lo que pasa después\n\n| Condición | WR (IC 95%) |\n|---|---|")
for lbl, cond in [("Equipo con oro >= 0 al 14", lambda g: g["tg14"] >= 0),
                  ("Equipo con oro < 0 al 14", lambda g: g["tg14"] < 0),
                  ("0 muertes del 14 al 25", lambda g: g["d1425"] == 0),
                  ("1–2 muertes del 14 al 25", lambda g: 1 <= g["d1425"] <= 2),
                  ("3+ muertes del 14 al 25", lambda g: g["d1425"] >= 3),
                  ("Sin pick-offs del 14 al 25", lambda g: g["pick"] == 0),
                  ("1+ pick-off del 14 al 25", lambda g: g["pick"] >= 1),
                  ("Entregaste 1+ shutdown del 14 al 25", lambda g: g["shut"] >= 1)]:
    print(f"| {lbl} | {wr([g for g in ok if cond(g)])} |")

# causalidad: si las muertes solo fueran consecuencia de que el equipo va abajo, con el equipo >= 0 no separarían
print("\n### Muertes del 14 al 25 según el oro del equipo al 14\n\n| Muertes 14–25 | Equipo >= 0 al 14 | Equipo < 0 al 14 |\n|---|---|---|")
for lbl, cond in [("0–2", lambda g: g["d1425"] <= 2), ("3+", lambda g: g["d1425"] >= 3)]:
    print(f"| {lbl} | {wr([g for g in ok if cond(g) and g['tg14'] >= 0])} | {wr([g for g in ok if cond(g) and g['tg14'] < 0])} |")

dl = [d for d in deaths if d["lane_ok"]]
print(f"\n## Las {len(dl)} muertes del 14 al 25 en esas partidas\n\n"
      "| | En victorias | En derrotas |\n|---|---|---|")
for lbl, f in [("Pick-off", lambda d: d["pick"]), ("Contra 3+ enemigos", lambda d: d["n"] >= 3),
               ("Contra 1 enemigo", lambda d: d["n"] == 1), ("Entregando shutdown", lambda d: d["shut"]),
               ("Seguida de objetivo perdido", lambda d: d["obj"])]:
    cols = []
    for w in (True, False):
        ds = [d for d in dl if d["win"] == w]; k = sum(map(f, ds))
        cols.append(f"{k}/{len(ds)} ({k / max(1, len(ds)):.0%})")
    print(f"| {lbl} | {' | '.join(cols)} |")
bw, bl = ([b for g in grp for b in g["base"]] for grp in (W, L))
print(f"| *Línea base: objetivo perdido en 90 s desde un instante cualquiera* | {sum(bw)/len(bw):.0%} | {sum(bl)/len(bl):.0%} |")

print("\n### Por zona\n\n| Zona | Muertes | En derrotas | Pick-off | Objetivo perdido después |\n|---|---|---|---|---|")
for z, n in Counter(d["zona"] for d in dl).most_common(8):
    ds = [d for d in dl if d["zona"] == z]
    print(f"| {z} | {n} | {sum(not d['win'] for d in ds)} | {sum(d['pick'] for d in ds) / n:.0%} | "
          f"{sum(d['obj'] for d in ds) / n:.0%} |")
