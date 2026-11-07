"""Placas reales desde el timeline (TURRET_PLATE_DESTROYED, sugerencia de DeepSeek) contra WR.
En este parche las placas siguen cayendo después del 14 y hay hasta 15 por línea y equipo (3 torres × 5);
killerId 0 = súbditos; teamId = dueño de la torre. Como las placas dan oro, se controla a igual oro al 14.
Uso: python scripts/placas.py > datos/analisis-placas-AAAA-MM-DD.md"""
import json, math, pathlib, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LANE = {"MIDDLE": "MID_LANE", "TOP": "TOP_LANE", "BOTTOM": "BOT_LANE", "UTILITY": "BOT_LANE"}


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


def placas(ev, lane, team, pid, hasta):
    """(tuyas, de tu equipo con súbditos, perdidas) en tu línea hasta `hasta` ms."""
    ps = [e for e in ev if e["laneType"] == lane and e["timestamp"] <= hasta]
    rival = [e for e in ps if e["teamId"] != team]
    return (sum(e["killerId"] == pid for e in rival), len(rival), sum(e["teamId"] == team for e in ps))
_ev = [{"laneType": "MID_LANE", "teamId": 200, "killerId": 3, "timestamp": 5}, {"laneType": "MID_LANE", "teamId": 200, "killerId": 0, "timestamp": 6},
       {"laneType": "MID_LANE", "teamId": 100, "killerId": 8, "timestamp": 7}, {"laneType": "TOP_LANE", "teamId": 200, "killerId": 3, "timestamp": 8},
       {"laneType": "MID_LANE", "teamId": 200, "killerId": 3, "timestamp": 99}]
assert placas(_ev, "MID_LANE", 100, 3, 50) == (1, 2, 1)

# Tiempo de reaparición base por nivel (antes del 15 no hay recargo por minuto) + ~20 s de caminar a la línea.
# shortcut: tabla fija del parche actual y caminata fija, ajustar si Riot cambia los tiempos.
RESPAWN = [10, 10, 12, 12, 14, 16, 20, 25, 28, 32.5, 35, 37.5, 40, 42.5, 45, 47.5, 50, 52.5]
CAMINAR = 20


def ausente(t, muertes):
    """¿La placa que cayó en t (ms) cayó mientras estabas muerto o volviendo a la línea? muertes = [(t, nivel)]."""
    return any(tm <= t <= tm + (RESPAWN[nv - 1] + CAMINAR) * 1000 for tm, nv in muertes)
assert ausente(70000, [(60000, 6)]) and not ausente(100000, [(60000, 6)]) and not ausente(50000, [(60000, 6)])

def zone(x, y, team):  # misma función que scripts/xp.py
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"
assert zone(7400, 7400, 100) == "mid (lado rival)" and zone(1000, 1000, 100) == "base propia"
LINEA = {"MIDDLE": "mid", "TOP": "top", "BOTTOM": "bot", "UTILITY": "bot"}

games, total_ev = [], Counter()
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 1200: continue  # 20+ min reales, igual que castigo.py
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] not in LANE: continue  # sin jungla
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    if not opp: continue
    fr = json.loads(tf.read_text())["info"]["frames"]
    ev = [e for f in fr for e in f["events"] if e["type"] == "TURRET_PLATE_DESTROYED"]
    total_ev[len(ev) > 0] += 1
    if not ev: continue  # timelines sin el evento: no se pueden contar
    pid, oid = me["participantId"], opp["participantId"]
    pf = lambda mn, i, k: fr[mn]["participantFrames"][str(i)][k]
    lane, team = LANE[me["teamPosition"]], me["teamId"]
    t14, tfin = placas(ev, lane, team, pid, 14 * 60000), placas(ev, lane, team, pid, 10 ** 9)
    muertes = [(e["timestamp"], pf(e["timestamp"] // 60000, pid, "level")) for f in fr for e in f["events"]
               if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid and e["timestamp"] <= 14 * 60000]
    perdidas = [e["timestamp"] for e in ev if e["laneType"] == lane and e["teamId"] == team and e["timestamp"] <= 14 * 60000]
    muerto14 = sum(ausente(t, muertes) for t in perdidas)
    # Vivo: ¿la foto más cercana (una por minuto) te pone en tu línea? Aproximación gruesa.
    pos = lambda t: fr[round(t / 60000)]["participantFrames"][str(pid)]["position"]
    enlinea14 = sum(not ausente(t, muertes) and zone(pos(t)["x"], pos(t)["y"], team).startswith(LINEA[me["teamPosition"]])
                    for t in perdidas)
    games.append(dict(win=me["win"], champ=me["championName"], rol=me["teamPosition"],
                      gd14=pf(14, pid, "totalGold") - pf(14, oid, "totalGold"), muerto14=muerto14, vivo14=len(perdidas) - muerto14,
                      enlinea14=enlinea14, fuera14=len(perdidas) - muerto14 - enlinea14,
                      mias14=t14[0], eq14=t14[1], perd14=t14[2], mias=tfin[0], eq=tfin[1], perd=tfin[2]))
assert games, "sin timelines con placas"
assert all(g["muerto14"] + g["vivo14"] == g["perd14"] for g in games)

avg = lambda rs, f: st.mean([f(r) for r in rs]) if rs else float("nan")
gan, perd = [g for g in games if g["gd14"] >= 0], [g for g in games if g["gd14"] < 0]
print(f"# Placas en tu línea ({len(games)} partidas de 20+ min sin jungla; {total_ev[False]} timelines sin eventos de placas, fuera)\n")
print("Desde `TURRET_PLATE_DESTROYED`. **Tuyas** = el último golpe fue tuyo; **del equipo** = cayeron en la torre rival "
      "de tu línea (tú, aliados o súbditos); **perdidas** = cayeron en tu torre de tu línea. En este parche hay placas "
      "después del 14 y en las 3 torres. Intervalos Wilson 95%.\n")

print("## Promedio por partida, V contra D\n\n| | Tuyas <14 | Del equipo <14 | Perdidas <14 | Tuyas (partida) | Perdidas (partida) |\n|---|---|---|---|---|---|")
for lbl, rs in [("Línea ganada, V", [g for g in gan if g["win"]]), ("Línea ganada, D", [g for g in gan if not g["win"]]),
                ("Línea perdida, V", [g for g in perd if g["win"]]), ("Línea perdida, D", [g for g in perd if not g["win"]])]:
    print(f"| {lbl} ({len(rs)}) | " + " | ".join(f"{avg(rs, lambda g: g[k]):.2f}" for k in ["mias14", "eq14", "perd14", "mias", "perd"]) + " |")

print("\n## WR según tus placas antes del 14\n\n| Placas tuyas <14 | Línea ganada | Línea perdida | Todas |\n|---|---|---|---|")
for lbl, c in [("0", lambda g: g["mias14"] == 0), ("1–2", lambda g: 1 <= g["mias14"] <= 2), ("3+", lambda g: g["mias14"] >= 3)]:
    print(f"| {lbl} | {wr([g for g in gan if c(g)])} | {wr([g for g in perd if c(g)])} | {wr([g for g in games if c(g)])} |")

print("\n## Neto de placas en tu línea antes del 14 (del equipo − perdidas)\n\n| Neto | Línea ganada | Línea perdida |\n|---|---|---|")
neto = lambda g: g["eq14"] - g["perd14"]
for lbl, c in [("≤ −2", lambda g: neto(g) <= -2), ("−1 a +1", lambda g: -1 <= neto(g) <= 1), ("≥ +2", lambda g: neto(g) >= 2)]:
    print(f"| {lbl} | {wr([g for g in gan if c(g)])} | {wr([g for g in perd if c(g)])} |")

# Control por oro: las placas son parte del oro; a igual oro, ¿siguen separando?
print("\n## A igual oro al 14 (las placas dan oro, así que se compara dentro de cada banda)\n\n| Oro vs rival al 14 | Partidas | 0 placas tuyas <14 | 1+ placas tuyas <14 | Media de placas V / D | Perdidas <14 V / D | 0–1 perdidas <14 | 3+ perdidas <14 |\n|---|---|---|---|---|---|---|---|")
for lo, hi in [(-1500, -500), (-500, 500), (500, 1500)]:
    rs = [g for g in games if lo <= g["gd14"] < hi]
    v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    print(f"| {lo:+} a {hi:+} | {len(rs)} | {wr([g for g in rs if not g['mias14']])} | {wr([g for g in rs if g['mias14']])} | "
          f"{avg(v, lambda g: g['mias14']):.2f} / {avg(d, lambda g: g['mias14']):.2f} | "
          f"{avg(v, lambda g: g['perd14']):.2f} / {avg(d, lambda g: g['perd14']):.2f} | "
          f"{wr([g for g in rs if g['perd14'] <= 1])} | {wr([g for g in rs if g['perd14'] >= 3])} |")

# ¿Causa o reflejo? Si solo separan las placas perdidas mientras estás muerto, es reflejo de las muertes.
print("\n## Placas perdidas <14: estando muerto o vivo (DeepSeek: ¿causa o reflejo?)\n\n"
      f"**Muerto** = cayó entre tu muerte y tu reaparición + {CAMINAR} s de caminar (reaparición por nivel); **vivo** = el resto "
      "(en línea, en base o fuera).\n\n| Oro vs rival al 14 | Partidas | Muerto V / D | Vivo V / D | 0 vivo | 1 vivo | 2+ vivo |\n|---|---|---|---|---|---|---|")
for lo, hi in [(-1500, -500), (-500, 500), (500, 1500), (-10 ** 9, 10 ** 9)]:
    rs = [g for g in games if lo <= g["gd14"] < hi]
    v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    print(f"| {'todas' if lo < -10 ** 6 else f'{lo:+} a {hi:+}'} | {len(rs)} | "
          f"{avg(v, lambda g: g['muerto14']):.2f} / {avg(d, lambda g: g['muerto14']):.2f} | "
          f"{avg(v, lambda g: g['vivo14']):.2f} / {avg(d, lambda g: g['vivo14']):.2f} | "
          f"{wr([g for g in rs if g['vivo14'] == 0])} | {wr([g for g in rs if g['vivo14'] == 1])} | {wr([g for g in rs if g['vivo14'] >= 2])} |")

print("\n### Vivo, separado: en tu línea contra fuera de ella (base, roam, jungla; foto del minuto más cercano)\n\n"
      "| Oro vs rival al 14 | En línea V / D | Fuera V / D | 0 fuera | 1+ fuera | 0 en línea | 1+ en línea |\n|---|---|---|---|---|---|---|")
for lo, hi in [(-1500, -500), (-500, 500), (500, 1500), (-10 ** 9, 10 ** 9)]:
    rs = [g for g in games if lo <= g["gd14"] < hi]
    v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    print(f"| {'todas' if lo < -10 ** 6 else f'{lo:+} a {hi:+}'} | "
          f"{avg(v, lambda g: g['enlinea14']):.2f} / {avg(d, lambda g: g['enlinea14']):.2f} | "
          f"{avg(v, lambda g: g['fuera14']):.2f} / {avg(d, lambda g: g['fuera14']):.2f} | "
          f"{wr([g for g in rs if not g['fuera14']])} | {wr([g for g in rs if g['fuera14']])} | "
          f"{wr([g for g in rs if not g['enlinea14']])} | {wr([g for g in rs if g['enlinea14']])} |")

print("\n## Por campeón (8+)\n\n| Campeón | Partidas | WR | Placas tuyas <14 (V) | (D) | Perdidas <14 (V) | (D) | WR con 1+ tuya <14 | WR con 0 |\n|---|---|---|---|---|---|---|---|---|")
for c, n in Counter(g["champ"] for g in games).most_common():
    if n < 8: break
    rs = [g for g in games if g["champ"] == c]; v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    print(f"| {c} | {n} | {wr(rs)} | {avg(v, lambda g: g['mias14']):.2f} | {avg(d, lambda g: g['mias14']):.2f} | "
          f"{avg(v, lambda g: g['perd14']):.2f} | {avg(d, lambda g: g['perd14']):.2f} | "
          f"{wr([g for g in rs if g['mias14']])} | {wr([g for g in rs if not g['mias14']])} |")
