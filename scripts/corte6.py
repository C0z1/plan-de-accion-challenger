"""¿Con qué promedio de nivel al 6 contra un rival conviene subir la regla del 6 al frente en champ select?
Leave-one-out: para cada partida, la media de nivel6 en tus OTRAS partidas (3+) contra ese rival en ese rol
(lo que vería draft.ficha() antes de esa partida) contra lo que pasó en ella: abajo al 6 y WR.
Uso: python scripts/corte6.py"""
from collections import defaultdict
import draft

gs = [g for g in draft.games if g.get("nivel6") is not None and g["opp"] != "?"]
por = defaultdict(list)
for g in gs: por[(g["opp"], g["pos"])].append(g)
filas = [(sum(r["nivel6"] for r in rs if r is not g) / (len(rs) - 1), g) for rs in por.values() if len(rs) >= 4 for g in rs]


def tasa(rs, f):
    k = sum(f(g) for g in rs); lo, hi = draft.wilson(k, len(rs))
    return f"{k / len(rs):.0%} ({lo:.0%}–{hi:.0%})" if rs else "-"


print(f"# Corte de la regla del 6: {len(filas)} partidas con 3+ otras contra el mismo rival y rol\n")
print(f"Abajo al 6 en todas ellas: {tasa([g for _, g in filas], lambda g: g['nivel6'] < 0)}\n")
print("| Media de las otras < corte | n sí | Abajo al 6 (sí) | WR (sí) | n no | Abajo al 6 (no) | WR (no) |\n|---|---|---|---|---|---|---|")
for c in (0, -0.1, -0.2, -0.3, -0.5):
    a = [g for m, g in filas if m < c]; b = [g for m, g in filas if m >= c]
    print(f"| {c:+.1f} | {len(a)} | {tasa(a, lambda g: g['nivel6'] < 0)} | {tasa(a, lambda g: g['win'])} "
          f"| {len(b)} | {tasa(b, lambda g: g['nivel6'] < 0)} | {tasa(b, lambda g: g['win'])} |")
