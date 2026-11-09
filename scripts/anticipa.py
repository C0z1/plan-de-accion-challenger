"""¿Tu media contra un rival (lo que muestra «Cuidado con <rival>» en champ select) anticipa la próxima partida contra él?
Para cada medida de draft.MEDIDAS y cada partida con 3+ otras contra el mismo rival y rol:
- LOO: media de las otras partidas contra el rival; temporal: solo las anteriores (lo que habrías visto ese día).
- r = correlación de (media del rival − media del rol) con (valor real − media del rol); la media del rol sale sin esa partida.
- p por permutación: barajar los rivales dentro del rol (2000 veces); Bonferroni ×5 medidas.
- MSE: error al predecir con la media del rival contra la media del rol (< 1 = el rival aporta).
Uso: python scripts/anticipa.py"""
import random
import statistics as st
from collections import defaultdict
import draft

N_PERM, MIN_OTRAS = 2000, 3


def pares(gs, campo, temporal):
    """[(predicción por rival − rol, real − rol, error rival², error rol²)] para cada partida con MIN_OTRAS+ otras."""
    por, rol = defaultdict(list), defaultdict(list)
    for g in gs: por[(g["_opp"], g["pos"])].append(g); rol[g["pos"]].append(g[campo])
    out = []
    for (_, pos), rs in por.items():
        for g in rs:
            otras = [r[campo] for r in rs if r is not g and (not temporal or r["t"] < g["t"])]
            if len(otras) < MIN_OTRAS: continue
            base = (sum(rol[pos]) - g[campo]) / (len(rol[pos]) - 1)
            m = st.mean(otras)
            out.append((m - base, g[campo] - base, (g[campo] - m) ** 2, (g[campo] - base) ** 2))
    return out


def r_de(ps):
    if len(ps) < 3: return None
    x, y = [p[0] for p in ps], [p[1] for p in ps]
    try: return st.correlation(x, y)
    except st.StatisticsError: return None


def medir(campo, temporal, rnd):
    gs = [dict(g, _opp=g["opp"]) for g in draft.games if g.get(campo) is not None and g["opp"] != "?"]
    ps = pares(gs, campo, temporal); r = r_de(ps)
    if r is None: return dict(n=len(ps), r=None, p=None, mse=None)
    mayores = 0
    for _ in range(N_PERM):
        for pos in {g["pos"] for g in gs}:
            idx = [i for i, g in enumerate(gs) if g["pos"] == pos]; ops = [gs[i]["opp"] for i in idx]; rnd.shuffle(ops)
            for i, o in zip(idx, ops): gs[i]["_opp"] = o
        rp = r_de(pares(gs, campo, temporal))
        mayores += rp is not None and rp >= r
    return dict(n=len(ps), r=round(r, 2), p=round((mayores + 1) / (N_PERM + 1), 3),
                mse=round(sum(p[2] for p in ps) / max(1e-9, sum(p[3] for p in ps)), 2))


def main():
    rnd = random.Random(6)
    print("# ¿Tu media contra un rival anticipa la próxima partida contra él?\n")
    print(f"Partidas con {MIN_OTRAS}+ otras contra el mismo rival y rol. r: correlación (rival − rol) con (real − rol); "
          f"p: permutación de rivales dentro del rol ({N_PERM}), una cola; p×5: Bonferroni; MSE: error con la media del rival / con la del rol.\n")
    print("| Medida | Método | n | r | p | p×5 | MSE rival/rol |\n|---|---|---|---|---|---|---|")
    for k, campo in draft.MEDIDAS.items():
        for temporal in (False, True):
            m = medir(campo, temporal, rnd)
            p5 = min(1, m["p"] * 5) if m["p"] is not None else None
            print(f"| {k} | {'temporal' if temporal else 'LOO'} | {m['n']} | {m['r']} | {m['p']} | "
                  f"{round(p5, 3) if p5 is not None else None} | {m['mse']} |")


if __name__ == "__main__":
    main()
