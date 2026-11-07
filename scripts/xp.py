"""¿De dónde sale la XP que pierdes contra tu rival de línea antes del 14? Reparte la diferencia de XP de cada
minuto (2 a 14) según dónde estabas tú (muerto, en base, fuera de tu línea, en tu línea) y dónde tu rival.
Las posiciones del timeline son una foto por minuto: es una aproximación, no un rastreo continuo.
Uso: python scripts/xp.py > datos/analisis-xp-AAAA-MM-DD.md"""
import json, math, pathlib, statistics as st, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE": "mid", "TOP": "top", "BOTTOM": "bot", "UTILITY": "bot"}
ESTADOS = ["muerto", "muere él", "base", "fuera", "línea"]


def wilson(k, n, z=1.96):  # misma función que scripts/linea.py
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
assert zone(7400, 7400, 100) == "mid (lado rival)" and zone(1000, 1000, 100) == "base propia"


def estado(fr, mn, i, team, linea, muertes):
    """Estado del jugador i en el minuto (mn-1, mn]: muerto si murió en ese minuto, base si la foto de mn-1 o mn
    está en su base (regreso), fuera si la foto de mn no está en su línea, si no línea."""
    if any((mn - 1) * 60000 < t <= mn * 60000 for t in muertes): return "muerto"
    zs = [zone(fr[k]["participantFrames"][str(i)]["position"]["x"], fr[k]["participantFrames"][str(i)]["position"]["y"], team)
          for k in (mn - 1, mn)]
    if "base propia" in zs: return "base"
    return "línea" if zs[1].startswith(linea) else "fuera"
_f = lambda x, y: {"participantFrames": {"1": {"position": {"x": x, "y": y}}}}
assert estado([_f(7000, 7000), _f(7200, 7300)], 1, 1, 100, "mid", []) == "línea"
assert estado([_f(7000, 7000), _f(500, 500)], 1, 1, 100, "mid", []) == "base"
assert estado([_f(7000, 7000), _f(4000, 9000)], 1, 1, 100, "mid", [30000]) == "muerto"
assert estado([_f(7000, 7000), _f(1000, 9000)], 1, 1, 100, "mid", []) == "fuera"

games = []
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] not in LINEA: continue  # sin jungla
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    fr = json.loads(tf.read_text())["info"]["frames"]
    if not opp or len(fr) <= 20 or m["gameDuration"] < 1200: continue  # 20+ min reales (sin 19:xx)
    pid, oid = me["participantId"], opp["participantId"]
    linea = LINEA[me["teamPosition"]]
    xp = lambda mn, i: fr[mn]["participantFrames"][str(i)]["xp"]
    kills = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL"]
    muere = lambda i: [e["timestamp"] for e in kills if e["victimId"] == i]
    # La diferencia de XP de cada minuto se reparte según tu estado y según el de tu rival.
    yo, el, mins = defaultdict(float), defaultdict(float), Counter()
    for mn in range(2, 15):
        d = (xp(mn, pid) - xp(mn - 1, pid)) - (xp(mn, oid) - xp(mn - 1, oid))
        a = estado(fr, mn, pid, me["teamId"], linea, muere(pid))
        b = estado(fr, mn, oid, opp["teamId"], linea, muere(oid))
        if b == "muerto" and a != "muerto": a = "muere él"  # separa la XP de matar a tu rival de la del farm
        yo[a] += d; el[b] += d; mins[a] += 1; mins["r" + b] += 1
    games.append(dict(win=me["win"], champ=me["championName"], gd14=fr[14]["participantFrames"][str(pid)]["totalGold"] - fr[14]["participantFrames"][str(oid)]["totalGold"],
                      xp14=xp(14, pid) - xp(14, oid), xp1=xp(1, pid) - xp(1, oid), mi14=xp(14, pid), su14=xp(14, oid),
                      yo=yo, el=el, mins=mins))
assert games, "sin timelines"
# La suma por estado más la diferencia del minuto 1 reconstruye la diferencia al 14.
assert all(abs(sum(g["yo"].values()) + g["xp1"] - g["xp14"]) < 1e-6 for g in games)

perd, gan = [g for g in games if g["gd14"] < 0], [g for g in games if g["gd14"] >= 0]
W, L = [g for g in perd if g["win"]], [g for g in perd if not g["win"]]
avg = lambda rs, f: st.mean([f(r) for r in rs]) if rs else float("nan")

print(f"# ¿De dónde sale la XP perdida antes del 14? ({len(perd)} líneas perdidas de {len(games)} partidas, 20+ min, sin jungla)\n")
print("Cada minuto del 2 al 14 se etiqueta por tu estado: **muerto** (moriste en ese minuto), **base** (la foto del minuto "
      "anterior o de este te pone en tu base: regreso), **fuera** (la foto no está en tu línea: roam, jungla, río) o "
      "**línea**; si no moriste pero murió tu rival de línea, el minuto va a **muere él** (la XP de matarlo). Las fotos son una por minuto: es una aproximación. XP = tú menos tu rival de línea; "
      "\"XP del minuto\" = lo que ganaste tú menos lo que ganó él en ese minuto. Intervalos Wilson 95%.\n")

print("## XP absoluta al 14: ¿la pierdes tú o la gana él?\n\n| | Partidas | Tu XP @14 | XP del rival @14 | Diferencia |\n|---|---|---|---|---|")
for lbl, rs in [("Línea ganada (oro ≥ 0)", gan), ("Línea perdida: victorias", W), ("Línea perdida: derrotas", L)]:
    print(f"| {lbl} | {len(rs)} | {avg(rs, lambda g: g['mi14']):.0f} | {avg(rs, lambda g: g['su14']):.0f} | {avg(rs, lambda g: g['xp14']):+.0f} |")

print("\n## Línea perdida: XP perdida según TU estado (suma por partida, minutos 2–14)\n")
print("| Tu estado | Minutos por partida (V) | Minutos (D) | XP del minuto (V) | XP del minuto (D) | XP por minuto en ese estado (V) | (D) |\n|---|---|---|---|---|---|---|")
for s in ESTADOS:
    mv, md = avg(W, lambda g: g["mins"][s]), avg(L, lambda g: g["mins"][s])
    xv, xd = avg(W, lambda g: g["yo"][s]), avg(L, lambda g: g["yo"][s])
    print(f"| {s} | {mv:.1f} | {md:.1f} | {xv:+.0f} | {xd:+.0f} | {xv / mv if mv else 0:+.0f} | {xd / md if md else 0:+.0f} |")
print(f"| minuto 1 (antes de la línea) | | | {avg(W, lambda g: g['xp1']):+.0f} | {avg(L, lambda g: g['xp1']):+.0f} | | |")
print(f"| **Total @14** | | | {avg(W, lambda g: g['xp14']):+.0f} | {avg(L, lambda g: g['xp14']):+.0f} | | |")

print("\n## Línea perdida: XP según el estado de TU RIVAL\n")
print("| Estado del rival | Minutos (V) | Minutos (D) | XP del minuto (V) | XP del minuto (D) |\n|---|---|---|---|---|")
for s in ESTADOS:
    if s == "muere él": continue
    print(f"| {s} | {avg(W, lambda g: g['mins']['r' + s]):.1f} | {avg(L, lambda g: g['mins']['r' + s]):.1f} | "
          f"{avg(W, lambda g: g['el'][s]):+.0f} | {avg(L, lambda g: g['el'][s]):+.0f} |")

# ¿Qué palanca pesa en el WR? Minutos fuera de la línea y en base, partido por la mediana.
print("\n## WR con la línea perdida según tus minutos fuera de la línea (2–14)\n\n| Condición | Línea perdida | Todas |\n|---|---|---|")
for lbl, c in [("0–1 minutos muerto", lambda g: g["mins"]["muerto"] <= 1), ("2+ minutos muerto", lambda g: g["mins"]["muerto"] >= 2),
               ("0–2 minutos en base", lambda g: g["mins"]["base"] <= 2), ("3+ minutos en base", lambda g: g["mins"]["base"] >= 3),
               ("0–1 minutos fuera", lambda g: g["mins"]["fuera"] <= 1), ("2+ minutos fuera", lambda g: g["mins"]["fuera"] >= 2),
               ("10+ minutos en tu línea", lambda g: g["mins"]["línea"] >= 10), ("< 10 en tu línea", lambda g: g["mins"]["línea"] < 10)]:
    print(f"| {lbl} | {wr([g for g in perd if c(g)])} | {wr([g for g in games if c(g)])} |")

top = [c for c, n in Counter(g["champ"] for g in perd).most_common() if n >= 8]
print("\n## Por campeón, con la línea perdida (8+ partidas): XP del minuto según tu estado\n")
print("| Campeón | Partidas | WR | XP @14 | " + " | ".join(ESTADOS) + " | Minutos fuera + base |\n|---|---|---|---|" + "---|" * (len(ESTADOS) + 1))
for c in top:
    rs = [g for g in perd if g["champ"] == c]
    print(f"| {c} | {len(rs)} | {wr(rs)} | {avg(rs, lambda g: g['xp14']):+.0f} | "
          + " | ".join(f"{avg(rs, lambda g: g['yo'][s]):+.0f}" for s in ESTADOS)
          + f" | {avg(rs, lambda g: g['mins']['fuera'] + g['mins']['base']):.1f} |")
