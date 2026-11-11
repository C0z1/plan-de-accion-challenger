"""Humo del companion de punta a punta sin cliente (corre en el CI): Lobby → ChampSelect → InProgress → EndOfGame.
Solo se simulan urlopen (LCU y puerto 2999, con fixtures), el reloj, sleep y la descarga; draft y revision.py corren de verdad."""
import contextlib, io, json, os, pathlib, subprocess, sys, tempfile, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
FIX = AQUI / "fixtures"
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(FIX / "datos")  # CI o clon nuevo, como test_draft
import companion, draft  # draft reconfigura stdout al importarse: antes de redirigirlo

CORRER = subprocess.run

FASES = ["Lobby", "ChampSelect", "ChampSelect", "InProgress", "InProgress", "InProgress", "EndOfGame", "EndOfGame", "Lobby"]


class Flujo(unittest.TestCase):
    def test_partida_completa(self):
        sesion = json.loads((FIX / "champselect" / "session.json").read_text())
        for p in sesion["theirTeam"]:
            if p["assignedPosition"] == "middle": p["championId"] = 238  # Zed: está en los datos de fixture y en la foto en vivo
        foto = (FIX / "vivo" / "allgamedata.json").read_bytes()
        fases, reloj, urls, cmds = iter(FASES), iter(range(100, 100_000, 100)), [], []

        def urlopen(req, **kw):
            url = getattr(req, "full_url", req); urls.append(url)
            if ":2999/" in url: return io.BytesIO(foto)
            if "champ-select" in url: return io.BytesIO(json.dumps(sesion).encode())
            return io.BytesIO(json.dumps(next(fases)).encode())  # al acabarse, StopIteration corta el bucle

        def run(cmd):
            cmds.append(pathlib.Path(cmd[1]).name)
            if cmds[-1] == "descargar.py": return subprocess.CompletedProcess(cmd, 0)  # sin red ni key
            r = CORRER(cmd, capture_output=True, text=True, encoding="utf-8", env={**os.environ, "DATOS_DIR": str(FIX / "datos")})
            print(r.stdout, r.stderr); return r

        with tempfile.TemporaryDirectory() as t:
            lock = pathlib.Path(t) / "lockfile"; lock.write_text("LeagueClient:1:50001:pw:https")
            orig = (companion.LOCK, companion.VIVO, companion.urllib.request.urlopen, companion.subprocess.run,
                    companion.time.sleep, companion.time.time)
            companion.LOCK, companion.VIVO = lock, pathlib.Path(t) / "vivo"
            companion.urllib.request.urlopen, companion.subprocess.run = urlopen, run
            companion.time.sleep, companion.time.time = (lambda _: None), (lambda: next(reloj))
            out = io.StringIO()
            try:
                with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
            finally:
                (companion.LOCK, companion.VIVO, companion.urllib.request.urlopen, companion.subprocess.run,
                 companion.time.sleep, companion.time.time) = orig
            vivos = list((pathlib.Path(t) / "vivo").glob("*.jsonl"))
            fotos = vivos[0].read_text(encoding="utf-8").splitlines() if vivos else []
        out = out.getvalue()
        self.assertEqual(out.count("=== Zed (MIDDLE) ==="), 1, out)  # 2 sondeos en champ select, 1 recomendación
        self.assertIn("Recomendación: ", out)
        self.assertEqual((len(vivos), len(fotos)), (1, 3), out)  # una foto por sondeo de InProgress, un archivo
        self.assertEqual(json.loads(fotos[0])["gameData"]["gameTime"], json.loads(foto)["gameData"]["gameTime"])
        self.assertEqual(out.count("no tradear hasta igualar"), 1)  # aviso de nivel una vez
        self.assertEqual(cmds, ["descargar.py", "revision.py"])  # post-partida una vez
        self.assertIn("| Win rate |", out)  # revision.py 1 corrió y salió su tabla
        self.assertNotIn("Traceback", out); self.assertNotIn("Error (sigo)", out)
        self.assertTrue(all("127.0.0.1" in u for u in urls))  # solo local


if __name__ == "__main__": unittest.main()
