"""Pruebas de companion_web.py (Turno 7): el servidor local escucha solo en 127.0.0.1 y sirve
el estado de la página sin red ni ventanas. No toca el cliente de LoL ni descarga imágenes."""
import http.server, json, threading, unittest, urllib.error, urllib.request
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

import companion_web as web  # noqa: E402


class Servidor:
    def __init__(self):
        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), web.H)
        self.url = f"http://127.0.0.1:{self.srv.server_port}"
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def get(self, path, host=None):
        req = urllib.request.Request(self.url + path, headers={} if host is None else {"Host": host})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.headers.get("Content-Type"), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type"), b""

    def stop(self):
        self.srv.shutdown()


class TestServidor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor()

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()

    def test_escucha_solo_loopback(self):
        self.assertEqual(self.s.srv.server_address[0], "127.0.0.1")

    def test_index_html(self):
        code, tipo, cuerpo = self.s.get("/")
        self.assertEqual(code, 200)
        self.assertIn("text/html", tipo)
        self.assertIn(b"Plan Challenger", cuerpo)

    def test_estado_es_json(self):
        code, tipo, cuerpo = self.s.get("/api/estado")
        self.assertEqual(code, 200)
        self.assertIn("application/json", tipo)
        d = json.loads(cuerpo)
        for k in ("fase", "draft", "meta", "fin", "revision", "rango", "aviso", "v"):
            self.assertIn(k, d)

    def test_host_local_sirve(self):
        for host in ("127.0.0.1", "localhost", "localhost:9999", "127.0.0.1:1"):
            code, _, _ = self.s.get("/api/estado", host=host)
            self.assertEqual(code, 200, host)

    def test_host_ajeno_403(self):
        code, _, _ = self.s.get("/api/estado", host="malo.ejemplo")
        self.assertEqual(code, 403)

    def test_ruta_desconocida_404(self):
        code, _, _ = self.s.get("/no-existe")
        self.assertEqual(code, 404)


class TestEstado(unittest.TestCase):
    def test_evento_fase_resetea_draft(self):
        web.ESTADO.update(fase="inicio", draft={"recs": []}, fin={"texto": "x"}, v=0)
        web.evento(("fase", "ChampSelect"))
        self.assertEqual(web.ESTADO["fase"], "ChampSelect")
        self.assertIsNone(web.ESTADO["draft"])
        self.assertIsNone(web.ESTADO["fin"])
        self.assertIsNone(web.ESTADO["meta"])

    def test_draft_json_quita_partidas_y_cuenta(self):
        ficha = {"cuidado": {"rival": "Zed", "n": 0, "v": 0, "ic": [0.0, 0.0], "notas": [], "ref": {}},
                 "counters": {"lista": [], "ref": {}}}
        recs = [("Zed", {"vs": [{"win": True}, {"win": False}], "en": [1, 2],
                         "filas": [{"champ": "Yone", "est": 0.55, "vd": "3-1"}], "ficha": ficha})]
        d = web.draft_json("MIDDLE", recs)
        self.assertEqual(d["pos"], "MIDDLE")
        r = d["recs"][0]
        self.assertNotIn("vs", r)
        self.assertNotIn("en", r)
        self.assertEqual(r["v"], 1)
        self.assertEqual(r["n"], 2)
        self.assertEqual(r["lineas"], {"cuidado": [], "counters": []})


if __name__ == "__main__":
    unittest.main()
