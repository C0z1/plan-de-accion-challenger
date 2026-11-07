"""¿Por qué un campeón no convierte la línea ganada? En partidas con oro >= 0 contra tu rival al 14,
compara por campeón (y V contra D del campeón elegido): cómo crece tu ventaja del 14 al 20, el oro del equipo,
muertes y takedowns del 14 al 25, torres, objetivos y dónde estás en el mapa del 15 al 24.
Uso: python scripts/convertir.py [Campeón] > datos/analisis-convertir-AAAA-MM-DD.md   (por defecto Ekko)"""
import json, math, pathlib, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
FOCO = sys.argv[1] if len(sys.argv) > 1 else "Ekko"


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


def zone(x, y, team):  # misma función que scripts/timeline.py
    own = (x + y < 14800) == (team == 100)
    if x + y < 5600 or x + y > 24000: return "base propia" if own else "base rival"
    if abs(x - y) < 1600: z = "mid"
    elif x < 2300 or y > 12500: z = "top"
    elif y < 2300 or x > 12500: z = "bot"
    elif abs(x + y - 14800) < 1500: return "río"
    else: z = "jungla"
    return f"{z} ({'lado propio' if own else 'lado rival'})"
assert zone(7400, 7400, 100) == "mid (lado rival)" and zone(1000, 1000, 100) == "base propia"


games = []
for tf in (RAW / "timeline").glob("LA1_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 300: continue  # remakes
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    fr = json.loads(tf.read_text())["info"]["frames"]
    if not opp or len(fr) <= 20: continue  # hace falta el minuto 20
    pid, oid, team = me["participantId"], opp["participantId"], me["teamId"]
    pf = lambda mn, i: fr[mn]["participantFrames"][str(i)]
    oro = lambda mn, i: pf(mn, i)["totalGold"]
    cs = lambda mn, i: pf(mn, i)["minionsKilled"] + pf(mn, i)["jungleMinionsKilled"]
    eq = lambda mn: sum(oro(mn, p["participantId"]) * (1 if p["teamId"] == team else -1) for p in ps)
    kills = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL" and 14 <= e["timestamp"] / 60000 < 25]
    zonas = Counter(zone(pf(mn, pid)["position"]["x"], pf(mn, pid)["position"]["y"], team).split(" (")[0]
                    for mn in range(15, min(25, len(fr))))
    ch = me["challenges"]
    games.append(dict(
        win=me["win"], champ=me["championName"], rol=me["teamPosition"],
        gd14=oro(14, pid) - oro(14, oid), gd20=oro(20, pid) - oro(20, oid),
        cs20=cs(20, pid) - cs(20, oid), tg14=eq(14), tg20=eq(20),
        d1425=sum(e["victimId"] == pid for e in kills),
        td1425=sum(pid == e["killerId"] or pid in e.get("assistingParticipantIds", []) for e in kills),
        torres=me.get("turretTakedowns", 0),
        drag=ch.get("dragonTakedowns", 0), her=ch.get("riftHeraldTakedowns", 0),
        edif=me.get("damageDealtToBuildings", 0), kp=ch.get("killParticipation", 0),
        en_linea=zonas["mid" if me["teamPosition"] == "MIDDLE" else me["teamPosition"].lower()] / max(1, sum(zonas.values())),
        dur=m["gameDuration"] / 60))
assert games, "sin timelines"
todas = games
games = [g for g in todas if g["gd14"] >= 0]  # solo línea ganada

FILAS = [("Tu oro vs rival @14", "gd14", "+.0f"), ("Tu oro vs rival @20", "gd20", "+.0f"),
         ("CS vs rival @20", "cs20", "+.1f"), ("Oro del equipo @14", "tg14", "+.0f"), ("Oro del equipo @20", "tg20", "+.0f"),
         ("Muertes 14–25", "d1425", ".2f"), ("Takedowns 14–25", "td1425", ".2f"),  ("Torres (takedowns)", "torres", ".1f"), ("Dragones (takedowns)", "drag", ".1f"), ("Heraldos (takedowns)", "her", ".2f"),
         ("Daño a edificios", "edif", ".0f"), ("KP", "kp", ".0%"), ("Minutos 15–24 en tu línea", "en_linea", ".0%"),
         ("Duración (min)", "dur", ".1f")]
avg = lambda rs, k: st.mean([r[k] for r in rs]) if rs else float("nan")
crece = lambda rs: f"{sum(r['gd20'] > r['gd14'] for r in rs)}/{len(rs)}"

print(f"# Convertir la línea ganada: {FOCO} contra el resto ({len(games)} partidas con oro >= 0 al 14 y 20+ min)\n")
print("Intervalos Wilson 95%. Oro vs rival = tu oro menos el de tu rival de línea. "
      "\"En tu línea\" = minutos 15–24 en los que tu posición estaba en la línea de tu rol (cualquier lado).\n")

top = [c for c, n in Counter(g["champ"] for g in games).most_common() if n >= 8]
print("## Por campeón (8+ partidas con la línea ganada)\n")
print("| | " + " | ".join(top) + " | Todos |\n|---|" + "---|" * (len(top) + 1))
grupos = [[g for g in games if g["champ"] == c] for c in top] + [games]
print("| Convertir (WR) | " + " | ".join(wr(rs) for rs in grupos) + " |")
print("| Ventaja crece del 14 al 20 | " + " | ".join(crece(rs) for rs in grupos) + " |")
for lbl, k, f in FILAS:
    print(f"| {lbl} | " + " | ".join(f"{avg(rs, k):{f}}" for rs in grupos) + " |")

print("\n## Con la línea ganada contra perdida (todas las partidas de 20+ min)\n\n"
      "| Campeón | Oro >= 0 al 14 | Oro < 0 al 14 | % línea ganada |\n|---|---|---|---|")
for c in top + ["Todos"]:
    rs = [g for g in todas if c in ("Todos", g["champ"])]; ok = [g for g in rs if g["gd14"] >= 0]
    print(f"| {c} | {wr(ok)} | {wr([g for g in rs if g['gd14'] < 0])} | {len(ok) / len(rs):.0%} |")

foco = [g for g in games if g["champ"] == FOCO]
W, L = [g for g in foco if g["win"]], [g for g in foco if not g["win"]]
print(f"\n## {FOCO}: victorias contra derrotas con la línea ganada\n\n| | Victorias | Derrotas |\n|---|---|---|")
print(f"| Partidas | {len(W)} | {len(L)} |\n| Ventaja crece del 14 al 20 | {crece(W)} | {crece(L)} |")
for lbl, k, f in FILAS:
    print(f"| {lbl} | {avg(W, k):{f}} | {avg(L, k):{f}} |")

print(f"\n## {FOCO}: WR según lo que pasa del 14 al 20\n\n| Condición | WR (IC 95%) |\n|---|---|")
for lbl, cond in [("Tu ventaja crece del 14 al 20", lambda g: g["gd20"] > g["gd14"]),
                  ("Tu ventaja se encoge del 14 al 20", lambda g: g["gd20"] <= g["gd14"]),
                  ("Equipo >= 0 al 20", lambda g: g["tg20"] >= 0), ("Equipo < 0 al 20", lambda g: g["tg20"] < 0),
                  ("0–2 muertes del 14 al 25", lambda g: g["d1425"] <= 2), ("3+ muertes del 14 al 25", lambda g: g["d1425"] >= 3),
                  ("En tu línea >= 50% del 15 al 24", lambda g: g["en_linea"] >= .5),
                  ("En tu línea < 50% del 15 al 24", lambda g: g["en_linea"] < .5)]:
    print(f"| {lbl} | {wr([g for g in foco if cond(g)])} |")
