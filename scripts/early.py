"""¿Qué separa victorias de derrotas en el early, por campeón? Solo métricas del early (challenges de los
primeros 10–14 min y timeline al 14). Por campeón (12+ partidas): media en V y en D, diferencia estandarizada,
p de permutación dentro del campeón y q de Benjamini-Hochberg (son muchas pruebas). Para la mejor métrica de cada
campeón, WR partiendo por la mediana con Wilson.
Uso: python scripts/early.py > datos/analisis-early-AAAA-MM-DD.md"""
import json, math, pathlib, random, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


def wr(rs):
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k}/{len(rs)} = {k / len(rs):.0%} ({lo:.0%}–{hi:.0%})" if rs else "-"


# Challenges que miden solo el early (se excluyen máximos de toda la partida como maxLevelLeadLaneOpponent).
CH = [("laneMinionsFirst10Minutes", "Minions de línea @10"), ("earlyLaningPhaseGoldExpAdvantage", "Ventaja oro+XP early (ch)"),
      ("laningPhaseGoldExpAdvantage", "Ventaja oro+XP fase de líneas (ch)"), ("takedownsFirstXMinutes", "Takedowns primeros min (ch)"),
      ("landSkillShotsEarlyGame", "Skillshots acertados early"), ("takedownsBeforeJungleMinionSpawn", "Takedowns antes de la jungla"),
      ("quickSoloKills", "Solo kills rápidos (ch)"), ("killsOnOtherLanesEarlyJungleAsLaner", "Kills en otras líneas early"),
      ("outerTurretExecutesBefore10Minutes", "Torre exterior <10 (ch)")]
TL = [("gd14", "Oro vs rival @14"), ("cs14", "CS vs rival @14"), ("xp14", "XP vs rival @14"), ("lv6", "Nivel vs rival @6"),
      ("d14", "Muertes <14"), ("dj14", "Muertes <14 con jungla rival"), ("k14", "Kills <14"), ("solo14", "Solo kills <14"),
      ("kp14", "Kills de tu equipo <14 con tu participación")]
MET = CH + TL

games = []
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 900: continue  # remakes y partidas sin minuto 14
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    fr = json.loads(tf.read_text())["info"]["frames"]
    if not opp or len(fr) <= 14 or me["teamPosition"] == "JUNGLE": continue
    pid, oid, team = me["participantId"], opp["participantId"], me["teamId"]
    ejg = next((p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] != team), None)
    mios = {p["participantId"] for p in ps if p["teamId"] == team}
    pf = lambda mn, i: fr[mn]["participantFrames"][str(i)]
    dif = lambda mn, f: f(pf(mn, pid)) - f(pf(mn, oid))
    ev = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL" and e["timestamp"] < 14 * 60000]
    mias = [e for e in ev if e["victimId"] == pid]
    hechas = [e for e in ev if e.get("killerId") in mios]
    ch = me["challenges"]
    g = dict(win=me["win"], champ=me["championName"], rol=me["teamPosition"],
             gd14=dif(14, lambda p: p["totalGold"]), cs14=dif(14, lambda p: p["minionsKilled"] + p["jungleMinionsKilled"]),
             xp14=dif(14, lambda p: p["xp"]), lv6=dif(6, lambda p: p["level"]),
             d14=len(mias), dj14=sum(ejg in [e.get("killerId")] + e.get("assistingParticipantIds", []) for e in mias),
             k14=sum(e["killerId"] == pid for e in ev),
             solo14=sum(e["killerId"] == pid and not e.get("assistingParticipantIds") for e in ev),
             kp14=sum(pid == e["killerId"] or pid in e.get("assistingParticipantIds", []) for e in hechas) / max(1, len(hechas)))
    for k, _ in CH: g[k] = ch.get(k, 0)
    games.append(g)
assert games, "sin timelines"
assert all(g["solo14"] <= g["k14"] and g["dj14"] <= g["d14"] and 0 <= g["kp14"] <= 1 for g in games)


def efecto(rs, k):  # diferencia de medias V−D en desviaciones estándar
    v = [r[k] for r in rs if r["win"]]; d = [r[k] for r in rs if not r["win"]]
    if len(v) < 2 or len(d) < 2: return 0.0, 0, 0
    s = st.pstdev([r[k] for r in rs])
    return ((st.mean(v) - st.mean(d)) / s if s else 0.0), st.mean(v), st.mean(d)


def perm(rs, k, n=2000, rnd=random.Random(1)):
    obs = abs(efecto(rs, k)[0]); ws = [r["win"] for r in rs]; xs = [{k: r[k]} for r in rs]; hit = 0
    for _ in range(n):
        rnd.shuffle(ws)
        hit += abs(efecto([dict(x, win=w) for x, w in zip(xs, ws)], k)[0]) >= obs - 1e-12
    return (hit + 1) / (n + 1)


def bh(ps):  # q de Benjamini-Hochberg
    o = sorted(range(len(ps)), key=lambda i: ps[i]); q = [0.0] * len(ps); m = 1.0
    for r, i in reversed(list(enumerate(o, 1))):
        m = min(m, ps[i] * len(ps) / r); q[i] = m
    return q
assert [round(x, 3) for x in bh([0.01, 0.04, 0.03])] == [0.03, 0.04, 0.04]

print(f"# Early por campeón: qué separa V de D ({len(games)} partidas de 15+ min con timeline, sin jungla)\n")
print("Solo métricas del early. *d* = (media V − media D) / desviación del campeón. p = permutación de V/D dentro del "
      "campeón (2000, semilla 1). q = Benjamini-Hochberg sobre todas las pruebas de la tabla del campeón: "
      "q < 0.10 es lo único que se lee como señal; lo demás es ruido posible.\n")
champs = [c for c, n in Counter(g["champ"] for g in games).most_common() if n >= 12]
grupos = [(c, [g for g in games if g["champ"] == c]) for c in champs] + [("Todos", games)]
resumen = []
for c, rs in grupos:
    filas = [(lab, k, *efecto(rs, k), perm(rs, k)) for k, lab in MET]
    qs = bh([f[5] for f in filas])
    print(f"## {c}: {wr(rs)}\n\n| Métrica | V | D | d | p | q |\n|---|---|---|---|---|---|")
    for (lab, k, d, mv, md, p), q in sorted(zip(filas, qs), key=lambda t: -abs(t[0][2])):
        print(f"| {lab} | {mv:.2f} | {md:.2f} | {d:+.2f} | {p:.3f} | {q:.2f}{' ✅' if q < 0.10 else ''} |")
    (lab, k, d, *_), q = max(zip(filas, qs), key=lambda t: abs(t[0][2]))
    med = st.median(r[k] for r in rs)
    alto = [r for r in rs if r[k] > med]; bajo = [r for r in rs if r[k] <= med]
    print(f"\nMejor métrica: **{lab}**. > {med:g}: {wr(alto)}; ≤ {med:g}: {wr(bajo)}.\n")
    # Control: ¿es solo reflejo del oro @14 o del rol? Mismo corte dentro de cada tercio de oro y solo en mid.
    if k != "gd14":
        por_oro = sorted(rs, key=lambda r: r["gd14"]); n = len(por_oro)
        print(f"Control (mismo corte {med:g}):\n\n| Grupo | > | ≤ |\n|---|---|---|")
        for t in range(3):
            b = por_oro[t * n // 3:(t + 1) * n // 3]
            print(f"| Oro @14 {b[0]['gd14']:+.0f} a {b[-1]['gd14']:+.0f} | {wr([r for r in b if r[k] > med])} | {wr([r for r in b if r[k] <= med])} |")
        mid = [r for r in rs if r["rol"] == "MIDDLE"]
        print(f"| Solo mid | {wr([r for r in mid if r[k] > med])} | {wr([r for r in mid if r[k] <= med])} |\n")
    resumen.append((c, len(rs), lab, d, q, sum(x < 0.10 for x in qs)))

print("## Resumen\n\n| Campeón | n | Lo que más separa | d | q | Métricas con q < 0.10 |\n|---|---|---|---|---|---|")
for c, n, lab, d, q, s in resumen:
    print(f"| {c} | {n} | {lab} | {d:+.2f} | {q:.2f} | {s} de {len(MET)} |")
