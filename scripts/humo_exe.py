"""Humo de la build: arranca Companion.exe --demo --no-abrir, busca su puerto y pide /api/estado.
  python scripts/humo_exe.py [ruta.exe]   sale con 0 si responde JSON con 'fase'."""
import json, pathlib, re, subprocess, sys, time, urllib.request

exe = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / "Companion.exe")
p = subprocess.Popen([str(exe), "--demo", "--no-abrir"])
try:
    for _ in range(30):  # onefile desempaca y el server corre en un proceso hijo: se buscan todos los Companion.exe
        time.sleep(1)
        tl = subprocess.run(["tasklist", "/FI", f"IMAGENAME eq {exe.name}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        pids = set(re.findall(r'^"[^"]+","(\d+)"', tl, re.M))
        net = subprocess.run(["netstat", "-ano", "-p", "TCP"], capture_output=True, text=True).stdout
        ports = [port for port, pid in re.findall(r"127\.0\.0\.1:(\d+)\s+\S+\s+LISTENING\s+(\d+)", net) if pid in pids]
        if ports:
            d = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{ports[0]}/api/estado", timeout=5).read())
            print("OK puerto", ports[0], "fase =", d.get("fase"), "| claves:", sorted(d)); sys.exit(0 if "fase" in d else 1)
    print("sin puerto tras 30 s"); sys.exit(1)
finally:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)], capture_output=True)
