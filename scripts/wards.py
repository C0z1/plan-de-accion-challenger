"""Control wards: ¿la regla "1 control ward en cada regreso" tiene respaldo en los datos?
Tú tienes muy pocas partidas con control ward, así que también se mide en los otros jugadores de línea (top/mid/bot,
sin jungla ni support) de tus mismas partidas: control ward antes del 14 contra muertes por gank antes del 14 y WR,
a igual oro @14 contra su rival de línea.
Uso: python scripts/wards.py > datos/analisis-wards-AAAA-MM-DD.md"""
import json, os, math, pathlib, sys

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE", "TOP", "BOTTOM"}
C14 = 14 * 60000


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
    return f"{sum(xs) / len(xs):.2f}" if xs else "-"


def ganks(ev, pid, jr):
    """Muertes de pid antes del 14 en las que mata o asiste el jungla rival."""
    return sum(1 for e in ev if e["type"] == "CHAMPION_KILL" and e["timestamp"] < C14 and e["victimId"] == pid
               and jr in {e["killerId"], *e.get("assistingParticipantIds", [])})
assert ganks([{"type": "CHAMPION_KILL", "timestamp": 1, "victimId": 1, "killerId": 2, "assistingParticipantIds": [9]},
              {"type": "CHAMPION_KILL", "timestamp": 1, "victimId": 1, "killerId": 2}], 1, 9) == 1


yo, otros = [], []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 900: continue  # 15+ min, mismo corte que early.py y muertes6.py
    fr = json.loads(tf.read_text())["info"]["frames"]
    if len(fr) <= 14: continue
    ev = [e for f in fr for e in f["events"]]
    ps = m["participants"]
    for p in ps:
        rol = p["teamPosition"]
        if rol not in LINEA: continue
        opp = next((q for q in ps if q["teamPosition"] == rol and q["teamId"] != p["teamId"]), None)
        jr = next((q["participantId"] for q in ps if q["teamPosition"] == "JUNGLE" and q["teamId"] != p["teamId"]), None)
        if not opp or not jr: continue
        pid = p["participantId"]
        cw14 = sum(1 for e in ev if e["type"] == "WARD_PLACED" and e.get("wardType") == "CONTROL_WARD"
                   and e.get("creatorId") == pid and e["timestamp"] < C14)
        pf = fr[14]["participantFrames"]
        g = dict(win=p["win"], rol=rol, cw=p["challenges"].get("controlWardsPlaced", 0), cw14=cw14,
                 gank=ganks(ev, pid, jr), gd14=pf[str(pid)]["totalGold"] - pf[str(opp["participantId"])]["totalGold"])
        (yo if p["puuid"] == puuid else otros).append(g)
assert yo and otros

print(f"# Control wards ({len(yo)} partidas tuyas de 15+ min en top/mid/bot; {len(otros)} jugadores de línea ajenos)\n")
print("## Tú\n")
print("| Control wards en la partida | Partidas | WR | Muertes por gank <14 |\n|---|---|---|---|")
for et, f in (("0", lambda g: g["cw"] == 0), ("1+", lambda g: g["cw"] >= 1)):
    gs = [g for g in yo if f(g)]
    print(f"| {et} | {len(gs)} | {wr(gs)} | {media([g['gank'] for g in gs])} |")
print(f"\nCon al menos 1 control ward antes del 14: {sum(g['cw14'] >= 1 for g in yo)} de {len(yo)}.\n")

print("## Los otros jugadores de línea de tus partidas (top/mid/bot, sin ti)\n")
k1 = sum(g["cw"] >= 1 for g in otros); k14 = sum(g["cw14"] >= 1 for g in otros)
print(f"Con 1+ control ward en la partida: {k1}/{len(otros)} = {k1 / len(otros):.0%}; antes del 14: {k14}/{len(otros)} = {k14 / len(otros):.0%}.\n")
print("| Control wards antes del 14 | Jugadores | WR | Muertes por gank <14 | % con 1+ muerte por gank <14 |\n|---|---|---|---|---|")
for et, f in (("0", lambda g: g["cw14"] == 0), ("1", lambda g: g["cw14"] == 1), ("2+", lambda g: g["cw14"] >= 2)):
    gs = [g for g in otros if f(g)]
    k = sum(g["gank"] >= 1 for g in gs); lo, hi = wilson(k, len(gs))
    print(f"| {et} | {len(gs)} | {wr(gs)} | {media([g['gank'] for g in gs])} | {k / len(gs):.0%} ({lo:.0%}–{hi:.0%}) |")

print("\n### A igual oro @14 contra su rival de línea (control ward antes del 14: 0 contra 1+)\n")
print("| Oro @14 | WR con 0 | WR con 1+ | Gank <14 con 0 | Gank <14 con 1+ |\n|---|---|---|---|---|")
for et, lo_, hi_ in (("≤ −1000", -1e9, -1000), ("−1000 a 0", -1000, 0), ("0 a +1000", 0, 1000), ("≥ +1000", 1000, 1e9)):
    b = [g for g in otros if lo_ <= g["gd14"] < hi_]
    c0 = [g for g in b if g["cw14"] == 0]; c1 = [g for g in b if g["cw14"] >= 1]
    print(f"| {et} | {wr(c0)} | {wr(c1)} | {media([g['gank'] for g in c0])} | {media([g['gank'] for g in c1])} |")

print("\n### Por rol (control ward antes del 14: 0 contra 1+)\n")
print("| Rol | WR con 0 | WR con 1+ | Gank <14 con 0 | Gank <14 con 1+ |\n|---|---|---|---|---|")
for rol in ("TOP", "MIDDLE", "BOTTOM"):
    b = [g for g in otros if g["rol"] == rol]
    c0 = [g for g in b if g["cw14"] == 0]; c1 = [g for g in b if g["cw14"] >= 1]
    print(f"| {rol} | {wr(c0)} | {wr(c1)} | {media([g['gank'] for g in c0])} | {media([g['gank'] for g in c1])} |")
