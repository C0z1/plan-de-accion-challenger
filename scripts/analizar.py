"""Resume datos/raw/*.json en estadísticas agregadas. Uso: python scripts/analizar.py > datos/analisis-AAAA-MM-DD.md"""
import json, os, pathlib, statistics as st
from collections import defaultdict
from datetime import datetime, timedelta, timezone

RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
MX = timezone(timedelta(hours=-6))  # hora del centro de México

rows = []
for f in RAW.glob("*_*.json"):
    m = json.loads(f.read_text())["info"]
    if m["gameDuration"] < 300 or m.get("gameEndedInEarlySurrender"):  # remakes fuera
        continue
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    c = me.get("challenges", {})
    mins = m["gameDuration"] / 60
    rows.append(dict(
        t=m["gameCreation"], win=me["win"], champ=me["championName"], pos=me["teamPosition"] or "?",
        k=me["kills"], d=me["deaths"], a=me["assists"],
        cspm=(me["totalMinionsKilled"] + me["neutralMinionsKilled"]) / mins,
        vis=me["visionScore"] / mins, kp=c.get("killParticipation", 0), dmg=c.get("teamDamagePercentage", 0),
        lane=c.get("laningPhaseGoldExpAdvantage"), solo=c.get("soloKills", 0),
        gd=(me["goldEarned"] - opp["goldEarned"]) if opp else None,
        opp=opp["championName"] if opp else "?", mins=mins,
    ))
rows.sort(key=lambda r: r["t"])
assert rows, "sin partidas"


def wr(rs): return f"{sum(r['win'] for r in rs) / len(rs):.0%}" if rs else "-"
def avg(rs, k):
    v = [r[k] for r in rs if r[k] is not None]
    return st.mean(v) if v else 0
def line(name, rs):
    kda = (sum(r["k"] for r in rs) + sum(r["a"] for r in rs)) / max(1, sum(r["d"] for r in rs))
    return (f"| {name} | {len(rs)} | {wr(rs)} | {kda:.2f} | {avg(rs,'d'):.1f} | {avg(rs,'cspm'):.1f} | "
            f"{avg(rs,'kp'):.0%} | {avg(rs,'dmg'):.0%} | {avg(rs,'vis'):.2f} | {avg(rs,'gd'):+.0f} |")
HDR = "| | Partidas | WR | KDA | Muertes | CS/min | KP | % daño | Visión/min | Oro vs rival |\n|---|---|---|---|---|---|---|---|---|---|"


def table(title, key, min_n=1):
    g = defaultdict(list)
    for r in rows: g[key(r)].append(r)
    print(f"\n## {title}\n\n{HDR}")
    for k, rs in sorted(g.items(), key=lambda x: -len(x[1])):
        if len(rs) >= min_n: print(line(k, rs))


first, last = [datetime.fromtimestamp(rows[i]["t"] / 1000, MX).date() for i in (0, -1)]
print(f"# Análisis Solo/Duo: {len(rows)} partidas ({first} a {last})\n\n{HDR}")
print(line("Total", rows))
print(line("Últimas 20", rows[-20:]))
print(line("Últimas 50", rows[-50:]))
print(line("Victorias", [r for r in rows if r["win"]]))
print(line("Derrotas", [r for r in rows if not r["win"]]))
table("Por rol", lambda r: r["pos"])
table("Por campeón (3+ partidas)", lambda r: r["champ"], 3)

# Sesiones: partidas separadas por menos de 90 min
sess, cur = [], [rows[0]]
for a, b in zip(rows, rows[1:]):
    if b["t"] - a["t"] > 90 * 60_000: sess.append(cur); cur = []
    cur.append(b)
sess.append(cur)
print(f"\n## Sesiones ({len(sess)}, promedio {st.mean(len(s) for s in sess):.1f} partidas)\n")
by_idx = defaultdict(list)
for s in sess:
    for i, r in enumerate(s): by_idx[min(i + 1, 6)].append(r)
print("| Partida # en la sesión | Partidas | WR |\n|---|---|---|")
for i in sorted(by_idx): print(f"| {i if i < 6 else '6+'} | {len(by_idx[i])} | {wr(by_idx[i])} |")

after = defaultdict(list)
for s in sess:
    for i in range(1, len(s)):
        streak = 2 if i >= 2 and not s[i-1]["win"] and not s[i-2]["win"] else (0 if s[i-1]["win"] else 1)
        after[streak].append(s[i])
print("\n| Después de… | Partidas | WR |\n|---|---|---|")
for k, lbl in [(0, "una victoria"), (1, "una derrota"), (2, "2+ derrotas seguidas")]:
    print(f"| {lbl} | {len(after[k])} | {wr(after[k])} |")

hours = defaultdict(list)
for r in rows:
    h = datetime.fromtimestamp(r["t"] / 1000, MX).hour
    hours[f"{h // 4 * 4:02d}-{h // 4 * 4 + 4:02d}h"].append(r)
print("\n## Horario (hora de México)\n\n| Bloque | Partidas | WR |\n|---|---|---|")
for k in sorted(hours): print(f"| {k} | {len(hours[k])} | {wr(hours[k])} |")

durs = {"<25 min": [r for r in rows if r["mins"] < 25], "25-32": [r for r in rows if 25 <= r["mins"] < 32],
        "32+": [r for r in rows if r["mins"] >= 32]}
print("\n## Duración\n\n| Duración | Partidas | WR |\n|---|---|---|")
for k, rs in durs.items(): print(f"| {k} | {len(rs)} | {wr(rs)} |")

lane = [r for r in rows if r["lane"] is not None]
ahead = [r for r in lane if r["lane"] > 0]; behind = [r for r in lane if r["lane"] <= 0]
print(f"\n## Fase de líneas\n\nGanó la fase de líneas (ventaja de oro y XP): {len(ahead)}/{len(lane)} "
      f"({len(ahead)/max(1,len(lane)):.0%}). WR con ventaja: {wr(ahead)}. WR sin ventaja: {wr(behind)}.")
print(f"Kills en solitario por partida: {avg(rows,'solo'):.2f}")

opp = defaultdict(list)
for r in rows: opp[r["opp"]].append(r)
print("\n## Rivales de línea más frecuentes (3+)\n\n| Rival | Partidas | WR |\n|---|---|---|")
for k, rs in sorted(opp.items(), key=lambda x: -len(x[1]))[:15]:
    if len(rs) >= 3: print(f"| {k} | {len(rs)} | {wr(rs)} |")
