"""Solo desarrollo (no va en el .exe): dibuja la franja real con una partida grabada, para verla encima del juego o el escritorio.
  python scripts/dev_franja.py datos/vivo/20261109-175517.jsonl                 recorre la partida (cada foto, 1 s)
  python scripts/dev_franja.py <archivo> --minuto 18:58 [--aviso "texto"]       se queda en ese minuto (peor ancho, D9)
  python scripts/dev_franja.py <archivo> --segundos 30                          cuánto dura abierta (por defecto, toda la partida)"""
import argparse, pathlib, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import overlay, replay


def cuadro(rs, minuto):
    """La foto más cercana al minuto «MM:SS»."""
    m, s = (int(x) for x in minuto.split(":"))
    return min(rs, key=lambda r: abs(r["t"] - (m * 60 + s)))


def main(argv=None):
    a = argparse.ArgumentParser(); a.add_argument("archivo"); a.add_argument("--minuto"); a.add_argument("--aviso"); a.add_argument("--segundos", type=float)
    a = a.parse_args(argv)
    rs = [r for r in replay.repetir(replay.cargar(a.archivo)) if r["meta"]]
    fijo, inicio = cuadro(rs, a.minuto) if a.minuto else None, time.time()
    fin = inicio + (a.segundos or (30 if fijo else len(rs)))

    def leer():
        r = fijo or rs[min(len(rs) - 1, int(time.time() - inicio))]
        aviso = {"corto": a.aviso, "franja": inicio} if a.aviso else None
        return {"fase": "InProgress", "meta": {**r["meta"], "recibido": time.time()}, "ajustes": {}, "aviso": aviso}

    import companion_web
    overlay.correr(leer, lambda: time.time() < fin, icono=companion_web.imagen)


if __name__ == "__main__": main()
