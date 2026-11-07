"""Revisión: tus últimas N partidas contra las metas del PLAN (para los domingos y al terminar cada sesión).
Uso: python scripts/revision.py [N]   (por defecto 20; antes corre scripts/descargar.py para bajar las nuevas)"""
import json, math, pathlib, statistics as st, sys
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
POOL = {"Yone", "Ekko", "Mordekaiser"}  # PLAN, prioridad 2


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


games = []
for f in RAW.glob("LA1_*.json"):
    m = json.loads(f.read_text())["info"]
    if m["gameDuration"] < 300 or m.get("gameEndedInEarlySurrender"): continue
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    g = dict(win=me["win"], champ=me["championName"], t=m["gameCreation"], cw=me.get("visionWardsBoughtInGame", 0),
             placas=me.get("challenges", {}).get("turretPlatesTaken", 0), gd14=None, cd14=None, d14=None, d25=None)
    tf = RAW / "timeline" / f.name
    if tf.exists():
        fr = json.loads(tf.read_text())["info"]["frames"]; pid = me["participantId"]
        if opp and len(fr) > 14:
            a, b = fr[14]["participantFrames"][str(pid)], fr[14]["participantFrames"][str(opp["participantId"])]
            g["gd14"] = a["totalGold"] - b["totalGold"]
            g["cd14"] = a["minionsKilled"] + a["jungleMinionsKilled"] - b["minionsKilled"] - b["jungleMinionsKilled"]
        mins = [e["timestamp"] / 60000 for x in fr for e in x["events"] if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid]
        g["d14"] = sum(t < 14 for t in mins); g["d25"] = sum(14 <= t < 25 for t in mins)
    games.append(g)
games.sort(key=lambda g: g["t"])
assert games, "sin partidas"

N = int(sys.argv[1]) if len(sys.argv) > 1 else 20
rec, ant = games[-N:], games[:-N]


def prop(rs, ok):
    """Proporción con intervalo, solo entre las partidas que tienen el dato (ok devuelve None si falta)."""
    vs = [v for v in (ok(r) for r in rs) if v is not None]
    if not vs: return "-", None
    k = sum(vs); lo, hi = wilson(k, len(vs))
    return f"{k / len(vs):.0%} ({lo:.0%}–{hi:.0%}, n={len(vs)})", k / len(vs)


def media(rs, key):
    vs = [r[key] for r in rs if r[key] is not None]
    return (f"{st.mean(vs):+.1f}" if key in ("gd14", "cd14") else f"{st.mean(vs):.2f}", st.mean(vs)) if vs else ("-", None)


# (métrica, cómo se calcula, meta legible, prueba de la meta)
METRICAS = [
    ("Win rate", lambda rs: prop(rs, lambda r: r["win"]), "≥ 55% (semana 1), ≥ 58% después", lambda v: v >= .55),
    ("Oro ≥ 0 contra tu rival al 14", lambda rs: prop(rs, lambda r: None if r["gd14"] is None else r["gd14"] >= 0),
     "> 55%", lambda v: v > .55),
    ("WR cuando llegas al 14 con oro ≥ 0 (convertir)",
     lambda rs: prop([r for r in rs if r["gd14"] is not None and r["gd14"] >= 0], lambda r: r["win"]),
     "≥ 60% (tu temporada: 62%)", lambda v: v >= .6),
    ("Oro contra tu rival al 14 (media)", lambda rs: media(rs, "gd14"), "≥ 0", lambda v: v >= 0),
    ("CS contra tu rival al 14 (media)", lambda rs: media(rs, "cd14"), "≥ 0", lambda v: v >= 0),
    ("Muertes antes del 14", lambda rs: media(rs, "d14"), "referencia: 2.12 en victorias", lambda v: v <= 2.12),
    ("Muertes del 14 al 25", lambda rs: media(rs, "d25"), "≤ 2", lambda v: v <= 2),
    ("Partidas con ≥ 1 control ward", lambda rs: prop(rs, lambda r: r["cw"] >= 1), "100% (1 por regreso a base)",
     lambda v: v >= .9),
    ("Control wards por partida", lambda rs: media(rs, "cw"), "≥ 1", lambda v: v >= 1),
    ("Partidas con el pool (Yone, Ekko, Mordekaiser)", lambda rs: prop(rs, lambda r: r["champ"] in POOL), "> 80%",
     lambda v: v > .8),
    ("Placas de torre", lambda rs: media(rs, "placas"), "referencia: 11.7 en victorias, 6.8 en derrotas", None),
]

fecha = lambda g: datetime.fromtimestamp(g["t"] / 1000)
print(f"# Revisión: últimas {len(rec)} partidas ({fecha(rec[0]):%Y-%m-%d} a {fecha(rec[-1]):%Y-%m-%d}) "
      f"contra las {len(ant)} anteriores\n")
print("✅ cumple la meta · ❌ no la cumple. Con pocas partidas el intervalo es ancho (con 20, ±20 puntos): "
      "mira la tendencia, no un solo número.\n")
print(f"| Métrica | Últimas {len(rec)} | Anteriores | Meta | |\n|---|---|---|---|---|")
for nombre, calc, meta, cumple in METRICAS:
    (txt, v), (txt0, _) = calc(rec), calc(ant)
    marca = "" if cumple is None or v is None else ("✅" if cumple(v) else "❌")
    print(f"| {nombre} | {txt} | {txt0} | {meta} | {marca} |")

print(f"\n## Partida por partida (más reciente primero)\n\n| Fecha | Campeón | | Oro @14 | CS @14 | Muertes <14 | Muertes 14–25 | Control wards |\n|---|---|---|---|---|---|---|---|")
f = lambda v, fmt="{:+d}": "-" if v is None else fmt.format(v)
for g in reversed(rec):
    print(f"| {fecha(g):%m-%d %H:%M} | {g['champ']}{'' if g['champ'] in POOL else ' (fuera del pool)'} | "
          f"{'V' if g['win'] else 'D'} | {f(g['gd14'])} | {f(g['cd14'])} | {f(g['d14'], '{}')} | {f(g['d25'], '{}')} | {g['cw']} |")
