"""Pruebas de DeepSeek del humo del companion (turno 4, iteración 5): dodge y key caducada.
Mismo patrón que test_flujo.py: solo se simulan urlopen, el lockfile, sleep, el reloj y descargar.py."""
import contextlib, io, json, os, pathlib, subprocess, sys, tempfile, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
FIX = AQUI / "fixtures"
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(FIX / "datos")  # CI o clon nuevo, como test_flujo
import companion, draft  # draft reconfigura stdout al importarse: antes de redirigirlo


class FlujoBordes(unittest.TestCase):
    def correr(self, fases_lista, descargar_rc=0):
        sesion = json.loads((FIX / "champselect" / "session.json").read_text())
        for p in sesion["theirTeam"]:
            if p["assignedPosition"] == "middle": p["championId"] = 238  # Zed: está en la fixture de datos
        foto = (FIX / "vivo" / "allgamedata.json").read_bytes()
        fases, reloj, urls, cmds = iter(fases_lista), iter(range(100, 100_000, 100)), [], []

        def urlopen(req, **kw):
            url = getattr(req, "full_url", req); urls.append(url)
            if ":2999/" in url: return io.BytesIO(foto)
            if "champ-select" in url: return io.BytesIO(json.dumps(sesion).encode())
            return io.BytesIO(json.dumps(next(fases)).encode())  # al acabarse, StopIteration corta el bucle

        def run(cmd):
            cmds.append(pathlib.Path(cmd[1]).name)
            return subprocess.CompletedProcess(cmd, descargar_rc if cmds[-1] == "descargar.py" else 0)

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
        return out.getvalue(), cmds

    def test_dodge_recomienda_otra_vez(self):
        out, cmds = self.correr(["ChampSelect", "Lobby", "ChampSelect", "Lobby"])  # dodge y vuelta con el mismo rival
        self.assertEqual(out.count("=== Zed (MIDDLE) ==="), 2, out)  # una recomendación por champ select
        self.assertEqual(cmds, [], cmds)  # sin post-partida

    def test_key_caducada_no_corre_revision(self):
        out, cmds = self.correr(["EndOfGame", "Lobby"], descargar_rc=2)
        self.assertIn("renueva RIOT_KEY", out)
        self.assertEqual(cmds, ["descargar.py"], cmds)  # descargar sí, revision.py no


if __name__ == "__main__":
    unittest.main()
