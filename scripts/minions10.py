"""Calibra el aviso en vivo de minions al 10 (companion.aviso_minions). La meta sale de laneMinionsFirst10Minutes
(solo minions de línea), pero en vivo solo se ve scores.creepScore (minions + monstruos). Aquí se reconstruye el
creepScore del minuto 10 con el timeline (minionsKilled + jungleMinionsKilled en la foto de las 10:00) y se mide:
cuánto se aleja de la meta, qué umbral de creepScore separa mejor y cuántos avisos serían falsos.
Por si la API en vivo lo da de 10 en 10, también se mide con el creepScore redondeado hacia abajo a la decena.
Uso: python scripts/minions10.py [Campeón] [mínimo]   (por defecto, minions10 de config.json)"""
import json, os, pathlib, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
BASE = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or BASE / "datos" / "raw")
CFG = BASE / "config.json"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
m10 = (json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}).get("minions10") or {}
champ = sys.argv[1] if len(sys.argv) > 1 else m10.get("campeon")
minimo = int(sys.argv[2]) if len(sys.argv) > 2 else m10.get("minimo")
if not champ or not minimo: sys.exit("Uso: minions10.py <Campeón> <mínimo> (o pon minions10 en config.json)")


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return (max(0, c - h), min(1, c + h))


def wr(rs):
    k = sum(r["win"] for r in rs); lo, hi = wilson(k, len(rs))
    return f"{k}/{len(rs)} = {k / len(rs):.0%} ({lo:.0%}–{hi:.0%})" if rs else "-"


def leer():
    gs = []
    for tf in (RAW / "timeline").glob("*_*.json"):
        mf = RAW / tf.name
        if not mf.exists(): continue
        m = json.loads(mf.read_text())["info"]
        if m["gameDuration"] < 660: continue  # remakes y partidas sin minuto 11
        me = next(p for p in m["participants"] if p["puuid"] == puuid)
        if me["championName"] != champ or "laneMinionsFirst10Minutes" not in me.get("challenges", {}): continue
        fr = json.loads(tf.read_text())["info"]["frames"]
        if len(fr) <= 10: continue
        p = fr[10]["participantFrames"][str(me["participantId"])]
        gs.append(dict(win=me["win"], linea=me["challenges"]["laneMinionsFirst10Minutes"],
                       cs=p["minionsKilled"] + p["jungleMinionsKilled"], jg=p["jungleMinionsKilled"]))
    return gs


def avisa(g, corte, decena): return (g["cs"] // 10 * 10 if decena else g["cs"]) < corte


games = leer()
if not games: sys.exit(f"Sin partidas de {champ} con timeline.")
n = len(games)
print(f"# Aviso de minions al 10 con {champ} (meta {minimo}+ de línea), {n} partidas\n")
print(f"- Base: {wr(games)}. Meta cumplida (línea ≥ {minimo}): {wr([g for g in games if g['linea'] >= minimo])}; "
      f"no: {wr([g for g in games if g['linea'] < minimo])}.")
dif = Counter(g["cs"] - g["linea"] for g in games)
print(f"- creepScore @10:00 (timeline) − minions de línea @10 (challenge): {dict(sorted(dif.items()))} "
      f"(monstruos en la foto: media {sum(g['jg'] for g in games) / n:.1f}).\n")
print("| Umbral de creepScore | En vivo | Avisa | WR si avisa | WR si no | Falsos (línea ≥ meta) | Perdidos (línea < meta sin aviso) |")
print("|---|---|---|---|---|---|---|")
for decena in (False, True):
    for corte in range(minimo - 10, minimo + 11, 2 if not decena else 10):
        a = [g for g in games if avisa(g, corte, decena)]; b = [g for g in games if not avisa(g, corte, decena)]
        fal = sum(g["linea"] >= minimo for g in a); per = sum(g["linea"] < minimo for g in b)
        print(f"| < {corte} | {'de 10 en 10' if decena else 'exacto'} | {len(a)} | {wr(a)} | {wr(b)} | {fal} | {per} |")
assert all(g["cs"] >= 0 and g["jg"] >= 0 for g in games)
