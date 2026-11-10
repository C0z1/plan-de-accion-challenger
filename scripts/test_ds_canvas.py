"""Pruebas de lo nuevo del canvas→app (DeepSeek, 2026-11-10): meta_fase/meta_aram/grieta/historial/nombres_lcu,
rutas de companion_web (rango/minion/fuentes), eventos (cuenta/region), vistas._build e index.html.
Sin red, sin cliente de LoL ni key."""
import http.client, http.server, io, json, os, pathlib, sys, tempfile, threading, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixtures de draft

import companion  # noqa: E402
import companion_web as w  # noqa: E402

FIX = AQUI / "fixtures" / "vivo" / "allgamedata.json"


def foto():
    return json.loads(FIX.read_text(encoding="utf-8"))


class MetaFase(unittest.TestCase):
    def test_meta_fase_de_la_fixture(self):
        m = companion.meta_fase(foto(), m10={})
        self.assertIsInstance(m["t"], int)
        self.assertEqual(m["t"], 362)  # gameTime 362.4 → segundos enteros
        self.assertEqual(m["kda"], "0/0/0")
        self.assertEqual(m["items"], [])  # la foto no trae ítems

    def test_items_sin_consumibles_ni_trinket_y_max_6(self):
        d = foto(); me = d["allPlayers"][0]
        me["items"] = [{"itemID": i, "displayName": f"It{i}", "slot": s}
                       for i, s in ((1001, 0), (1002, 1), (1003, 2), (1004, 3), (1005, 4), (1006, 5), (1007, 0), (1008, 1))]
        me["items"] += [{"itemID": 2003, "displayName": "Poción", "slot": 2, "consumable": True},
                        {"itemID": 3340, "displayName": "Trinket", "slot": 6}]
        m = companion.meta_fase(d, m10={})
        self.assertEqual(m["items"], [[1001, "It1001"], [1002, "It1002"], [1003, "It1003"], [1004, "It1004"], [1005, "It1005"], [1006, "It1006"]])


class GrietaYAram(unittest.TestCase):
    def test_sin_game_mode_es_grieta(self):
        self.assertTrue(companion.grieta({}))
        self.assertTrue(companion.grieta(None))
        self.assertTrue(companion.grieta({"gameData": {}}))
        self.assertFalse(companion.grieta({"gameData": {"gameMode": "ARAM"}}))

    def test_aram_sin_rivales_amenazas_vacias(self):
        d = {"activePlayer": {"riotId": "yo#X", "summonerName": "yo"},
             "gameData": {"gameMode": "ARAM", "gameTime": 600},
             "allPlayers": [{"championName": "Zeri", "team": "ORDER", "position": "NONE", "level": 5,
                             "scores": {"kills": 1, "deaths": 2, "assists": 3}, "riotId": "yo#X", "summonerName": "yo", "items": []}],
             "events": {"Events": []}}
        m = companion.meta_aram(d, d["allPlayers"][0])
        self.assertEqual(m["amenazas"], [])
        self.assertEqual(m["kills"], [1, 0])  # sin rivales, solo cuentan tus kills


class HistorialYNombres(unittest.TestCase):
    def test_historial_bordes(self):
        h = {"games": {"games": [
            {"queueId": 420, "gameDuration": 300, "gameCreation": 100, "participants": None},   # sin participante
            {"queueId": 999, "gameDuration": 1800, "gameCreation": 200, "participants": [{"championId": 1, "stats": {}}]},  # cola fuera
            {"queueId": 420, "gameDuration": 200, "gameCreation": 300, "participants": [{"championId": 1, "stats": {}}]},  # remake
        ]}}
        self.assertEqual(companion.historial(h, {1: "Ahri"}), [])
        self.assertEqual(companion.historial(None, {}), [])
        self.assertEqual(companion.historial({"games": None}, {}), [])

    def test_nombres_lcu_filtra_raro_y_negativos(self):
        lista = [{"id": 1, "alias": "Ahri"}, {"id": -5, "alias": "X"}, {"id": 2, "alias": ""},
                 "raro", None, {"id": 0, "alias": "Y"}]
        with mock.patch.object(companion, "lcu", return_value=lista):
            self.assertEqual(companion.nombres_lcu(), {1: "Ahri"})
        with mock.patch.object(companion, "lcu", return_value=None):
            self.assertEqual(companion.nombres_lcu(), {})


class Rutas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown(); cls.srv.server_close()

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("GET", path); r = c.getresponse(); b = r.read(); return r.status, b

    def test_rango_invalido_404_sin_red(self):
        self.assertEqual(self.get("/img/rango/madera.png")[0], 404)

    def test_minion_nombre_invalido_404(self):
        self.assertEqual(self.get("/img/minion/otro.png")[0], 404)

    def test_rango_y_minion_validos_sin_red(self):
        with tempfile.TemporaryDirectory() as t, mock.patch.object(w, "IMG", pathlib.Path(t)), \
             mock.patch.object(w.urllib.request, "urlopen", side_effect=lambda *a, **k: io.BytesIO(b"PNGDATA")):
            self.assertEqual(self.get("/img/rango/iron.png"), (200, b"PNGDATA"))
            self.assertEqual(self.get("/img/minion/caster.png"), (200, b"PNGDATA"))

    def test_fuentes(self):
        self.assertEqual(self.get("/fonts/mulish.woff2")[0], 200)
        self.assertEqual(self.get("/fonts/inter.woff2")[0], 200)
        self.assertEqual(self.get("/fonts/otra.woff2")[0], 404)


class Eventos(unittest.TestCase):
    def setUp(self):
        self.viejo = dict(w.ESTADO); self.cuenta = w.gui.CUENTA[0]

    def tearDown(self):
        w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.gui.CUENTA[0] = self.cuenta

    def test_cuenta_guarda_icono(self):
        with mock.patch.object(w.gui, "perfil", return_value="Nueva#LAN"), mock.patch.object(w, "refrescar"):
            w.evento(("cuenta", "Nueva#LAN", 456))
        self.assertEqual(w.ESTADO["cuenta"], "Nueva#LAN")
        self.assertEqual(w.ESTADO["icono"], 456)
        with mock.patch.object(w.gui, "perfil", return_value="Otra#LAS"), mock.patch.object(w, "refrescar"):
            w.evento(("cuenta", "Otra#LAS"))
        self.assertIsNone(w.ESTADO["icono"])

    def test_region_se_guarda(self):
        w.evento(("region", "LAN"))
        self.assertEqual(w.ESTADO["region"], "LAN")


class Builds(unittest.TestCase):
    def test_build_que_truena_da_none(self):
        import builds, vistas
        with mock.patch.object(builds, "guardado_dict", side_effect=RuntimeError("boom")):
            self.assertIsNone(vistas._build("Sylas", "MIDDLE"))
        with mock.patch.object(builds, "guardado_dict", return_value={"core": []}):
            self.assertEqual(vistas._build("Sylas", "MIDDLE"), {"core": []})


class IndexHtml(unittest.TestCase):
    def test_funciones_del_canvas_y_sin_textos_viejos(self):
        t = (w.WEB / "index.html").read_text(encoding="utf-8")
        for f in ("function cuentaCab(", "function rangoCard(", "function aro(", "function xpAro(",
                  "function franja(", "function envivoAram(", "function partidasCliente(", "function campeonesCliente("):
            self.assertIn(f, t)
        self.assertNotIn("avísale a Opus", t)
        self.assertNotIn("HTC", t.replace("X-HTC", ""))


if __name__ == "__main__":
    unittest.main()
