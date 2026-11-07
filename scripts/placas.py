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
    games.append(dict(win=me["win"], champ=me["championName"], rol=me["teamPosition"],
                      gd14=pf(14, pid, "totalGold") - pf(14, oid, "totalGold"),
                      mias14=t14[0], eq14=t14[1], perd14=t14[2], mias=tfin[0], eq=tfin[1], perd=tfin[2]))
assert games, "sin timelines con placas"

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

print("\n## Por campeón (8+)\n\n| Campeón | Partidas | WR | Placas tuyas <14 (V) | (D) | Perdidas <14 (V) | (D) | WR con 1+ tuya <14 | WR con 0 |\n|---|---|---|---|---|---|---|---|---|")
for c, n in Counter(g["champ"] for g in games).most_common():
    if n < 8: break
    rs = [g for g in games if g["champ"] == c]; v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    print(f"| {c} | {n} | {wr(rs)} | {avg(v, lambda g: g['mias14']):.2f} | {avg(d, lambda g: g['mias14']):.2f} | "
          f"{avg(v, lambda g: g['perd14']):.2f} | {avg(d, lambda g: g['perd14']):.2f} | "
          f"{wr([g for g in rs if g['mias14']])} | {wr([g for g in rs if not g['mias14']])} |")
