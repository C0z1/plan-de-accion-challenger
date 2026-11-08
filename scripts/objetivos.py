"""Objetivos, ganks y late: tres preguntas para afinar las reglas de la tarjeta.
1. Presencia: ¿estabas cerca (posición interpolada) cuando se tomó un dragón/barón/heraldo/larvas, y separa V/D?
2. Ganks tempranos: ¿a qué minuto te matan con el jungla rival antes del 14?
3. Late: muertes del 25 en adelante a igual oro del equipo al 25.
Uso: python scripts/objetivos.py > datos/analisis-objetivos-AAAA-MM-DD.md"""
import json, os, math, pathlib, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
CERCA = 4000  # unidades: dentro de la pelea por el objetivo


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


def posicion(fr, t, i):
    """Interpolada entre la foto del minuto y la siguiente."""
    a = min(t // 60000, len(fr) - 1); b = min(a + 1, len(fr) - 1); w = (t - a * 60000) / 60000
    pa = fr[a]["participantFrames"][str(i)]["position"]; pb = fr[b]["participantFrames"][str(i)]["position"]
    return (pa["x"] + (pb["x"] - pa["x"]) * w, pa["y"] + (pb["y"] - pa["y"]) * w)
_f = [{"participantFrames": {"1": {"position": {"x": 0, "y": 0}}}}, {"participantFrames": {"1": {"position": {"x": 100, "y": 0}}}}]
assert posicion(_f, 30000, 1) == (50, 0)


games = []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 1200: continue
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] == "JUNGLE": continue
    fr = json.loads(tf.read_text())["info"]["frames"]
    pid, team = me["participantId"], me["teamId"]
    jr = next((p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] != team), None)
    evs = [e for f in fr for e in f["events"]]
    g = dict(win=me["win"], champ=me["championName"], obj=0, cerca=0, cerca_r=0, obj_r=0, ganks=[], d25=0)
    for e in evs:
        if e["type"] == "ELITE_MONSTER_KILL" and e["timestamp"] >= 14 * 60000:
            near = math.dist(posicion(fr, e["timestamp"], pid), (e["position"]["x"], e["position"]["y"])) < CERCA
            if e.get("killerTeamId") == team: g["obj"] += 1; g["cerca"] += near
            else: g["obj_r"] += 1; g["cerca_r"] += near
        if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid:
            if e["timestamp"] < 14 * 60000 and jr in {e["killerId"], *e.get("assistingParticipantIds", [])}:
                g["ganks"].append(e["timestamp"])
            if e["timestamp"] >= 25 * 60000: g["d25"] += 1
            if 25 * 60000 <= e["timestamp"] < 31 * 60000: g["d2531"] = g.get("d2531", 0) + 1
    g["larga"] = m["gameDuration"] >= 31 * 60
    g["pres"] = (g["cerca"] + g["cerca_r"]) / (g["obj"] + g["obj_r"]) if g["obj"] + g["obj_r"] else None
    if len(fr) > 25:
        g["eq25"] = sum(posicion(fr, 25 * 60000, p["participantId"]) and fr[25]["participantFrames"][str(p["participantId"])]["totalGold"]
                        * (1 if p["teamId"] == team else -1) for p in ps)
        g["d25_10"] = g["d25"] / max((m["gameDuration"] - 1500) / 600, 0.5)
    games.append(g)

V = [g for g in games if g["win"]]; D = [g for g in games if not g["win"]]
print(f"# Objetivos, ganks y late ({len(games)} partidas de 20+ min, sin jungla)\n")
print("Intervalos Wilson 95%. Posición interpolada entre fotos por minuto; \"cerca\" = a < 4000 unidades del objetivo al morir el monstruo.\n")

print("## 1. Presencia en objetivos (del 14 en adelante)\n")
print("| | Victorias | Derrotas |\n|---|---|---|")
pr = lambda gs, k, n: sum(g[k] for g in gs) / max(sum(g[n] for g in gs), 1)
print(f"| Objetivos de tu equipo con presencia tuya | {pr(V, 'cerca', 'obj'):.0%} | {pr(D, 'cerca', 'obj'):.0%} |")
print(f"| Objetivos del rival con presencia tuya | {pr(V, 'cerca_r', 'obj_r'):.0%} | {pr(D, 'cerca_r', 'obj_r'):.0%} |")
con = [g for g in games if g["pres"] is not None]
corte = sorted(g["pres"] for g in con)[len(con) // 2]
print(f"\n| Presencia en todos los objetivos | WR |\n|---|---|")
print(f"| ≥ {corte:.0%} (mediana) | {wr([g for g in con if g['pres'] >= corte])} |")
print(f"| < {corte:.0%} | {wr([g for g in con if g['pres'] < corte])} |")
print("\n**A igual oro del equipo al 25** (para separar \"vas porque ganas\" de \"ganas porque vas\"):\n")
print("| Oro del equipo @25 | Presencia ≥ mediana | < mediana |\n|---|---|---|")
for lo, hi, lab in ((-1e9, -2000, "≤ −2000"), (-2000, 2000, "−2000 a +2000"), (2000, 1e9, "≥ +2000")):
    s = [g for g in con if "eq25" in g and lo <= g["eq25"] < hi]
    print(f"| {lab} | {wr([g for g in s if g['pres'] >= corte])} | {wr([g for g in s if g['pres'] < corte])} |")

print("\n## 2. Ganks tempranos: minuto de tus muertes con el jungla rival antes del 14\n")
c = Counter(t // 60000 for g in games for t in g["ganks"])
tot = sum(c.values())
print("| Minuto | Muertes | % |\n|---|---|---|")
for mn in range(14): print(f"| {mn}:00–{mn}:59 | {c[mn]} | {c[mn] / tot:.0%} |")
print(f"\nTotal: {tot}. Partidas sin morir a un gank antes del 14: {wr([g for g in games if not g['ganks']])}; "
      f"con 1+: {wr([g for g in games if g['ganks']])}.")

print("\n## 3. Late: muertes del 25 en adelante (por 10 min) a igual oro del equipo al 25\n")
late = [g for g in games if "eq25" in g]
print("| Oro del equipo @25 | ≤ 1.5 muertes / 10 min | > 1.5 |\n|---|---|---|")
for lo, hi, lab in ((-1e9, -2000, "≤ −2000"), (-2000, 2000, "−2000 a +2000"), (2000, 1e9, "≥ +2000")):
    s = [g for g in late if lo <= g["eq25"] < hi]
    print(f"| {lab} | {wr([g for g in s if g['d25_10'] <= 1.5])} | {wr([g for g in s if g['d25_10'] > 1.5])} |")

print("\n**Control de partidas cortas** (revisión de DeepSeek): solo partidas de 31+ min, muertes en la ventana fija 25–31.\n")
print("| Oro del equipo @25 | 0 muertes | 1 | 2+ |\n|---|---|---|---|")
for lo, hi, lab in ((-1e9, -2000, "≤ −2000"), (-2000, 2000, "−2000 a +2000"), (2000, 1e9, "≥ +2000")):
    s = [g for g in late if g["larga"] and lo <= g["eq25"] < hi]
    print(f"| {lab} | {wr([g for g in s if not g.get('d2531')])} | {wr([g for g in s if g.get('d2531') == 1])} "
          f"| {wr([g for g in s if g.get('d2531', 0) >= 2])} |")
