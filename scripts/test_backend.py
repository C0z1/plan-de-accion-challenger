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
        if p.endswith("&queue=420&start=0&count=1"): return self.responder(200, ["LA1_9"])
        if p.endswith("&queue=440&start=0&count=1"): return self.responder(200, [])  # Flex: nada
        if p.endswith("&queue=420&start=0&count=100"): return self.responder(200, ["LA1_9", "LA1_12"])  # «todo»: menos de 100, fin
        if p.endswith("&queue=440&start=0&count=100"): return self.responder(200, ["LA1_11"])
        if "/matches/LA1_" in p and "by-puuid" not in p: return self.responder(200, PARTIDA)
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

    def correr(self, token, n="1", d=None):
        Falso.vistos.clear()
        d = d or tempfile.mkdtemp()
        env = {k: v for k, v in os.environ.items() if k not in ("RIOT_KEY",)}
        env.update(RACHA_INICIO="1767225600", RACHA_SOLO_BACKEND="1", RACHA_API=f"http://127.0.0.1:{self.srv.server_port}", RACHA_TOKEN=token,
                   RIOT_ID="Amigo#LAN", RIOT_REGION="la1", DATOS_DIR=d, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, str(DIR / "descargar.py"), n], env=env, capture_output=True, text=True, encoding="utf-8", timeout=60)
        return r, pathlib.Path(d)

    def test_baja_con_codigo_sin_key(self):
        r, d = self.correr("codigo-ok")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((d / "LA1_9.json").exists() and (d / "timeline" / "LA1_9.json").exists())
        self.assertTrue(all(t == "codigo-ok" and k is None for _, t, k in Falso.vistos))  # nunca manda una key de Riot
        self.assertTrue(Falso.vistos[0][0].startswith("/v1/riot/americas/riot/account/v1/accounts/by-riot-id/Amigo/LAN"))

    def test_todo_solo_y_flex_y_marca(self):
        r, d = self.correr("codigo-ok", "todo")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(f.stem for f in d.glob("LA1_*.json")), ["LA1_12", "LA1_9"])  # solo Solo/Duo (0.31): sin la Flex
        self.assertTrue(all("startTime=1767225600&queue=420" in p for p, *_ in Falso.vistos if "/ids?" in p))  # solo la temporada
        self.assertTrue((d / "historial.json").exists())  # historial completo: la próxima vez solo lo nuevo
        r, _ = self.correr("codigo-ok", "todo", str(d))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(any("/matches/LA1_" in p and "by-puuid" not in p for p, *_ in Falso.vistos))  # nada repetido

    def test_dos_pasadas_lista_primero_y_detalles_al_final(self):  # 0.30: la lista completa enseguida; los timelines viejos al final
        import runpy, unittest.mock as um
        d, lineas = tempfile.mkdtemp(), []
        env = {"RACHA_INICIO": "1767225600", "RACHA_SOLO_BACKEND": "1", "RACHA_API": f"http://127.0.0.1:{self.srv.server_port}", "RACHA_TOKEN": "codigo-ok", "RIOT_REGION": "la1"}
        Falso.vistos.clear()
        with um.patch.dict(os.environ, env), um.patch.dict(os.environ, {"RIOT_KEY": ""}):
            os.environ.pop("RIOT_KEY")
            try: runpy.run_path(str(DIR / "descargar.py"), run_name="__main__", init_globals=dict(ARGV=["todo"], RAW_DIR=d, RIOT_ID_G="Amigo#LAN", RECIENTES=1, ECO=lineas.append))
            except SystemExit as e: self.assertIn(e.code, (0, None))
        rutas = [p for p, *_ in Falso.vistos if "/matches/LA1_" in p and "by-puuid" not in p]
        self.assertEqual(rutas[:3], ["/v1/riot/americas/lol/match/v5/matches/LA1_12", "/v1/riot/americas/lol/match/v5/matches/LA1_12/timeline",
                                     "/v1/riot/americas/lol/match/v5/matches/LA1_9"])  # la más nueva completa; las demás, primero la partida
        self.assertTrue(rutas[-1].endswith("/timeline"))  # los detalles viejos, al final
        self.assertTrue(all((pathlib.Path(d) / "timeline" / f"{m}.json").exists() for m in ("LA1_9", "LA1_12")))
        self.assertIn("progreso 2/2", lineas); self.assertIn("detalles 1/1", lineas); self.assertTrue((pathlib.Path(d) / "historial.json").exists())

    def test_no_mezcla_otra_cuenta(self):
        d = tempfile.mkdtemp()
        pathlib.Path(d, "perfil.json").write_text(json.dumps({"account": {"puuid": "OTRO", "gameName": "Dueño", "tagLine": "LAN"}}))
        r, _ = self.correr("codigo-ok", "1", d)
        self.assertEqual(r.returncode, 4); self.assertIn("Dueño#LAN", r.stderr)
        self.assertFalse(list(pathlib.Path(d).glob("LA1_*.json")))

    def test_codigo_invalido_sale_con_2(self):
        r, _ = self.correr("codigo-malo")
        self.assertEqual(r.returncode, 2); self.assertIn("código de acceso", r.stderr)


if __name__ == "__main__":
    unittest.main()
