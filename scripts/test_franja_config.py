"""A4 franja configurable: piezas según ajustes, posición, lista blanca de franja_pos y POST /api/ajuste."""
import http.server, json, pathlib, tempfile, threading, unittest, urllib.error, urllib.request
from unittest import mock

import companion_gui as g
import companion_web as w
import overlay

META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "cs": 71, "rival_cs": 140, "recibido": 1000.0, "muertes14": 3, "minuto": 20,
        "objetivos": {"dragon": 90, "baron": None}, "oro": {"tu": 7400, "rival": 7900}}


def textos(aj):  # todas las fases juntas: cada fase enseña piezas distintas (F6)
    return " | ".join(t for m in (3, 9, 20) for t, _ in overlay.partes({**META, "minuto": m}, 1000.0, aj))


class Piezas(unittest.TestCase):
    def test_todo_por_defecto(self):
        for aj in (None, {}):
            t = textos(aj)
            for x in ("Dragón", "Barón", "Nv 11", "CS 71", "Oro", "Muertes 14"): self.assertIn(x, t)

    def test_cada_ajuste_quita_lo_suyo(self):
        t = textos({"franja_objetivos": False}); self.assertNotIn("Dragón", t); self.assertNotIn("Barón", t); self.assertIn("Nv 11", t)
        t = textos({"franja_linea": False}); self.assertTrue(all(x not in t for x in ("Nv", "CS", "Oro"))); self.assertIn("Dragón", t)
        t = textos({"franja_regla": False}); self.assertNotIn("Muertes", t); self.assertIn("Oro", t)

    def test_pos_y(self):
        self.assertEqual(overlay.pos_y("arriba", 1080, 30), 6); self.assertEqual(overlay.pos_y(None, 1080, 30), 6)
        self.assertEqual(overlay.pos_y("abajo", 1080, 30), 1044); self.assertEqual(overlay.pos_y("abajo", 20, 30), 0)
        self.assertEqual(overlay.pos_y("abajo", 1080, 30, 6, 0.95), 990)  # encima de la barra de tareas (5 % de la pantalla)
        self.assertTrue(0.5 <= overlay.fraccion_util() <= 1.0)


class Ajustes(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.addCleanup(self.d.cleanup)
        p = mock.patch.object(g, "AJUSTES_F", pathlib.Path(self.d.name) / "a.json"); p.start(); self.addCleanup(p.stop)

    def test_defaults_y_lista_blanca(self):
        a = g.ajustes()
        self.assertEqual(a["franja_pos"], "arriba"); self.assertTrue(a["franja_objetivos"] and a["franja_linea"] and a["franja_regla"])
        self.assertEqual(g.guardar_ajuste("franja_pos", "abajo")["franja_pos"], "abajo"); self.assertEqual(g.ajustes()["franja_pos"], "abajo")
        for clave, v in (("franja_pos", "lado"), ("franja_pos", True), ("franja_pos", None), ("franja_linea", "abajo"), ("overlay", "arriba")):
            with self.assertRaises(ValueError): g.guardar_ajuste(clave, v)

    def test_archivo_con_valor_malo_vuelve_al_defecto(self):
        g.AJUSTES_F.write_text(json.dumps({"franja_pos": "lado", "franja_regla": "no"}))
        self.assertEqual((g.ajustes()["franja_pos"], g.ajustes()["franja_regla"]), ("arriba", True))


class Endpoint(unittest.TestCase):
    def post(self, cuerpo):
        r = urllib.request.Request(self.url + "api/ajuste", json.dumps(cuerpo).encode(), {"X-HTC": "1", "Content-Type": "application/json"})
        try: return urllib.request.urlopen(r).status
        except urllib.error.HTTPError as e: return e.code

    def test_abajo_si_lado_no(self):
        d = tempfile.TemporaryDirectory(); self.addCleanup(d.cleanup)
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H); self.addCleanup(srv.server_close)
        threading.Thread(target=srv.serve_forever, daemon=True).start(); self.addCleanup(srv.shutdown)
        self.url = f"http://127.0.0.1:{srv.server_port}/"
        with mock.patch.object(g, "AJUSTES_F", pathlib.Path(d.name) / "a.json"), mock.patch.object(w, "sync_nube", lambda: None):
            self.assertEqual(self.post({"clave": "franja_pos", "on": "abajo"}), 200); self.assertEqual(g.ajustes()["franja_pos"], "abajo")
            self.assertEqual(self.post({"clave": "franja_pos", "on": "lado"}), 400)
            self.assertEqual(self.post({"clave": "overlay", "on": "abajo"}), 400)
            self.assertEqual(self.post({"clave": "overlay", "on": False}), 200)


if __name__ == "__main__": unittest.main()
