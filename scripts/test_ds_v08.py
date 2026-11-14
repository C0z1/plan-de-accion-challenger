"""v0.8 → v0.9 calidad (pedido prompt-deepseek-v09.md, tarea 1). Sin red:
- builds.bajar()/subir() con builds._backend simulado: lista vacía, servidor None, clave con apóstrofo
  («Kai'Sa|BOTTOM»), builds.json roto, ts más nuevo en el servidor (re-baja) y guardado_dict que ignora «_bajadas».
- postpartida.momentos/muertes_sin_objetivo sobre TODAS las partidas reales de datos/raw (skip si no existe).
- POST /api/reporte y /api/invitar: sin X-HTC → 403; cuerpo vacío o JSON roto → 400.
"""
import http.client, http.server, json, pathlib, tempfile, threading, unittest, urllib.request
from unittest import mock

import builds, companion_web as w, postpartida as P

BASE = pathlib.Path(__file__).resolve().parent.parent
RAW = BASE / "datos" / "raw"


class Builds(unittest.TestCase):
    def meta(self, contenido):
        t = tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        p = pathlib.Path(t.name) / "builds.json"
        if contenido is not None: p.write_text(contenido, encoding="utf-8")
        patcher = mock.patch.object(builds, "META", pathlib.Path(t.name)); patcher.start(); self.addCleanup(patcher.stop)
        return p

    def test_bajar_lista_vacia_no_escribe(self):
        p = self.meta(None)
        with mock.patch.object(builds, "_backend", return_value=[]) as b:
            self.assertEqual(builds.bajar(), 0)
        b.assert_called_once_with("GET", "/v1/builds/_todas")
        self.assertFalse(p.exists())  # n=0: no se toca builds.json

    def test_bajar_servidor_que_devuelve_none(self):
        p = self.meta(None)
        with mock.patch.object(builds, "_backend", return_value=None) as b:
            self.assertEqual(builds.bajar(), 0)
        self.assertFalse(p.exists())

    def test_bajar_clave_con_apostrofo(self):
        p = self.meta("{}")
        datos = {"core": [["Liche", 0.6, "3100"]]}
        def falso(m, ruta, c=None, base=None):
            if ruta == "/v1/builds/_todas": return [{"clave": "Kai'Sa|BOTTOM", "ts": 5, "datos": datos}]
            raise AssertionError(f"ruta inesperada: {ruta}")
        with mock.patch.object(builds, "_backend", falso):
            self.assertEqual(builds.bajar(), 1)
        d = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["Kai'Sa|BOTTOM"], datos)
        self.assertEqual(d["_bajadas"], {"Kai'Sa|BOTTOM": 5})
        g = builds.guardado_dict("Kai'Sa", "BOTTOM")
        self.assertEqual((g["core"], g["fuente"]), (datos["core"], "mejores"))

    def test_bajar_con_builds_json_roto_no_tumba(self):
        p = self.meta("{ esto no es json")
        def falso(m, ruta, c=None, base=None):
            if ruta == "/v1/builds/_todas": return [{"clave": "Yone|MIDDLE", "ts": 1, "datos": {"n": 2}}]
            raise AssertionError(ruta)
        with mock.patch.object(builds, "_backend", falso):
            self.assertEqual(builds.bajar(), 1)
        self.assertEqual(json.loads(p.read_text(encoding="utf-8"))["Yone|MIDDLE"], {"n": 2})

    def test_bajar_ts_mas_nuevo_rebaja_y_viejo_no(self):
        p = self.meta(json.dumps({"_bajadas": {"A|B": 10, "C|D": 100}}))
        def falso(m, ruta, c=None, base=None):
            if ruta == "/v1/builds/_todas": return [{"clave": "A|B", "ts": 20, "datos": {"ruta": "A|B"}}, {"clave": "C|D", "ts": 50, "datos": {"ruta": "C|D"}}]
            raise AssertionError(ruta)
        with mock.patch.object(builds, "_backend", falso):
            self.assertEqual(builds.bajar(), 1)  # solo A|B (10 < 20); C|D ya está al día (100 >= 50)
        d = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(d["_bajadas"], {"A|B": 20, "C|D": 100})
        self.assertEqual(d["A|B"], {"ruta": "A|B"})

    def test_guardado_dict_ignora_bajadas(self):
        build = {"core": [["Liche", 0.6, "3100"]], "n": 5}
        self.meta(json.dumps({"_bajadas": {"X|Y": 1}, "Yone|MIDDLE|tu": build}))
        self.assertEqual(builds.guardado_dict("Yone", "MIDDLE")["fuente"], "tu")
        self.assertIsNone(builds.guardado_dict("Yone", "TOP"))
        self.assertIsNone(builds.guardado_dict("X", "Y"))  # «_bajadas» nunca sale como build

    def test_subir_solo_los_mejores(self):
        mejores = {"Kai'Sa|BOTTOM": {"n": 3}}
        self.meta(json.dumps({**mejores, "Yone|MIDDLE|tu": {"n": 4}, "_bajadas": {"A|B": 1}}))
        with mock.patch.object(builds, "_backend", return_value=None) as b:
            self.assertEqual(builds.subir(), 1)
        b.assert_called_once_with("PUT", "/v1/builds", {"Kai'Sa|BOTTOM": {"n": 3}})

    def test_subir_con_json_roto_devuelve_0(self):
        self.meta("{ roto")
        with mock.patch.object(builds, "_backend") as b:
            self.assertEqual(builds.subir(), 0)
        b.assert_not_called()


@unittest.skipUnless(RAW.exists() and (RAW / "perfil.json").exists(), "sin datos/raw")
class PostpartidaReal(unittest.TestCase):
    def test_todas_las_partidas(self):
        puuid = json.loads((RAW / "perfil.json").read_text(encoding="utf-8"))["account"]["puuid"]
        probadas = 0
        for f in sorted(RAW.glob("*_*.json")):
            tl = RAW / "timeline" / f.name
            if not tl.exists(): continue  # sin timeline no hay nada que medir
            m = json.loads(f.read_text(encoding="utf-8")); t = json.loads(tl.read_text(encoding="utf-8"))
            mo = P.momentos(m, t, puuid)          # no lanza con ninguna partida real
            self.assertLessEqual(len(mo), 3, f.name)
            self.assertEqual([x["t"] for x in mo], sorted(x["t"] for x in mo), f.name)  # orden cronológico
            s = P.muertes_sin_objetivo(m, t, puuid)  # tampoco lanza
            self.assertEqual(set(s), {"n", "total", "ratio", "por_tipo", "lista"}, f.name)
            probadas += 1
        self.assertGreater(probadas, 0)


class PostV08(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def post(self, ruta, cuerpo, htc=None):
        headers = {"Content-Type": "application/json"}
        if htc: headers["X-HTC"] = htc
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", ruta, cuerpo, headers); r = c.getresponse(); b = r.read()
        c.close(); return r.status, b

    def test_reporte_sin_htc_403(self):
        with mock.patch.object(w, "reportar") as r:
            self.assertEqual(self.post("/api/reporte", b'{"texto":"x"}')[0], 403)
            r.assert_not_called()

    def test_invitar_sin_htc_403(self):
        with mock.patch.object(w, "invitar") as i:
            self.assertEqual(self.post("/api/invitar", b'{"nombre":"x"}')[0], 403)
            i.assert_not_called()

    def test_reporte_cuerpo_vacio_400(self):
        self.assertEqual(self.post("/api/reporte", b"", htc="1")[0], 400)

    def test_reporte_json_roto_400(self):
        self.assertEqual(self.post("/api/reporte", b"{no", htc="1")[0], 400)

    def test_invitar_cuerpo_vacio_400(self):
        self.assertEqual(self.post("/api/invitar", b"", htc="1")[0], 400)

    def test_invitar_json_roto_400(self):
        self.assertEqual(self.post("/api/invitar", b"{no", htc="1")[0], 400)

    def test_campo_faltante_400(self):  # JSON válido pero sin texto/nombre también es 400
        self.assertEqual(self.post("/api/reporte", b"{}", htc="1")[0], 400)
        self.assertEqual(self.post("/api/invitar", b"{}", htc="1")[0], 400)


if __name__ == "__main__":
    unittest.main()
