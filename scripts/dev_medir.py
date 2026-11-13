"""Solo desarrollo (no va en el .exe): capturas de cada vista con Edge headless y el tiempo del primer pintado de Inicio
(plan de reinvención, 0.18). Levanta un Racha propio sin ventana ni franja (--no-abrir) sobre tus datos.
  python scripts/dev_medir.py [carpeta]   (por defecto datos/salud/estela)"""
import pathlib, re, subprocess, sys, time
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import ventana

VISTAS = ("inicio", "draft", "companion", "envivo", "perfil", "partidas", "campeones", "errores", "ajustes")
TAMANOS = ((1440, 1024), (1100, 720))


def edge(*args, timeout=60):
    return subprocess.run([ventana.edge(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", *args],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    out = pathlib.Path(argv[0] if argv else pathlib.Path(__file__).resolve().parent.parent / "datos" / "salud" / "estela").resolve(); out.mkdir(parents=True, exist_ok=True)  # absoluta: Edge resuelve otra carpeta
    srv = subprocess.Popen([sys.executable, str(pathlib.Path(__file__).with_name("companion_web.py")), "--no-abrir"], stdout=subprocess.PIPE, text=True)
    try:
        url = srv.stdout.readline().strip(); time.sleep(4)  # que refrescar() calcule el rendimiento
        for w, h in TAMANOS:
            for v in VISTAS:
                edge(f"--window-size={w},{h}", f"--screenshot={out / f'{v}-{w}.png'}", "--virtual-time-budget=4000", f"{url}#{v}")
        ms = []
        for _ in range(3):
            dom = edge("--window-size=1440,1024", "--virtual-time-budget=8000", "--dump-dom", f"{url}#inicio&medir").stdout
            if m := re.search(r'data-medida="(\d+)"', dom): ms.append(int(m[1]))
        print(f"capturas en {out}; primer pintado de Inicio (ms): {ms}")
        return ms
    finally: srv.terminate()


if __name__ == "__main__": main()
