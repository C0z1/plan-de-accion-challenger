"""Muertes antes del minuto 6: cuántas, de qué tipo (1 contra 1 con tu rival de línea, gank, otra), por campeón y por rival,
diferencia de nivel al 3 y al 6, y cuánto cambian el WR y el oro al 14 cuando mueres antes del 6.
Uso: python scripts/muertes6.py > datos/analisis-muertes6-AAAA-MM-DD.md"""
import json, math, pathlib, sys
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE", "TOP", "BOTTOM", "UTILITY"}
SEIS = 6 * 60000


def wilson(k, n, z=1.96):  # misma función que scripts/linea.py
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


def wr(gs):
    if not gs: return "-"
    k = sum(g["win"] for g in gs); lo, hi = wilson(k, len(gs))
    return f"{k}/{len(gs)} = {k / len(gs):.0%} ({lo:.0%}–{hi:.0%})"


def media(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def nivel(ups, t):  # misma función que scripts/nivel6.py
    return max([lv for ts, lv in ups if ts <= t], default=1)
assert nivel([(60000, 2), (120000, 3)], 90000) == 2 and nivel([(60000, 2)], 0) == 1


def tipo(e, oid, jr):
    """1v1 = solo tu rival de línea (sin asistencias); gank = participa el jungla rival; otra = el resto."""
    quien = {e["killerId"], *e.get("assistingParticipantIds", [])}
    if jr in quien: return "gank"
    if quien == {oid}: return "1v1"
    return "otra"
assert tipo({"killerId": 7}, 7, 8) == "1v1" and tipo({"killerId": 7, "assistingParticipantIds": [8]}, 7, 8) == "gank" \
    and tipo({"killerId": 9}, 7, 8) == "otra"

games = []
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 900: continue  # 15+ min, mismo corte que early.py
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] not in LINEA: continue
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    if not opp: continue
    fr = json.loads(tf.read_text())["info"]["frames"]
    if len(fr) <= 14: continue
    pid, oid = me["participantId"], opp["participantId"]
    jr = next((p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] != me["teamId"]), None)
    ev = [e for f in fr for e in f["events"]]
    ups = lambda i: sorted((e["timestamp"], e["level"]) for e in ev if e["type"] == "LEVEL_UP" and e["participantId"] == i)
    mis, sus = ups(pid), ups(oid)
    kills = [e for e in ev if e["type"] == "CHAMPION_KILL" and e["timestamp"] < SEIS]
    # nivel 3 s antes de morir: al instante el LEVEL_UP del propio kill ya cuenta (ver nivel6.py)
    muertes = [dict(t=e["timestamp"], tipo=tipo(e, oid, jr), dn=nivel(mis, e["timestamp"] - 3000) - nivel(sus, e["timestamp"] - 3000))
               for e in kills if e["victimId"] == pid]
    mato = sum(1 for e in kills if e["victimId"] == oid and pid in {e["killerId"], *e.get("assistingParticipantIds", [])})
    pf = lambda mn, k: fr[mn]["participantFrames"][str(pid)][k] - fr[mn]["participantFrames"][str(oid)][k]
    games.append(dict(win=me["win"], champ=me["championName"], rival=opp["championName"], rol=me["teamPosition"],
                      id=tf.stem, muertes=muertes, mato=mato, dn3=nivel(mis, 180000) - nivel(sus, 180000),
                      dn6=nivel(mis, SEIS) - nivel(sus, SEIS), gd14=pf(14, "totalGold"), xp14=pf(14, "xp"),
                      gd6=pf(6, "totalGold")))
assert games, "sin timelines"
n = len(games)
cero = [g for g in games if not g["muertes"]]
alguna = [g for g in games if g["muertes"]]
assert len(cero) + len(alguna) == n

print(f"# Muertes antes del minuto 6 ({n} partidas, 15+ min, sin jungla)\n")
print("Tipo: **1v1** = te mató solo tu rival de línea; **gank** = participó el jungla rival; **otra** = el resto. "
      "Nivel = tu nivel − el de tu rival (eventos LEVEL_UP), al 3:00 y al 6:00; en cada muerte, 3 s antes. Intervalos Wilson 95%.\n")

tot = [d for g in games for d in g["muertes"]]
print(f"Muertes antes del 6: {len(tot)} en {len(alguna)} partidas ({len(alguna) / n:.0%}). "
      + ", ".join(f"{t} {sum(d['tipo'] == t for d in tot)}" for t in ("1v1", "gank", "otra")) + ".\n")

print("## WR y oro al 14 según las muertes antes del 6\n\n| Muertes <6 | Partidas | WR | Oro @14 | XP @14 | Oro @6 |\n|---|---|---|---|---|---|")
for nom, gs in [("0", cero), ("1", [g for g in games if len(g["muertes"]) == 1]), ("2+", [g for g in games if len(g["muertes"]) >= 2]), ("1+", alguna)]:
    print(f"| {nom} | {len(gs)} | {wr(gs)} | {media([g['gd14'] for g in gs]):+.0f} | {media([g['xp14'] for g in gs]):+.0f} | {media([g['gd6'] for g in gs]):+.0f} |")
print()

print("¿Partidas con sangre? Muertes <6 cruzadas con tus kills/asistencias sobre tu rival antes del 6:\n\n"
      "| | 0 kills tuyos <6 | 1+ kills tuyos <6 |\n|---|---|---|")
for nom, gs in [("0 muertes <6", cero), ("1+ muertes <6", alguna)]:
    print(f"| {nom} | {wr([g for g in gs if not g['mato']])} | {wr([g for g in gs if g['mato']])} |")
print()

print("## Por tipo de la primera muerte antes del 6\n\n| Tipo | Partidas | WR | Oro @14 |\n|---|---|---|---|")
for t in ("1v1", "gank", "otra"):
    gs = [g for g in alguna if g["muertes"][0]["tipo"] == t]
    print(f"| {t} | {len(gs)} | {wr(gs)} | {media([g['gd14'] for g in gs]):+.0f} |")
gs = [g for g in games if not any(d["tipo"] == "1v1" for d in g["muertes"])]
print(f"\nSin ninguna muerte 1v1 antes del 6: {wr(gs)}; con 1+: {wr([g for g in games if g not in gs])}.\n")

# control: ¿morir antes del 6 pesa a igual línea, o solo es parte de perderla? Se corta por el oro al 14 SIN contar el
# oro que da tu muerte no se puede separar; el corte es por tercios del oro @14 y, más limpio, por el kill propio antes del 6.
print("## Control: dentro de tercios de oro @14\n\n| Tercio de oro @14 | 0 muertes <6 | 1+ muertes <6 |\n|---|---|---|")
orden = sorted(games, key=lambda g: g["gd14"])
for i, nom in enumerate(("bajo", "medio", "alto")):
    tr = orden[i * n // 3:(i + 1) * n // 3]
    print(f"| {nom} ({tr[0]['gd14']:+.0f} a {tr[-1]['gd14']:+.0f}) | {wr([g for g in tr if not g['muertes']])} | {wr([g for g in tr if g['muertes']])} |")
print("\nOjo: tu muerte le da oro al rival, así que el oro @14 es en parte *consecuencia* de morir; este control sobre-controla.\n")

print("## Diferencia de nivel al 3 y al 6\n\n| Nivel | Al 3: partidas | WR | % con muerte <6 | Al 6: partidas | WR | % con muerte <6 |\n|---|---|---|---|---|---|---|")
for d in (-1, 0, 1):
    a = [g for g in games if max(-1, min(1, g["dn3"])) == d]; b = [g for g in games if max(-1, min(1, g["dn6"])) == d]
    nom = {-1: "abajo (≤ −1)", 0: "igual", 1: "arriba (≥ +1)"}[d]
    pm = lambda gs: f"{sum(1 for g in gs if g['muertes']) / len(gs):.0%}" if gs else "-"
    print(f"| {nom} | {len(a)} | {wr(a)} | {pm(a)} | {len(b)} | {wr(b)} | {pm(b)} |")
dn = [d["dn"] for d in tot]
print(f"\nEn el momento de las muertes <6: abajo {sum(x < 0 for x in dn)}, igual {sum(x == 0 for x in dn)}, arriba {sum(x > 0 for x in dn)}. "
      f"Las 1v1: abajo {sum(d['dn'] < 0 for d in tot if d['tipo'] == '1v1')}, igual {sum(d['dn'] == 0 for d in tot if d['tipo'] == '1v1')}, "
      f"arriba {sum(d['dn'] > 0 for d in tot if d['tipo'] == '1v1')}.\n")

print("## Por campeón (8+ partidas)\n\n| Campeón | Partidas | % con muerte <6 | 1v1 <6 por partida | WR con 0 | WR con 1+ | Oro @14 con 0 / 1+ |\n|---|---|---|---|---|---|---|")
por = defaultdict(list)
for g in games: por[g["champ"]].append(g)
for c, gs in sorted(por.items(), key=lambda kv: -len(kv[1])):
    if len(gs) < 8: continue
    z = [g for g in gs if not g["muertes"]]; u = [g for g in gs if g["muertes"]]
    print(f"| {c} | {len(gs)} | {len(u) / len(gs):.0%} | {media([sum(d['tipo'] == '1v1' for d in g['muertes']) for g in gs]):.2f} | {wr(z)} | {wr(u)} | "
          f"{media([g['gd14'] for g in z]):+.0f} / {media([g['gd14'] for g in u]):+.0f} |")
print()

print("## Por rival de línea (5+ partidas, ordenado por % con muerte <6)\n\n| Rival | Partidas | % con muerte <6 | 1v1 <6 | WR |\n|---|---|---|---|---|")
por = defaultdict(list)
for g in games: por[g["rival"]].append(g)
filas = [(r, gs) for r, gs in por.items() if len(gs) >= 5]
for r, gs in sorted(filas, key=lambda kv: -sum(1 for g in kv[1] if g["muertes"]) / len(kv[1])):
    print(f"| {r} | {len(gs)} | {sum(1 for g in gs if g['muertes']) / len(gs):.0%} | {sum(d['tipo'] == '1v1' for g in gs for d in g['muertes'])} | {wr(gs)} |")
print()

# permutación del rival: ¿el % con muerte <6 varía por rival más que por azar?
import random
random.seed(1)
def disp(etq):
    grp = defaultdict(list)
    for e, g in zip(etq, games): grp[e].append(1 if g["muertes"] else 0)
    vals = [media(v) for v in grp.values() if len(v) >= 5]
    mu = media(vals); return media([(v - mu) ** 2 for v in vals])
etq = [g["rival"] for g in games]; real = disp(etq); mayor = 0
for _ in range(2000):
    random.shuffle(etq); mayor += disp(etq) >= real
print(f"Permutación del rival (2000): dispersión real {real:.4f}, p = {mayor / 2000:.2f}.\n")

print("## Últimas 10 partidas\n\n| Partida | Campeón | Rival | V/D | Muertes <6 (min, tipo, nivel) | Nivel @3 / @6 | Oro @14 |\n|---|---|---|---|---|---|---|")
for g in sorted(games, key=lambda g: g["id"])[-10:]:
    ms = ", ".join(f"{d['t'] / 60000:.1f} {d['tipo']} {d['dn']:+d}" for d in g["muertes"]) or "-"
    print(f"| {g['id']} | {g['champ']} | {g['rival']} | {'V' if g['win'] else 'D'} | {ms} | {g['dn3']:+d} / {g['dn6']:+d} | {g['gd14']:+d} |")
