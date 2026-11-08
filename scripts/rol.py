"""¿Mid o top como rol principal? Compara por rol: WR, línea al 14, conversión, muertes, campeones
y tendencia reciente; con intervalos Wilson y un test de permutación de la diferencia mid vs top.
Uso: python scripts/rol.py > datos/analisis-rol-AAAA-MM-DD.md"""
import json, os, math, pathlib, random, statistics as st, sys
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
NOMBRE = {"MIDDLE": "mid", "TOP": "top", "UTILITY": "support", "JUNGLE": "jungla", "BOTTOM": "adc"}
CFG_F = pathlib.Path(__file__).resolve().parent.parent / "config.json"  # opcional, como en revision.py
CFG = json.loads(CFG_F.read_text(encoding="utf-8")) if CFG_F.exists() else {}


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


def perm_p(a, b, reps=5000, seed=1):
    """p bilateral: ¿qué tan seguido el azar (barajar V/D entre los dos grupos) da una diferencia de WR tan grande?"""
    obs = abs(st.mean(a) - st.mean(b)); todo = a + b; rnd = random.Random(seed); hits = 0
    for _ in range(reps):
        rnd.shuffle(todo)
        hits += abs(st.mean(todo[:len(a)]) - st.mean(todo[len(a):])) >= obs - 1e-12
    return hits / reps
assert perm_p([1] * 30, [0] * 30) < 0.01 and perm_p([1, 0] * 20, [0, 1] * 20) > 0.9


games = []
for mf in RAW.glob("*_*.json"):
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    g = dict(win=int(me["win"]), champ=me["championName"], rol=NOMBRE.get(me["teamPosition"], "?"), t=m["gameCreation"],
             gd14=None, d14=None, d1425=None)
    tf = RAW / "timeline" / mf.name
    if opp and tf.exists():
        fr = json.loads(tf.read_text())["info"]["frames"]
        if len(fr) > 14:
            pid = me["participantId"]
            oro = lambda i: fr[14]["participantFrames"][str(i)]["totalGold"]
            g["gd14"] = oro(pid) - oro(opp["participantId"])
            dt = [e["timestamp"] / 60000 for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid]
            g["d14"] = sum(t < 14 for t in dt); g["d1425"] = sum(14 <= t < 25 for t in dt)
    games.append(g)
assert games, "sin partidas"
games.sort(key=lambda g: g["t"])
por_rol = defaultdict(list)
for g in games: por_rol[g["rol"]].append(g)
# tus dos roles más jugados (para cozi: mid y top); con uno solo, el segundo queda vacío
R1, R2 = ([r for r, _ in Counter(g["rol"] for g in games).most_common(2)] + ["-"])[:2]
POOL = CFG.get("pool") or [c for c, _ in Counter(g["champ"] for g in games).most_common(3)]

avg = lambda rs, k: st.mean([r[k] for r in rs if r[k] is not None] or [0])
print(f"# {R1.capitalize()} contra {R2} ({len(games)} partidas sin remakes)\n")
print("Intervalos Wilson 95%. Oro @14 = tu oro menos el de tu rival de línea. Convertir = WR cuando llegas al 14 con oro >= 0.\n")
print("## Por rol\n\n| Rol | Partidas | WR | Oro @14 | Oro >= 0 al 14 | Convertir | Muertes <14 | Muertes 14–25 |\n|---|---|---|---|---|---|---|---|")
for rol, rs in sorted(por_rol.items(), key=lambda kv: -len(kv[1])):
    tl = [r for r in rs if r["gd14"] is not None]; ok = [r for r in tl if r["gd14"] >= 0]
    print(f"| {rol} | {len(rs)} | {wr(rs)} | {avg(tl, 'gd14'):+.0f} | {len(ok) / max(1, len(tl)):.0%} | {wr(ok)} | "
          f"{avg(tl, 'd14'):.2f} | {avg(tl, 'd1425'):.2f} |")

mid, top = [g["win"] for g in por_rol[R1]], [g["win"] for g in por_rol[R2]]
if mid and top:
    p = perm_p(mid, top)
    print(f"\n**Diferencia {R2} − {R1}:** {st.mean(top) - st.mean(mid):+.1%}. Test de permutación (5000 barajadas): p = {p:.2f}.")
    # n por grupo para detectar la diferencia observada con 80% de potencia y alfa 0.05 (aprox. normal)
    p1, p2 = st.mean(mid), st.mean(top); pb = (p1 + p2) / 2
    n_nec = math.ceil(((1.96 * math.sqrt(2 * pb * (1 - pb)) + 0.84 * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) / (p2 - p1)) ** 2) if p1 != p2 else None
    print(f"Para confirmar una diferencia de ese tamaño harían falta ~{n_nec} partidas por rol (hoy {R2} tiene {len(top)}).\n")

print("## Campeones por rol (3+ partidas)\n\n| Rol | Campeón | WR | Oro @14 |\n|---|---|---|---|")
for rol in (R1, R2):
    c = Counter(g["champ"] for g in por_rol[rol])
    for ch, n in c.most_common():
        if n < 3: break
        rs = [g for g in por_rol[rol] if g["champ"] == ch]
        print(f"| {rol} | {ch} | {wr(rs)} | {avg([r for r in rs if r['gd14'] is not None], 'gd14'):+.0f} |")

# el campeón de mejor WR (3+ partidas) en tu 2.º rol: ¿ese rol rinde por él o por el rol? (cozi: Mordekaiser top)
c2 = [ch for ch, n in Counter(g["champ"] for g in por_rol[R2]).items() if n >= 3]
MEJOR = max(c2, key=lambda ch: st.mean(g["win"] for g in por_rol[R2] if g["champ"] == ch), default=None)
EN_POOL = [c for c in POOL if any(g["champ"] == c for g in por_rol[R1])]
print(f"\n## {R2.capitalize()} sin {MEJOR} y {R1} solo con el pool ({', '.join(EN_POOL)})\n\n| Grupo | WR |\n|---|---|")
print(f"| {R2.capitalize()} con {MEJOR} | {wr([g for g in por_rol[R2] if g['champ'] == MEJOR])} |")
print(f"| {R2.capitalize()} sin {MEJOR} | {wr([g for g in por_rol[R2] if g['champ'] != MEJOR])} |")
print(f"| {R1.capitalize()} con {' o '.join(EN_POOL)} | {wr([g for g in por_rol[R1] if g['champ'] in EN_POOL])} |")
print(f"| {R1.capitalize()} con otros | {wr([g for g in por_rol[R1] if g['champ'] not in EN_POOL])} |")

print("\n## Tendencia: últimas N partidas de cada rol\n\n| Rol | Últimas 20 | Últimas 40 | Todas |\n|---|---|---|---|")
for rol in (R1, R2):
    rs = por_rol[rol]
    print(f"| {rol} | {wr(rs[-20:])} | {wr(rs[-40:])} | {wr(rs)} |")
