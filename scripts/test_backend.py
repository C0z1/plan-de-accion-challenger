"""descargar.py contra el backend de Racha (un servidor falso local): baja tus partidas con tu código de acceso, sin key."""
import http.server, json, os, pathlib, subprocess, sys, tempfile, threading, unittest

DIR = pathlib.Path(__file__).resolve().parent
PARTIDA = {"metadata": {"matchId": "LA1_9"}, "info": {"participants": []}}


class Falso(http.server.BaseHTTPRequestHandler):
    vistos = []
    def log_message(self, *a): pass
    def do_GET(self):
        Falso.vistos.append((self.path, self.headers.get("X-Racha-Token"), self.headers.get("X-Riot-Token")))
        if self.headers.get("X-Racha-Token") != "codigo-ok": return self.responder(401, {"error": "código"})
        p = self.path
        if "/riot/account/v1/" in p: return self.responder(200, {"puuid": "P", "gameName": "Amigo", "tagLine": "LAN"})
        if "/league/v4/" in p: return self.responder(200, [])
        if p.endswith("/ids?queue=420&start=0&count=1"): return self.responder(200, ["LA1_9"])
        if "/matches/LA1_9" in p: return self.responder(200, PARTIDA)
        self.responder(404, {})
    def responder(self, code, d):
        b = json.dumps(d).encode(); self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


class TestBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Falso)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def correr(self, token):
        Falso.vistos.clear()
        d = tempfile.mkdtemp()
        env = {k: v for k, v in os.environ.items() if k not in ("RIOT_KEY",)}
        env.update(RACHA_SOLO_BACKEND="1", RACHA_API=f"http://127.0.0.1:{self.srv.server_port}", RACHA_TOKEN=token,
                   RIOT_ID="Amigo#LAN", RIOT_REGION="la1", DATOS_DIR=d, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(DIR / "descargar.py"), "1"], env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
        return r, pathlib.Path(d)

    def test_baja_con_codigo_sin_key(self):
        r, d = self.correr("codigo-ok")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((d / "LA1_9.json").exists() and (d / "timeline" / "LA1_9.json").exists())
        self.assertTrue(all(t == "codigo-ok" and k is None for _, t, k in Falso.vistos))  # nunca manda una key de Riot
        self.assertTrue(Falso.vistos[0][0].startswith("/v1/riot/americas/riot/account/v1/accounts/by-riot-id/Amigo/LAN"))

    def test_codigo_invalido_sale_con_2(self):
        r, _ = self.correr("codigo-malo")
        self.assertEqual(r.returncode, 2); self.assertIn("código de acceso", r.stderr)


if __name__ == "__main__":
    unittest.main()
