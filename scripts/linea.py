"""¿Cómo pierdes la línea y cuál línea perdida se remonta? En partidas con oro < 0 contra tu rival al 14,
separa la desventaja por causa (muertes por gank, muertes 1 contra 1, farm, XP) por campeón, y compara
V contra D. Uso: python scripts/linea.py [Campeón] > datos/analisis-linea-AAAA-MM-DD.md   (por defecto Ekko)"""
import json, os, math, pathlib, random, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
FOCO = sys.argv[1] if len(sys.argv) > 1 else "Ekko"


def wilson(k, n, z=1.96):  # misma función que scripts/convertir.py
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


def wr(rs):
    if not rs: return "-"
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k}/{len(rs)} = {k / len(rs):.0%} ({lo:.0%}–{hi:.0%})"


def tipo(e, pid, oid, jid):
    """Muerte antes del 14: 'gank' si participa el jungla rival, '1v1' si solo tu rival de línea, si no 'otra'."""
    ids = {e["killerId"], *e.get("assistingParticipantIds", [])}
    return "gank" if jid in ids else "1v1" if ids == {oid} else "otra"
assert tipo({"killerId": 7, "assistingParticipantIds": [9]}, 1, 7, 9) == "gank"
assert tipo({"killerId": 7}, 1, 7, 9) == "1v1" and tipo({"killerId": 8, "assistingParticipantIds": [7]}, 1, 7, 9) == "otra"


games = []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    rival = lambda pos: next((p for p in ps if p["teamPosition"] == pos and p["teamId"] != me["teamId"]), None)
    opp, jg = rival(me["teamPosition"]), rival("JUNGLE")
    fr = json.loads(tf.read_text())["info"]["frames"]
    if not opp or not jg or len(fr) <= 20 or m["gameDuration"] < 1200 or me["teamPosition"] == "JUNGLE": continue
    pid, oid, jid = me["participantId"], opp["participantId"], jg["participantId"]
    pf = lambda mn, i: fr[mn]["participantFrames"][str(i)]
    dif = lambda mn, f: f(pf(mn, pid)) - f(pf(mn, oid))
    ev = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL" and e["timestamp"] < 14 * 60000]
    mias = Counter(tipo(e, pid, oid, jid) for e in ev if e["victimId"] == pid)
    games.append(dict(
        win=me["win"], champ=me["championName"], rival=opp["championName"],
        gd14=dif(14, lambda p: p["totalGold"]), gd20=dif(20, lambda p: p["totalGold"]),
        cs14=dif(14, lambda p: p["minionsKilled"] + p["jungleMinionsKilled"]), xp14=dif(14, lambda p: p["xp"]),
        cs10=dif(10, lambda p: p["minionsKilled"] + p["jungleMinionsKilled"]),
        d14=sum(mias.values()), gank=mias["gank"], uno=mias["1v1"],
        k14=sum(e["killerId"] == pid for e in ev), od14=sum(e["victimId"] == oid for e in ev),
        primera=min((e["timestamp"] / 60000 for e in ev if e["victimId"] == pid), default=None)))
assert games, "sin timelines"
perd = [g for g in games if g["gd14"] < 0]

FILAS = [("Oro vs rival @14", "gd14", "+.0f"), ("Oro vs rival @20", "gd20", "+.0f"), ("CS vs rival @10", "cs10", "+.1f"),
         ("CS vs rival @14", "cs14", "+.1f"), ("XP vs rival @14", "xp14", "+.0f"), ("Tus muertes <14", "d14", ".2f"),
         ("  por gank (jungla rival)", "gank", ".2f"), ("  1 contra 1 (solo tu rival)", "uno", ".2f"),
         ("Tus kills <14", "k14", ".2f"), ("Muertes de tu rival <14", "od14", ".2f")]
avg = lambda rs, k: st.mean([r[k] for r in rs]) if rs else float("nan")

print(f"# Perder la línea: cómo y cuál se remonta ({len(perd)} de {len(games)} partidas con oro < 0 al 14, 20+ min, sin jungla)\n")
print("Intervalos Wilson 95%. \"Gank\" = el jungla rival mató o asistió; \"1 contra 1\" = solo te mató tu rival de línea. "
      "Oro, CS y XP = tú menos tu rival de línea.\n")

top = [c for c, n in Counter(g["champ"] for g in perd).most_common() if n >= 8]
grupos = [[g for g in perd if g["champ"] == c] for c in top] + [perd]
print("## Por campeón, con la línea perdida (8+ partidas)\n")
print("| | " + " | ".join(top) + " | Todos |\n|---|" + "---|" * (len(top) + 1))
print("| WR | " + " | ".join(wr(rs) for rs in grupos) + " |")
for lbl, k, f in FILAS:
    print(f"| {lbl} | " + " | ".join(f"{avg(rs, k):{f}}" for rs in grupos) + " |")
print("| Sin morir antes del 14 | " + " | ".join(f"{sum(g['d14'] == 0 for g in rs)}/{len(rs)}" for rs in grupos) + " |")

W, L = [g for g in perd if g["win"]], [g for g in perd if not g["win"]]
print(f"\n## Todos: victorias contra derrotas con la línea perdida\n\n| | Victorias | Derrotas |\n|---|---|---|")
print(f"| Partidas | {len(W)} | {len(L)} |")
for lbl, k, f in FILAS:
    print(f"| {lbl} | {avg(W, k):{f}} | {avg(L, k):{f}} |")

CONDS = [("0 muertes antes del 14", lambda g: g["d14"] == 0), ("1 muerte", lambda g: g["d14"] == 1),
         ("2+ muertes", lambda g: g["d14"] >= 2), ("0 muertes por gank", lambda g: g["gank"] == 0),
         ("1+ muertes por gank", lambda g: g["gank"] >= 1), ("1+ muertes 1 contra 1", lambda g: g["uno"] >= 1),
         ("Primera muerte antes del 6", lambda g: g["primera"] is not None and g["primera"] < 6),
         ("Pierdes ≤ 1000 de oro al 14", lambda g: g["gd14"] > -1000), ("Pierdes > 1000", lambda g: g["gd14"] <= -1000),
         ("Pierdes ≤ 10 de CS al 14", lambda g: g["cs14"] >= -10), ("Pierdes > 10 de CS", lambda g: g["cs14"] < -10),
         ("Pierdes ≤ 500 de XP al 14", lambda g: g["xp14"] >= -500), ("Pierdes > 500 de XP", lambda g: g["xp14"] < -500),
         ("Recortas la desventaja del 14 al 20", lambda g: g["gd20"] > g["gd14"])]
foco = [g for g in perd if g["champ"] == FOCO]
print(f"\n## WR con la línea perdida, según cómo la perdiste\n\n| Condición | Todos | {FOCO} |\n|---|---|---|")
for lbl, c in CONDS:
    print(f"| {lbl} | {wr([g for g in perd if c(g)])} | {wr([g for g in foco if c(g)])} |")

print(f"\n## {FOCO}: victorias contra derrotas con la línea perdida\n\n| | Victorias | Derrotas |\n|---|---|---|")
FW, FL = [g for g in foco if g["win"]], [g for g in foco if not g["win"]]
print(f"| Partidas | {len(FW)} | {len(FL)} |")
for lbl, k, f in FILAS:
    print(f"| {lbl} | {avg(FW, k):{f}} | {avg(FL, k):{f}} |")

# ¿El CS separa por sí mismo o solo porque es parte del oro? Compara a igual oro @14.
banda = [g for g in perd if -1500 <= g["gd14"] <= -500]
print(f"\n## A igual oro: solo partidas entre −1500 y −500 de oro al 14 ({len(banda)})\n\n| | Victorias | Derrotas |\n|---|---|---|")
BW, BL = [g for g in banda if g["win"]], [g for g in banda if not g["win"]]
print(f"| Partidas | {len(BW)} | {len(BL)} |")
for lbl, k, f in FILAS[:6]:
    print(f"| {lbl} | {avg(BW, k):{f}} | {avg(BL, k):{f}} |")
mcs = st.median(g["cs14"] for g in banda)
print(f"| WR con CS @14 ≥ mediana ({mcs:+.0f}) | {wr([g for g in banda if g['cs14'] >= mcs])} | |")
print(f"| WR con CS @14 < mediana | {wr([g for g in banda if g['cs14'] < mcs])} | |")
mxp = st.median(g["xp14"] for g in banda)
print(f"| WR con XP @14 ≥ mediana ({mxp:+.0f}) | {wr([g for g in banda if g['xp14'] >= mxp])} | |")
print(f"| WR con XP @14 < mediana | {wr([g for g in banda if g['xp14'] < mxp])} | |")


# ¿El CS perdido depende del matchup? Todas las partidas (ganadas o no), rivales de línea con 5+.
def dispersion(gs, etiqueta):
    """Varianza entre grupos de la media de CS @14 (ponderada por n): alta si el rival explica el farm."""
    grupos = {}
    for g in gs: grupos.setdefault(etiqueta(g), []).append(g["cs14"])
    mu = st.mean(g["cs14"] for g in gs)
    return sum(len(v) * (st.mean(v) - mu) ** 2 for v in grupos.values()) / len(gs)
assert dispersion([{"cs14": 1, "r": "a"}, {"cs14": 1, "r": "a"}, {"cs14": 3, "r": "b"}], lambda g: g["r"]) > 0


freq = {c for c, n in Counter(g["rival"] for g in games).items() if n >= 5}
con = [g for g in games if g["rival"] in freq]
real = dispersion(con, lambda g: g["rival"])
rng, etq = random.Random(7), [g["rival"] for g in con]
sims = []
for _ in range(2000):
    rng.shuffle(etq); m = dict(zip(map(id, con), etq))
    sims.append(dispersion(con, lambda g: m[id(g)]))
p = sum(s >= real for s in sims) / len(sims)
print(f"\n## CS por rival de línea (todas las partidas de 20+ min, rivales con 5+: {len(freq)} rivales, {len(con)} partidas)\n")
print(f"Test de permutación (2000 barajadas del rival): la dispersión real del CS @14 entre rivales es {real:.1f} "
      f"contra {st.mean(sims):.1f} del azar, p = {p:.2f}. Con p alta, el matchup no explica tu farm perdido.\n")
print("| Rival | Partidas | CS @10 | CS @14 | Oro @14 | % CS @14 < −10 | WR |\n|---|---|---|---|---|---|---|")
for c in sorted(freq, key=lambda c: avg([g for g in con if g["rival"] == c], "cs14")):
    rs = [g for g in con if g["rival"] == c]
    print(f"| {c} | {len(rs)} | {avg(rs, 'cs10'):+.1f} | {avg(rs, 'cs14'):+.1f} | {avg(rs, 'gd14'):+.0f} | "
          f"{sum(g['cs14'] < -10 for g in rs) / len(rs):.0%} | {wr(rs)} |")
