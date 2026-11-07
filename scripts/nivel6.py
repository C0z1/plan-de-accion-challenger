"""Nivel contra tu rival de línea antes del 14: ¿cuánto mueres (y matas) según vayas un nivel abajo, igual o arriba,
y qué pasa en la carrera al nivel 2 y al 6? Sale de los eventos LEVEL_UP del timeline (exactos al ms).
Uso: python scripts/nivel6.py > datos/analisis-nivel-AAAA-MM-DD.md"""
import json, math, pathlib, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE", "TOP", "BOTTOM", "UTILITY"}
FIN = 14 * 60000
ESTADOS = ["2+ abajo", "1 abajo", "igual", "1 arriba", "2+ arriba"]


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


def estado(d):
    return ESTADOS[max(-2, min(2, d)) + 2]
assert estado(-3) == "2+ abajo" and estado(0) == "igual" and estado(1) == "1 arriba"


def nivel(ups, t):
    """Nivel en el instante t a partir de [(timestamp, nivel)] ordenada."""
    return max([lv for ts, lv in ups if ts <= t], default=1)
assert nivel([(60000, 2), (120000, 3)], 90000) == 2 and nivel([(60000, 2)], 0) == 1


def exposicion(mis, sus):
    """Minutos de 0 a 14 en cada estado de diferencia de nivel (tú − él)."""
    cortes = sorted({0, FIN, *[ts for ts, _ in mis + sus if ts < FIN]})
    out = Counter()
    for a, b in zip(cortes, cortes[1:]):
        out[estado(nivel(mis, a) - nivel(sus, a))] += (b - a) / 60000
    return out
_e = exposicion([(60000, 2)], [])
assert abs(sum(_e.values()) - 14) < 1e-9 and abs(_e["1 arriba"] - 13) < 1e-9

games = []
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 1200: continue  # mismo filtro que castigo.py / placas.py
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] not in LINEA: continue
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    if not opp: continue
    fr = json.loads(tf.read_text())["info"]["frames"]
    pid, oid = me["participantId"], opp["participantId"]
    ev = [e for f in fr for e in f["events"]]
    ups = lambda i: sorted((e["timestamp"], e["level"]) for e in ev if e["type"] == "LEVEL_UP" and e["participantId"] == i)
    mis, sus = ups(pid), ups(oid)
    kills = [e for e in ev if e["type"] == "CHAMPION_KILL" and e["timestamp"] <= FIN]
    dif = lambda t: nivel(mis, t) - nivel(sus, t)
    # 3 s antes del kill: al instante, el LEVEL_UP que da la XP del propio kill ya cuenta y fabrica un "1 abajo" falso
    muertes = [estado(dif(e["timestamp"] - 3000)) for e in kills if e["victimId"] == pid]
    muertes2 = [estado(dif(e["timestamp"])) for e in kills if e["victimId"] == pid]
    jr = next((p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] != me["teamId"]), None)
    con_jg = [estado(dif(e["timestamp"] - 3000)) for e in kills
              if e["victimId"] == pid and jr in {e["killerId"], *e.get("assistingParticipantIds", [])}]
    # kills tuyos (o con asistencia) sobre tu rival de línea
    mato = [estado(dif(e["timestamp"] - 3000)) for e in kills
            if e["victimId"] == oid and pid in {e["killerId"], *e.get("assistingParticipantIds", [])}]
    t_n = lambda ups_, lv: next((ts for ts, l in ups_ if l >= lv), None)
    pf14 = fr[14]["participantFrames"]
    games.append(dict(win=me["win"], champ=me["championName"], rol=me["teamPosition"], muertes=muertes, muertes2=muertes2, con_jg=con_jg, mato=mato,
                      exp=exposicion(mis, sus), t2=(t_n(mis, 2), t_n(sus, 2)), t6=(t_n(mis, 6), t_n(sus, 6)),
                      gd14=pf14[str(pid)]["totalGold"] - pf14[str(oid)]["totalGold"]))
assert games, "sin timelines"

print(f"# Nivel contra tu rival de línea antes del 14 ({len(games)} partidas, 20+ min, sin jungla)\n")
print("Diferencia de nivel = tu nivel − el de tu rival de línea en cada instante (eventos LEVEL_UP). "
      "Tasa = muertes por cada 10 minutos pasados en ese estado; el estado de cada kill se mide 3 s antes. Intervalos Wilson 95%.\n")

# shortcut: la exposición incluye el tiempo que estás muerto (tras morir sueles quedar abajo), así que la tasa "abajo" está algo subestimada; restar el tiempo muerto si se usa para decidir algo fino.
exp = Counter(); mu = Counter(); ma = Counter(); mj = Counter()
for g in games:
    exp.update(g["exp"]); mu.update(g["muertes"]); ma.update(g["mato"]); mj.update(g["con_jg"])
print("## Muertes y kills por diferencia de nivel (0–14 min, todas)\n\n| Estado | Minutos | % del tiempo | Tus muertes | Por 10 min | Con jungla rival | Sin jungla rival, por 10 min | Kills tuyos sobre él | Por 10 min |\n|---|---|---|---|---|---|---|---|---|")
tot = sum(exp.values())
for s in ESTADOS:
    if exp[s]: print(f"| {s} | {exp[s]:.0f} | {exp[s] / tot:.0%} | {mu[s]} | {10 * mu[s] / exp[s]:.2f} | {mj[s] / mu[s]:.0%} | "
                     f"{10 * (mu[s] - mj[s]) / exp[s]:.2f} | {ma[s]} | {10 * ma[s] / exp[s]:.2f} |")
# razón de tasas contra "igual" con IC Poisson aproximado (log); shortcut: ignora que las muertes se agrupan por partida
for s in ["1 abajo", "1 arriba"]:
    r = (mu[s] / exp[s]) / (mu["igual"] / exp["igual"]); se = math.sqrt(1 / mu[s] + 1 / mu["igual"])
    print(f"\n{s} contra igual: muertes ×{r:.2f} ({r * math.exp(-1.96 * se):.2f}–{r * math.exp(1.96 * se):.2f})", end="")
print()

mu2 = Counter(s for g in games for s in g["muertes2"])
print("\nChequeo: midiendo el nivel **en el instante** de tu muerte (incluye el nivel que le da tu kill al rival; por eso se usa 3 s antes): "
      + ", ".join(f"{s} {10 * mu2[s] / exp[s]:.2f}" for s in ESTADOS if exp[s]))

for lbl, rs in [("victorias", [g for g in games if g["win"]]), ("derrotas", [g for g in games if not g["win"]])]:
    e = Counter(); d = Counter()
    for g in rs: e.update(g["exp"]); d.update(g["muertes"])
    print(f"\n{lbl.capitalize()} — muertes por 10 min: " + ", ".join(f"{s} {10 * d[s] / e[s]:.2f}" for s in ESTADOS if e[s] > 20)
          + "; tiempo abajo (1+): " + f"{(e['1 abajo'] + e['2+ abajo']) / sum(e.values()):.0%}")

for lv, k in [(2, "t2"), (6, "t6")]:
    print(f"\n## Carrera al nivel {lv}\n\n| Quién llega primero | Partidas | WR | Oro al 14 (media) |\n|---|---|---|---|")
    ok = [g for g in games if None not in g[k]]
    for lbl, c in [("tú (por 1+ s)", lambda a, b: a < b), ("él", lambda a, b: a > b), ("empate", lambda a, b: a == b)]:
        rs = [g for g in ok if c(*g[k])]
        if rs: print(f"| {lbl} | {len(rs)} | {wr(rs)} | {sum(g['gd14'] for g in rs) / len(rs):+.0f} |")
    if lv == 6:
        for lbl, c in [("tú por 30+ s", lambda a, b: b - a >= 30000), ("él por 30+ s", lambda a, b: a - b >= 30000)]:
            rs = [g for g in ok if c(*g[k])]
            print(f"| {lbl} | {len(rs)} | {wr(rs)} | {sum(g['gd14'] for g in rs) / len(rs):+.0f} |")
        # a igual oro: ¿llegar primero al 6 suma algo aparte de ir arriba?
        print("\nA igual oro al 14 (bandas):\n\n| Oro al 14 | Tú primero al 6 | Él primero |\n|---|---|---|")
        for lo, hi in [(-1500, -500), (-500, 500), (500, 1500)]:
            b = [g for g in ok if lo <= g["gd14"] < hi]
            print(f"| {lo:+} a {hi:+} | {wr([g for g in b if g[k][0] < g[k][1]])} | {wr([g for g in b if g[k][0] > g[k][1]])} |")

print("\n## WR según cuánto tiempo pasas 1+ nivel abajo antes del 14\n\n| Tiempo abajo | Todas | Oro al 14 entre −1500 y +500 |\n|---|---|---|")
abajo = lambda g: g["exp"]["1 abajo"] + g["exp"]["2+ abajo"]
for lbl, c in [("0–1 min", lambda x: x < 1), ("1–4 min", lambda x: 1 <= x < 4), ("4+ min", lambda x: x >= 4)]:
    print(f"| {lbl} | {wr([g for g in games if c(abajo(g))])} | {wr([g for g in games if c(abajo(g)) and -1500 <= g['gd14'] < 500])} |")

top = [c for c, n in Counter(g["champ"] for g in games).most_common() if n >= 15]
print("\n## Por campeón (15+)\n\n| Campeón | Partidas | Muertes/10 min abajo | igual | arriba | % tiempo abajo | Primero al 6 |\n|---|---|---|---|---|---|---|")
for c in top:
    rs = [g for g in games if g["champ"] == c]; e = Counter(); d = Counter()
    for g in rs: e.update(g["exp"]); d.update(g["muertes"])
    ab = e["1 abajo"] + e["2+ abajo"]; ar = e["1 arriba"] + e["2+ arriba"]
    f = lambda n, x: f"{10 * n / x:.2f}" if x else "-"
    seis = [g for g in rs if None not in g["t6"]]
    print(f"| {c} | {len(rs)} | {f(d['1 abajo'] + d['2+ abajo'], ab)} | {f(d['igual'], e['igual'])} | {f(d['1 arriba'] + d['2+ arriba'], ar)} | "
          f"{ab / sum(e.values()):.0%} | {sum(g['t6'][0] < g['t6'][1] for g in seis)}/{len(seis)} |")
