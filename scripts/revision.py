"""Revisión: tus últimas N partidas contra las metas del PLAN (para los domingos y al terminar cada sesión).
Uso: python scripts/revision.py [N]   (por defecto 20; antes corre scripts/descargar.py para bajar las nuevas)"""
import json, os, math, pathlib, statistics as st, sys
from collections import Counter
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
CFG_F = pathlib.Path(__file__).resolve().parent.parent / "config.json"  # opcional; ejemplo: config.ejemplo.json
CFG = json.loads(CFG_F.read_text(encoding="utf-8")) if CFG_F.exists() else {}
M10 = CFG.get("minions10")  # p. ej. {"campeon": "Sylas", "minimo": 69}; sin él no hay esa meta
NOMBRE = {"MIDDLE": "mid", "TOP": "top", "BOTTOM": "bot", "UTILITY": "bot"}  # misma tabla que scripts/nivel6.py


def zone(x, y, team):  # misma función que scripts/nivel6.py
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"


def pasado(z, linea):
    """¿La muerte fue pasado el río (mitad rival de tu línea, río o jungla rival)? Ver PLAN, prioridad 1."""
    return z == "río" or (z.endswith("(lado rival)") and (z.startswith(linea) or z.startswith("jungla")))
assert pasado(zone(7400, 7400, 100), "mid") and not pasado(zone(5000, 5000, 100), "mid") and pasado("río", "top")
assert not pasado("top (lado rival)", "mid") and pasado("jungla (lado rival)", "bot")


def wilson(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)
assert [round(v, 3) for v in wilson(5, 10)] == [0.237, 0.763]


games = []
for f in RAW.glob("*_*.json"):
    m = json.loads(f.read_text())["info"]
    if m["gameDuration"] < 300 or m.get("gameEndedInEarlySurrender"): continue
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    g = dict(win=me["win"], champ=me["championName"], t=m["gameCreation"], cw=me.get("visionWardsBoughtInGame", 0),
             gd14=None, cd14=None, xd14=None, lv6=None, d14=None, d25=None, rio14=None,
             lm10=me.get("challenges", {}).get("laneMinionsFirst10Minutes") if M10 and me["championName"] == M10["campeon"] else None)
    tf = RAW / "timeline" / f.name
    if tf.exists():
        fr = json.loads(tf.read_text())["info"]["frames"]; pid = me["participantId"]
        if opp and len(fr) > 14:
            a, b = fr[14]["participantFrames"][str(pid)], fr[14]["participantFrames"][str(opp["participantId"])]
            g["gd14"] = a["totalGold"] - b["totalGold"]
            g["cd14"] = a["minionsKilled"] + a["jungleMinionsKilled"] - b["minionsKilled"] - b["jungleMinionsKilled"]
            g["xd14"] = a["xp"] - b["xp"]
            a6, b6 = fr[6]["participantFrames"][str(pid)], fr[6]["participantFrames"][str(opp["participantId"])]
            g["lv6"] = a6["level"] - b6["level"]  # foto del minuto 6, como el aviso en vivo de companion.py
        mins = [e["timestamp"] / 60000 for x in fr for e in x["events"] if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid]
        g["d14"] = sum(t < 14 for t in mins); g["d25"] = sum(14 <= t < 25 for t in mins)
        if me["teamPosition"] in NOMBRE:  # sin jungla: no tiene "tu línea"
            g["rio14"] = sum(pasado(zone(e["position"]["x"], e["position"]["y"], me["teamId"]), NOMBRE[me["teamPosition"]])
                             for x in fr for e in x["events"]
                             if e["type"] == "CHAMPION_KILL" and e["victimId"] == pid and e["timestamp"] < 14 * 60000)
    games.append(g)
games.sort(key=lambda g: g["t"])
assert games, "sin partidas"
# sin config: el pool son tus 3 campeones más jugados
POOL = (CFG.get("pool") or [c for c, _ in Counter(g["champ"] for g in games).most_common(3)])

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


# referencias de todas tus partidas (no números fijos de cozi)
gan = [g for g in games if g["gd14"] is not None and g["gd14"] >= 0]
CONV = sum(g["win"] for g in gan) / len(gan) if gan else None
D14V = media([g for g in games if g["win"]], "d14")
RIO = [media([g for g in games if g["win"] == w], "rio14")[0] for w in (True, False)]

# (métrica, cómo se calcula, meta legible, prueba de la meta)
METRICAS = [
    ("Win rate", lambda rs: prop(rs, lambda r: r["win"]), "≥ 55% (semana 1), ≥ 58% después", lambda v: v >= .55),
    ("Oro ≥ 0 contra tu rival al 14", lambda rs: prop(rs, lambda r: None if r["gd14"] is None else r["gd14"] >= 0),
     "> 55%", lambda v: v > .55),
    ("WR cuando llegas al 14 con oro ≥ 0 (convertir)",
     lambda rs: prop([r for r in rs if r["gd14"] is not None and r["gd14"] >= 0], lambda r: r["win"]),
     "≥ 60%" + ("" if CONV is None else f" (todas tus partidas: {CONV:.0%})"), lambda v: v >= .6),
    ("Oro contra tu rival al 14 (media)", lambda rs: media(rs, "gd14"), "≥ 0", lambda v: v >= 0),
    ("CS contra tu rival al 14 (media)", lambda rs: media(rs, "cd14"), "≥ 0", lambda v: v >= 0),
    ("Muertes antes del 14", lambda rs: media(rs, "d14"), f"referencia: {D14V[0]} en tus victorias",
     None if D14V[1] is None else lambda v: v <= D14V[1]),
    ("Muertes antes del 14 pasado el río (río, mitad rival de tu línea o jungla rival)", lambda rs: media(rs, "rio14"),
     f"monitor de la regla de prioridad 1; en tus partidas, V {RIO[0]} contra D {RIO[1]}", None),
    ("Muertes del 14 al 25", lambda rs: media(rs, "d25"), "≤ 2", lambda v: v <= 2),
] + ([] if not M10 else [
    (f"{M10['campeon']}: partidas con {M10['minimo']}+ minions de línea al 10",
     # con ~4 por cada 20 partidas la marca es ruido: solo se marca con n ≥ 10 (revisión de DeepSeek)
     lambda rs: (lambda t: t if sum(r["lm10"] is not None for r in rs) >= 10 else (t[0], None))(
         prop(rs, lambda r: None if r["lm10"] is None else r["lm10"] >= M10["minimo"])),
     "> 50%, marca solo con n ≥ 10" + (f" ({M10['nota']})" if M10.get("nota") else ""), lambda v: v > .5),
]) + [
    ("Partidas con ≥ 1 control ward", lambda rs: prop(rs, lambda r: r["cw"] >= 1),
     "monitor sin meta: no baja los ganks ni sube el WR (wards.py)", None),
    (f"Partidas con el pool ({', '.join(POOL)})", lambda rs: prop(rs, lambda r: r["champ"] in POOL), "> 80%",
     lambda v: v > .8),
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


def racha(games):
    """Si 3+ de tus últimas 5 partidas llegan al 14 con oro < 0: 2 sugerencias medibles sacadas de tus partidas
    con oro < 0 al 14 (XP @14 y nivel al 6). Devuelve [] si no hay racha."""
    ult = games[-5:]
    k = sum(g["gd14"] is not None and g["gd14"] < 0 for g in ult)
    if k < 3: return []
    abajo = [g for g in games if g["gd14"] is not None and g["gd14"] < 0]

    def wr(rs):
        lo, hi = wilson(sum(r["win"] for r in rs), len(rs))
        return f"{sum(r['win'] for r in rs) / len(rs):.0%} ({lo:.0%}–{hi:.0%}, n={len(rs)})" if rs else "-"

    def pista(a, b):  # con intervalos cruzados la diferencia puede ser azar
        (la, ha), (lb, hb) = (wilson(sum(r["win"] for r in x), len(x)) for x in (a, b))
        return " (pista: los intervalos se cruzan)" if a and b and la <= hb and lb <= ha else ""

    def ult5(key, fmt):
        vs = [g[key] for g in ult if g[key] is not None]
        return f"tus últimas 5: media {fmt.format(st.mean(vs))}" if vs else "tus últimas 5: sin dato"

    lineas = [f"Llegaste al 14 con oro < 0 contra tu rival en {k} de tus últimas 5 partidas."]
    xs = sorted(g["xd14"] for g in abajo if g["xd14"] is not None)
    if xs:
        m = round(st.median(xs))
        a = [g for g in abajo if g["xd14"] is not None and g["xd14"] >= m]
        b = [g for g in abajo if g["xd14"] is not None and g["xd14"] < m]
        lineas.append(f"- XP al 14 a {m:+d} o mejor contra tu rival (la mediana de tus partidas con oro < 0): ahí ganas "
                      f"{wr(a)}, debajo {wr(b)}{pista(a, b)}; {ult5('xd14', '{:+.0f}')}.")
    ls = [g for g in abajo if g["lv6"] is not None]
    if ls:
        a, b = [g for g in ls if g["lv6"] >= 0], [g for g in ls if g["lv6"] < 0]
        lineas.append(f"- Al minuto 6 con nivel igual o arriba de tu rival: con oro < 0 al 14 ganas {wr(a)}, abajo "
                      f"{wr(b)}{pista(a, b)}; {ult5('lv6', '{:+.1f}')} niveles. No tradees hasta igualar.")
    return lineas


if rs := racha(games):
    print("\n## Racha de oro bajo al 14\n\n" + "\n".join(rs))

print(f"\n## Partida por partida (más reciente primero)\n\n| Fecha | Campeón | | Oro @14 | CS @14 | Muertes <14 | Muertes 14–25 | Control wards |\n|---|---|---|---|---|---|---|---|")
f = lambda v, fmt="{:+d}": "-" if v is None else fmt.format(v)
for g in reversed(rec):
    print(f"| {fecha(g):%m-%d %H:%M} | {g['champ']}{'' if g['champ'] in POOL else ' (fuera del pool)'} | "
          f"{'V' if g['win'] else 'D'} | {f(g['gd14'])} | {f(g['cd14'])} | {f(g['d14'], '{}')} | {f(g['d25'], '{}')} | {g['cw']} |")
