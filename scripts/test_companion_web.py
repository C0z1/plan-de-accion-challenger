"""Pruebas de companion_web.py sin red, sin cliente ni navegador: estado JSON y HTTP servido."""
import http.client, http.server, json, threading, unittest
from unittest import mock

import companion_web as w

FICHA = {"champ": "Sylas", "rival": "Ahri", "pos": "MIDDLE",
         "por_que": {"champ": "Sylas", "est": 0.6, "n_rol": 80, "wr_rol": 0.55, "v": 3, "n": 4, "oro14": 22, "frase": "Sylas va 3-1.", "pocas": True},
         "cuidado": {"rival": "Ahri", "v": 7, "n": 10, "wr": 0.7, "ic": [0.4, 0.9], "oro14": 293, "cs14": 3.2, "xp14": 1, "nivel6": -0.1,
                     "muertes6": 0.5, "ref": {"oro14": -118, "cs14": -3, "nivel6": 0, "muertes6": 0.6}, "notas": [], "pocas": False, "anticipa": ["muertes6"]},
         "reglas": [{"texto": "69+ minions al 10.", "numero": "74%", "n": 90, "pista": False}],
         "counters": {"lista": [{"rival": "Viktor", "v": 1, "n": 3, "ic": [0.06, 0.79], "cs14": -28, "oro14": -570, "pocas": True}], "ref": {"cs14": -7, "oro14": -273}}}
RECS = [("Ahri", {"nombre": "Ahri", "conocido": True, "vs": [{"win": True}, {"win": False}], "en": [{}], "filas": [{"champ": "Sylas", "est": 0.6, "vd": "3-1"}],
                  "avisos": [], "build_dict": None, "ficha": FICHA})]


class Estado(unittest.TestCase):
    def setUp(self): self.viejo = dict(w.ESTADO)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_draft_sin_partidas_y_con_lineas(self):
        w.evento(("fase", "ChampSelect")); w.evento(("draft", "MIDDLE", RECS))
        s = json.loads(w.estado())
        r = s["draft"]["recs"][0]
        self.assertNotIn("vs", r); self.assertNotIn("en", r)
        self.assertEqual((r["v"], r["n"]), (1, 2))
        self.assertTrue(any("tiende a repetirse" in l for l in r["lineas"]["cuidado"]))
        self.assertEqual(s["fase"], "ChampSelect")

    def test_rival_desconocido_y_version_sube(self):
        v = w.ESTADO["v"]; w.evento(("draft", "MIDDLE", [("Zed", None)]))
        self.assertEqual(w.ESTADO["draft"]["recs"][0], {"rival": "Zed", "conocido": False}); self.assertEqual(w.ESTADO["v"], v + 1)

    def test_champselect_borra_lo_anterior(self):
        w.evento(("aviso", {"texto": "x", "tipo": "consejo", "minuto": 5})); w.evento(("draft", "MIDDLE", RECS)); w.evento(("fase", "ChampSelect"))
        self.assertIsNone(w.ESTADO["draft"]); w.evento(("fase", "Lobby")); self.assertIsNone(w.ESTADO["aviso"])


    def test_demo_recorre_las_fases(self):
        q = []
        with mock.patch.object(w.gui, "recomendaciones", return_value=RECS), mock.patch.object(w.time, "sleep"), \
             mock.patch.object(w.companion, "minions10", return_value=None):
            w.demo(type("Q", (), {"put": lambda _, e: q.append(e)})())
        self.assertEqual([e[1] for e in q if e[0] == "fase"], ["ChampSelect", "InProgress", "EndOfGame"])
        for e in q: w.evento(e)
        s = json.loads(w.estado())
        self.assertEqual(s["fase"], "EndOfGame"); self.assertIn("kda", s["fin"]); self.assertIn("muertes14_25", s["fin"]); self.assertIn("nivel_rival", s["meta"])

    def test_minions10_incompleto_es_none(self):
        for cfg in ('{"minions10": {"campeon": "Sylas"}}', '{"minions10": {"minimo": 69}}'):
            with mock.patch.object(w.companion, "CFG") as f:
                f.exists.return_value = True; f.read_text.return_value = cfg
                self.assertIsNone(w.companion.minions10())


class Http(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def get(self, path, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("GET", path, headers={"Host": host} if host else {}); r = c.getresponse(); return r.status, r.read()

    def test_pagina_y_estado(self):
        st, b = self.get("/"); self.assertEqual(st, 200); self.assertIn(b"/api/estado", b); self.assertIn("Cómo jugarlo".encode(), b)
        st, b = self.get("/api/estado"); self.assertEqual(st, 200); self.assertIn("fase", json.loads(b))

    def test_pie_wr_con_pocas_partidas(self):
        st, b = self.get("/"); self.assertIn(b"ps.length > 3", b); self.assertIn("Pocas partidas: el WR casi no dice nada".encode(), b)

    def test_iconos_y_filas_nuevas(self):  # pedido del usuario: íconos por métrica, sin emoji, y filas con tu dato
        st, b = self.get("/"); t = b.decode()
        for k in ("nivel", "cs", "muertes", "kp", "vision", "oro", "dano", "objetivos", "linea", "tilt", "champselect", "perfil"):
            self.assertRegex(t, rf"\n  {k}: '<")
        for f in ("La sueles cumplir", "Te cuesta", "Lo que más te baja", 'class="div"', 'aria-hidden="true"', 'role="img"'):
            self.assertIn(f, t)
        self.assertNotRegex(t, "[\U0001F300-\U0001FAFF]")  # nada de emoji

    def test_vista_partidas(self):
        st, b = self.get("/"); t = b.decode()
        for f in ('id="b-partidas"', "\n  partidas: '<", "function partidas(s)", "Tus partidas", '"partidas"]'):
            self.assertIn(f, t)

    def test_csp_no_deja_cargar_de_fuera(self):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5); c.request("GET", "/")
        self.assertIn("default-src 'none'", c.getresponse().getheader("Content-Security-Policy"))

    def test_host_ajeno_403(self):
        self.assertEqual(self.get("/api/estado", host="evil.example")[0], 403)

    def test_imagen_valida_el_nombre(self):
        with mock.patch.object(w, "imagen", return_value=b"PNG") as im:
            self.assertEqual(self.get("/img/champion/Ahri.png"), (200, b"PNG")); im.assert_called_with("champion", "Ahri")
            self.assertEqual(self.get("/img/champion/..%2F..%2Fx.png")[0], 404)
            self.assertEqual(self.get("/img/otra/Ahri.png")[0], 404)
            self.assertEqual(im.call_count, 1)


class CacheRendimiento(unittest.TestCase):
    def test_usa_cache_y_la_invalida_al_cambiar_partidas(self):
        import pathlib, tempfile
        with tempfile.TemporaryDirectory() as d:
            raw, cache = pathlib.Path(d, "raw"), pathlib.Path(d, "c.json"); raw.mkdir()
            (raw / "LA1_1.json").write_text("{}")
            with mock.patch.object(w, "rendimiento", return_value={"x": 1}) as r:
                self.assertEqual(w.rendimiento_rapido(raw, cache), {"x": 1})
                self.assertEqual(w.rendimiento_rapido(raw, cache), {"x": 1})
                self.assertEqual(r.call_count, 1)  # la segunda sale de la caché
                (raw / "LA1_2.json").write_text("{}")
                w.rendimiento_rapido(raw, cache)
                self.assertEqual(r.call_count, 2)  # partida nueva: se recalcula


if __name__ == "__main__":
    unittest.main()
