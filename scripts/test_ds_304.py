"""Pruebas del 304 de /api/estado (propuesta de DeepSeek, aplicada por Opus en 50f7bbb):
GET /api/estado?desde=<v> responde 304 sin cuerpo si ESTADO['v'] no cambió; con otro v, sin ?desde o con
?desde=basura, 200 con el JSON. Mismo patrón de servidor que scripts/test_companion_web.py (sin red ni navegador)."""
import http.client, http.server, json, threading, unittest

import companion_web as w


class Estado304(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def setUp(self): self.viejo = dict(w.ESTADO)

    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("GET", path, headers={"Host": "127.0.0.1"}); r = c.getresponse(); b = r.read()
        return r.status, b

    def test_sin_desde_200_con_json(self):
        st, b = self.get("/api/estado")
        self.assertEqual(st, 200); self.assertIn("v", json.loads(b))

    def test_desde_actual_304_sin_cuerpo(self):
        st, b = self.get(f"/api/estado?desde={w.ESTADO['v']}")
        self.assertEqual(st, 304); self.assertEqual(b, b"")

    def test_desde_otro_200(self):
        st, b = self.get(f"/api/estado?desde={w.ESTADO['v'] + 1}")
        self.assertEqual(st, 200); self.assertIn("fase", json.loads(b))

    def test_desde_basura_200(self):
        self.assertEqual(self.get("/api/estado?desde=basura")[0], 200)

    def test_desde_vacio_200(self):
        self.assertEqual(self.get("/api/estado?desde=")[0], 200)

    def test_evento_nuevo_vuelve_a_dar_200(self):
        v = w.ESTADO["v"]
        self.assertEqual(self.get(f"/api/estado?desde={v}")[0], 304)          # nada cambió
        w.evento(("aviso", {"texto": "x", "tipo": "consejo", "minuto": 5}))   # algo cambió: v sube
        self.assertEqual(self.get(f"/api/estado?desde={v}")[0], 200)          # el v viejo ya no alcanza
        self.assertEqual(self.get(f"/api/estado?desde={w.ESTADO['v']}")[0], 304)  # el v nuevo sí


if __name__ == "__main__":
    unittest.main()
