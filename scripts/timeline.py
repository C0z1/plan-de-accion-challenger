"""Análisis con timeline + challenges: diferencias a 10/14/20, muertes (fase, zona, quién), objetivos.
Uso: python scripts/timeline.py > datos/analisis-timeline-AAAA-MM-DD.md"""
import json, os, math, pathlib, statistics as st, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")  # Windows usa cp1252 y no tiene ≤ ni –
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


def wr(rs):
    if not rs: return "-"
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k / len(rs):.0%} ({lo:.0%}–{hi:.0%})"


def zone(x, y, team):
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"


games, deaths = [], []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes (los JSON no traen gameEndedInEarlySurrender)
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    ejg = {p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] != me["teamId"]}
    t = json.loads(tf.read_text())["info"]
    fr = t["frames"]; pid = me["participantId"]
    g = dict(win=me["win"], champ=me["championName"], pos=me["teamPosition"] or "?", t=m["gameCreation"],
             c=me.get("challenges", {}), d14=0, team=me["teamId"])
    for mn in (10, 14, 20):
        if opp and len(fr) > mn:
            a, b = fr[mn]["participantFrames"][str(pid)], fr[mn]["participantFrames"][str(opp["participantId"])]
            cs = lambda f: f["minionsKilled"] + f["jungleMinionsKilled"]
            g[f"gd{mn}"], g[f"xd{mn}"], g[f"cd{mn}"] = a["totalGold"] - b["totalGold"], a["xp"] - b["xp"], cs(a) - cs(b)
    kills = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL"]
    g["fb_victim"] = bool(kills) and kills[0]["victimId"] == pid
    for e in kills:
        if e["victimId"] != pid: continue
        mn = e["timestamp"] / 60000
        who = {e["killerId"], *e.get("assistingParticipantIds", [])} - {0}
        if mn < 14: g["d14"] += 1
        deaths.append(dict(win=g["win"], champ=g["champ"], pos=g["pos"], mn=mn, n=len(who), jg=bool(who & ejg),
                           zone=zone(e["position"]["x"], e["position"]["y"], g["team"])))
    games.append(g)
games.sort(key=lambda g: g["t"])
assert games and deaths, "sin timelines"

W = [g for g in games if g["win"]]; L = [g for g in games if not g["win"]]
avg = lambda rs, k: st.mean([r[k] for r in rs if r.get(k) is not None] or [0])
print(f"# Análisis con timeline: {len(games)} partidas, {len(deaths)} muertes\n")
print("Intervalos: Wilson 95%. Con menos de ~20 partidas el intervalo es muy ancho: tómalo como pista, no como regla.\n")

print("## Diferencia contra el rival de línea\n\n| | Oro @10 | Oro @14 | Oro @20 | XP @14 | CS @14 |\n|---|---|---|---|---|---|")
for name, rs in [("Total", games), ("Victorias", W), ("Derrotas", L), ("Últimas 50", games[-50:])]:
    print(f"| {name} | {avg(rs,'gd10'):+.0f} | {avg(rs,'gd14'):+.0f} | {avg(rs,'gd20'):+.0f} | {avg(rs,'xd14'):+.0f} | {avg(rs,'cd14'):+.1f} |")

print("\n## WR según oro contra el rival a los 14 min\n\n| Oro @14 | Partidas | WR (IC 95%) |\n|---|---|---|")
for lbl, lo, hi in [("≤ −1000", -1e9, -1000), ("−1000 a 0", -1000, 0), ("0 a +1000", 0, 1000), ("≥ +1000", 1000, 1e9)]:
    rs = [g for g in games if g.get("gd14") is not None and lo <= g["gd14"] < hi]
    print(f"| {lbl} | {len(rs)} | {wr(rs)} |")

print("\n## WR según muertes antes del min 14\n\n| Muertes <14 | Partidas | WR (IC 95%) |\n|---|---|---|")
for k in (0, 1, 2, 3, 4):
    rs = [g for g in games if (g["d14"] == k if k < 4 else g["d14"] >= 4)]
    print(f"| {k if k < 4 else '4+'} | {len(rs)} | {wr(rs)} |")
print(f"\nPromedio de muertes antes del 14: {avg(W,'d14'):.2f} en victorias, {avg(L,'d14'):.2f} en derrotas.")
fb = [g for g in games if g["fb_victim"]]
print(f"\nFuiste la víctima del first blood en {len(fb)}/{len(games)} partidas ({len(fb)/len(games):.0%}); WR en esas: {wr(fb)}.")

print("\n## Muertes por fase\n\n| Fase | Muertes | Por partida | En victorias | En derrotas |\n|---|---|---|---|---|")
for lbl, lo, hi in [("0–14 min", 0, 14), ("14–25 min", 14, 25), ("25+ min", 25, 999)]:
    ds = [d for d in deaths if lo <= d["mn"] < hi]
    print(f"| {lbl} | {len(ds)} | {len(ds)/len(games):.2f} | {sum(d['win'] for d in ds)/len(W):.2f} | "
          f"{sum(not d['win'] for d in ds)/len(L):.2f} |")

print("\n## Muertes por zona del mapa\n\n| Zona | Muertes | % | Antes del 14 | Con el jungla rival |\n|---|---|---|---|---|")
for z, n in Counter(d["zone"] for d in deaths).most_common():
    ds = [d for d in deaths if d["zone"] == z]
    print(f"| {z} | {n} | {n/len(deaths):.0%} | {sum(d['mn'] < 14 for d in ds)} | {sum(d['jg'] for d in ds)/n:.0%} |")

print("\n## ¿Quién te mata? (enemigos involucrados)\n\n| Enemigos | Muertes | % | Antes del 14 |\n|---|---|---|---|")
for k in (1, 2, 3):
    ds = [d for d in deaths if (d["n"] == k if k < 3 else d["n"] >= 3)]
    print(f"| {k if k < 3 else '3+'} | {len(ds)} | {len(ds)/len(deaths):.0%} | {sum(d['mn'] < 14 for d in ds)} |")
e14 = [d for d in deaths if d["mn"] < 14]
print(f"\nMuertes antes del 14 con el jungla rival involucrado: {sum(d['jg'] for d in e14)}/{len(e14)} "
      f"({sum(d['jg'] for d in e14)/max(1,len(e14)):.0%}).")
mid14 = [d for d in e14 if d["pos"] == "MIDDLE"]
far = [d for d in mid14 if not d["zone"].startswith("mid") and d["zone"] != "base propia"]
print(f"Jugando mid, muertes antes del 14 fuera de la línea de mid: {len(far)}/{len(mid14)} "
      f"({Counter(d['zone'] for d in far).most_common(3)}).")

print("\n## Por campeón (8+ partidas)\n\n| Campeón | Partidas | WR (IC 95%) | Oro @14 | Oro @14 en V | Oro @14 en D | Muertes <14 | Muertes totales |\n|---|---|---|---|---|---|---|---|")
by = defaultdict(list)
for g in games: by[g["champ"]].append(g)
dpg = Counter(d["champ"] for d in deaths)
for ch, rs in sorted(by.items(), key=lambda x: -len(x[1])):
    if len(rs) < 8: continue
    print(f"| {ch} | {len(rs)} | {wr(rs)} | {avg(rs,'gd14'):+.0f} | {avg([r for r in rs if r['win']],'gd14'):+.0f} | "
          f"{avg([r for r in rs if not r['win']],'gd14'):+.0f} | {avg(rs,'d14'):.2f} | {dpg[ch]/len(rs):.1f} |")

# challenges: qué separa victorias de derrotas (diferencia estandarizada), y cómo vas en las últimas 50
keys = sorted({k for g in games for k, v in g["c"].items() if isinstance(v, (int, float)) and not isinstance(v, bool)})
eff = []
for k in keys:
    vw = [g["c"][k] for g in W if k in g["c"]]; vl = [g["c"][k] for g in L if k in g["c"]]
    if len(vw) < 30 or len(vl) < 30: continue
    sd = st.pstdev(vw + vl)
    if sd: eff.append(((st.mean(vw) - st.mean(vl)) / sd, k, st.mean(vw), st.mean(vl),
                       st.mean([g["c"].get(k, 0) for g in games[-50:]]), st.mean(vw + vl)))
EARLY = ("laneMinionsFirst10Minutes", "maxCsAdvantageOnLaneOpponent", "maxLevelLeadLaneOpponent", "takedownsFirstXMinutes",
         "earlyLaningPhaseGoldExpAdvantage", "laningPhaseGoldExpAdvantage", "soloKills", "killsUnderOwnTurret",
         "controlWardsPlaced", "skillshotsDodged", "visionScorePerMinute", "killParticipation", "turretPlatesTaken",
         "wardTakedownsBefore20M", "enemyJungleMonsterKills", "survivedSingleDigitHpCount", "outnumberedKills")
print("\n## Challenges: lo que más separa victorias de derrotas\n\n"
      "Efecto = (media en V − media en D) / desviación. Excluye métricas que son consecuencia directa de ganar (torres, oro total, etc. aparecen igual: léelas con criterio).\n\n"
      "| Métrica | Efecto | Victorias | Derrotas | Temporada | Últimas 50 |\n|---|---|---|---|---|---|")
for e, k, a, b, l50, s in sorted(eff, key=lambda x: -abs(x[0]))[:20]:
    print(f"| {k} | {e:+.2f} | {a:.2f} | {b:.2f} | {s:.2f} | {l50:.2f} |")
print("\n### Métricas de early game y hábitos\n\n| Métrica | Efecto | Victorias | Derrotas | Temporada | Últimas 50 |\n|---|---|---|---|---|---|")
for e, k, a, b, l50, s in eff:
    if k in EARLY: print(f"| {k} | {e:+.2f} | {a:.2f} | {b:.2f} | {s:.2f} | {l50:.2f} |")
