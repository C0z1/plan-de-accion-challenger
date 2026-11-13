"""A4 franja configurable: piezas según ajustes, posición, lista blanca de franja_pos y POST /api/ajuste."""
import http.server, json, pathlib, tempfile, threading, unittest, urllib.error, urllib.request
from unittest import mock

import companion_gui as g
import companion_web as w
import overlay

META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "cs": 71, "rival_cs": 140, "recibido": 1000.0, "muertes14": 3, "kda": "2/3/4"}


def tipos(aj):  # qué estado muestra la pastilla a los 3, 9 y 20 min
    return [overlay.estado({**META, "t": m * 60}, 1000.0, aj)["tipo"] for m in (3, 9, 20)]


class Piezas(unittest.TestCase):
    def test_todo_por_defecto(self):
        for aj in (None, {}): self.assertEqual(tipos(aj), ["linea", "linea", "peleas"])

    def test_cada_ajuste_quita_lo_suyo(self):
        self.assertEqual(tipos({"franja_linea": False}), ["tarde", "tarde", "peleas"])
        self.assertEqual(tipos({"franja_regla": False}), ["linea", "linea", "tarde"])
        self.assertEqual(tipos({"franja_objetivos": False}), ["linea", "linea", "peleas"])  # ajuste viejo de 0.16: no rompe

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
        self.assertEqual(a["franja_pos"], "arriba"); self.assertTrue(a["franja_linea"] and a["franja_regla"]); self.assertNotIn("franja_objetivos", a)  # timers fuera de la franja (0.17)
        self.assertEqual(g.guardar_ajuste("franja_pos", "abajo")["franja_pos"], "abajo"); self.assertEqual(g.ajustes()["franja_pos"], "abajo")
        for clave, v in (("franja_pos", "lado"), ("franja_pos", True), ("franja_pos", None), ("franja_linea", "abajo"), ("overlay", "arriba")):
            with self.assertRaises(ValueError): g.guardar_ajuste(clave, v)

    def test_posicion_libre(self):  # la franja se arrastra a donde quieras (Ajustes > Mover la franja)
        self.assertEqual(g.guardar_ajuste("franja_pos", "libre")["franja_pos"], "libre")
        self.assertEqual(g.guardar_ajuste("franja_x", 0.5)["franja_x"], 0.5); g.guardar_ajuste("franja_y", 0)
        for v in (-0.1, 1.5, "0.5", True, None):
            with self.assertRaises(ValueError): g.guardar_ajuste("franja_x", v)
        self.assertEqual(overlay.libre((1920, 0, 4480, 1440), (1920, 1080), 0.5, 0.5, 380, 72), (1920 + 1280, 720))  # otro monitor
        self.assertEqual(overlay.libre(None, (1920, 1080), 1.0, 1.0, 380, 72), (1540, 1008))  # nunca se sale
        self.assertEqual(overlay.fraccion((1920, 0, 4480, 1440), (1920, 1080), 3200, 720), (0.5, 0.5))

    def test_mover_se_apaga_solo(self):
        w.ESTADO["mover_franja"] = 123.0; w.apagar_mover(999.0); self.assertEqual(w.ESTADO["mover_franja"], 123.0)  # otra sesión de mover: no la toca
        w.apagar_mover(123.0); self.assertFalse(w.ESTADO["mover_franja"])

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
