"""Con la línea perdida al 14, ¿cómo muere tu rival de línea antes del 14 y cuánto de eso es tuyo?
Clasifica cada muerte de tu rival (tú solo, tú + jungla, tú + otro, sin ti), dónde fue (en tu línea o fuera) y si
te costó morir en los 20 s siguientes; reparte la XP de "muere él" de xp.py entre tuya y ajena, y prueba la
sensibilidad de "muerto" contando también el minuto siguiente a tu muerte (preguntas de DeepSeek, iteración 9).
Uso: python scripts/castigo.py > datos/analisis-castigo-AAAA-MM-DD.md"""
import json, os, math, pathlib, statistics as st, sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
RAW = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
puuid = json.loads((RAW / "perfil.json").read_text())["account"]["puuid"]
LINEA = {"MIDDLE": "mid", "TOP": "top", "BOTTOM": "bot", "UTILITY": "bot"}
TIPOS = ["tú solo", "tú + jungla", "tú + otro", "sin ti"]


def wilson(k, n, z=1.96):  # misma función que scripts/linea.py
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
assert zone(7400, 7400, 100) == "mid (lado rival)"


def tipo(e, pid, jg):
    """Quién mató a tu rival: tú solo, tú con tu jungla, tú con otro aliado, o sin ti."""
    quien = {e["killerId"], *e.get("assistingParticipantIds", [])}
    if pid not in quien: return "sin ti"
    if quien == {pid}: return "tú solo"
    return "tú + jungla" if jg in quien else "tú + otro"
assert tipo({"killerId": 3}, 3, 2) == "tú solo"
assert tipo({"killerId": 2, "assistingParticipantIds": [3]}, 3, 2) == "tú + jungla"
assert tipo({"killerId": 4, "assistingParticipantIds": [3]}, 3, 2) == "tú + otro"
assert tipo({"killerId": 2}, 3, 2) == "sin ti"

games = []
for tf in (RAW / "timeline").glob("*_*.json"):
    mf = RAW / tf.name
    if not mf.exists(): continue
    m = json.loads(mf.read_text())["info"]
    if m["gameDuration"] < 1200: continue  # 20+ min reales (el filtro por frames de linea.py deja pasar 19:xx)
    ps = m["participants"]
    me = next(p for p in ps if p["puuid"] == puuid)
    if me["teamPosition"] not in LINEA: continue  # sin jungla
    opp = next((p for p in ps if p["teamPosition"] == me["teamPosition"] and p["teamId"] != me["teamId"]), None)
    jg = next((p["participantId"] for p in ps if p["teamPosition"] == "JUNGLE" and p["teamId"] == me["teamId"]), None)
    if not opp: continue
    fr = json.loads(tf.read_text())["info"]["frames"]
    pid, oid, linea = me["participantId"], opp["participantId"], LINEA[me["teamPosition"]]
    pf = lambda mn, i, k: fr[mn]["participantFrames"][str(i)][k]
    kills = [e for f in fr for e in f["events"] if e["type"] == "CHAMPION_KILL" and e["timestamp"] <= 14 * 60000]
    mias = [e["timestamp"] for e in kills if e["victimId"] == pid]
    suyas = []
    for e in kills:
        if e["victimId"] != oid: continue
        z = zone(e["position"]["x"], e["position"]["y"], me["teamId"])
        suyas.append(dict(t=e["timestamp"], tipo=tipo(e, pid, jg), linea=z.startswith(linea),
                          cambio=any(0 <= t - e["timestamp"] <= 20000 for t in mias)))
    # XP del minuto (tú − él) en los minutos 2–14 donde murió él y tú no: ¿tuya o ajena?
    xpm = lambda mn: (pf(mn, pid, "xp") - pf(mn - 1, pid, "xp")) - (pf(mn, oid, "xp") - pf(mn - 1, oid, "xp"))
    en = lambda ts, mn: any((mn - 1) * 60000 < t <= mn * 60000 for t in ts)
    xp_tuya = xp_ajena = muerto1 = muerto2 = 0.0
    for mn in range(2, 15):
        d = xpm(mn)
        if en(mias, mn): muerto1 += d
        if en(mias, mn) or en(mias, mn - 1): muerto2 += d  # sensibilidad: también el minuto siguiente
        if en(mias, mn): continue
        sm = [s for s in suyas if (mn - 1) * 60000 < s["t"] <= mn * 60000]
        if sm and any(s["tipo"] != "sin ti" for s in sm): xp_tuya += d
        elif sm: xp_ajena += d
    games.append(dict(win=me["win"], champ=me["championName"], suyas=suyas,
                      gd14=pf(14, pid, "totalGold") - pf(14, oid, "totalGold"),
                      xp_tuya=xp_tuya, xp_ajena=xp_ajena, muerto1=muerto1, muerto2=muerto2))
assert games, "sin timelines"

perd = [g for g in games if g["gd14"] < 0]
W, L = [g for g in perd if g["win"]], [g for g in perd if not g["win"]]
avg = lambda rs, f: st.mean([f(r) for r in rs]) if rs else float("nan")
cuenta = lambda g, c: sum(1 for s in g["suyas"] if c(s))
tuyas = lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti")

print(f"# Castigar a tu rival con la línea perdida ({len(perd)} líneas perdidas al 14 de {len(games)} partidas, 20+ min, sin jungla)\n")
print("Muertes de tu rival de línea antes del 14. **tú solo** = lo mataste sin asistencias; **tú + jungla** / **tú + otro** "
      "= participaste con tu jungla u otro aliado; **sin ti** = no participaste. **En tu línea** = el kill fue en tu línea "
      "(si no: río, jungla, otra línea). **Te costó** = moriste en los 20 s siguientes. Intervalos Wilson 95%.\n")

print("## Muertes de tu rival por partida (antes del 14), línea perdida\n\n| Tipo | Victorias | Derrotas | Diferencia |\n|---|---|---|---|")
for t in TIPOS:
    v, d = avg(W, lambda g: cuenta(g, lambda s: s["tipo"] == t)), avg(L, lambda g: cuenta(g, lambda s: s["tipo"] == t))
    print(f"| {t} | {v:.2f} | {d:.2f} | {v - d:+.2f} |")
v, d = avg(W, lambda g: len(g["suyas"])), avg(L, lambda g: len(g["suyas"]))
print(f"| **Total** | {v:.2f} | {d:.2f} | {v - d:+.2f} |")
v, d = avg(W, lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti" and s["linea"])), avg(L, lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti" and s["linea"]))
print(f"| contigo, en tu línea | {v:.2f} | {d:.2f} | {v - d:+.2f} |")
v, d = avg(W, lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti" and not s["linea"])), avg(L, lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti" and not s["linea"]))
print(f"| contigo, fuera de tu línea | {v:.2f} | {d:.2f} | {v - d:+.2f} |")

print("\n## La XP de \"muere él\" (xp.py): ¿cuánta es tuya?\n\n| | Victorias | Derrotas |\n|---|---|---|")
print(f"| XP en minutos donde murió con tu participación | {avg(W, lambda g: g['xp_tuya']):+.0f} | {avg(L, lambda g: g['xp_tuya']):+.0f} |")
print(f"| XP en minutos donde murió sin ti | {avg(W, lambda g: g['xp_ajena']):+.0f} | {avg(L, lambda g: g['xp_ajena']):+.0f} |")
print(f"| Minutos de tu muerte (como en xp.py) | {avg(W, lambda g: g['muerto1']):+.0f} | {avg(L, lambda g: g['muerto1']):+.0f} |")
print(f"| Minutos de tu muerte + el siguiente | {avg(W, lambda g: g['muerto2']):+.0f} | {avg(L, lambda g: g['muerto2']):+.0f} |")

print("\n## WR con la línea perdida según cuántas veces participas en matar a tu rival antes del 14\n\n| Condición | Línea perdida | Todas |\n|---|---|---|")
for lbl, c in [("0 kills tuyos sobre tu rival", lambda g: tuyas(g) == 0), ("1", lambda g: tuyas(g) == 1), ("2+", lambda g: tuyas(g) >= 2),
               ("al menos 1 tú solo", lambda g: cuenta(g, lambda s: s["tipo"] == "tú solo") >= 1),
               ("al menos 1 con tu jungla", lambda g: cuenta(g, lambda s: s["tipo"] == "tú + jungla") >= 1),
               ("al menos 1 que no te costó morir", lambda g: cuenta(g, lambda s: s["tipo"] != "sin ti" and not s["cambio"]) >= 1)]:
    print(f"| {lbl} | {wr([g for g in perd if c(g)])} | {wr([g for g in games if c(g)])} |")

todas = [s for g in perd for s in g["suyas"] if s["tipo"] != "sin ti"]
print(f"\n## Tus kills sobre tu rival con la línea perdida ({len(todas)})\n\n| Tipo | Kills | En tu línea | Te costó morir (20 s) |\n|---|---|---|---|")
for t in TIPOS[:3]:
    ks = [s for s in todas if s["tipo"] == t]
    if ks: print(f"| {t} | {len(ks)} | {sum(s['linea'] for s in ks) / len(ks):.0%} | {sum(s['cambio'] for s in ks) / len(ks):.0%} |")
mins = Counter(min(s["t"] // 60000, 13) // 3 for s in todas)
print("\nPor minuto: " + ", ".join(f"{3 * k}–{3 * k + 2}: {mins[k]}" for k in sorted(mins)) + " (el último tramo llega a 14).")

top = [c for c, n in Counter(g["champ"] for g in perd).most_common() if n >= 8]
print("\n## Por campeón, línea perdida (8+)\n\n| Campeón | Partidas | WR | Kills tuyos sobre el rival (V) | (D) | tú solo (V) | (D) | WR con 1+ kill tuyo | WR con 0 |\n|---|---|---|---|---|---|---|---|---|")
for c in top:
    rs = [g for g in perd if g["champ"] == c]; v, d = [g for g in rs if g["win"]], [g for g in rs if not g["win"]]
    solo = lambda g: cuenta(g, lambda s: s["tipo"] == "tú solo")
    print(f"| {c} | {len(rs)} | {wr(rs)} | {avg(v, tuyas):.2f} | {avg(d, tuyas):.2f} | {avg(v, solo):.2f} | {avg(d, solo):.2f} | "
          f"{wr([g for g in rs if tuyas(g)])} | {wr([g for g in rs if not tuyas(g)])} |")
