"""Pruebas de la cuenta en la nube (scripts/nube.py) y sus rutas en companion_web.py, sin red y sin tocar
datos/cache/sesion.json real: nube.pedir se parchea y nube.SESION_F apunta a una carpeta temporal."""
import base64, hashlib, http.client, http.server, io, json, os, pathlib, tempfile, threading, time, unittest
import urllib.error, urllib.parse
from unittest import mock

import companion_web as w
import nube

SIN_ENV = {"RACHA_API": "", "RACHA_TOKEN": ""}
TOKEN = "a" * 64


def escribir_sesion(base, d):
    f = pathlib.Path(base) / "datos" / "cache" / "sesion.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d), encoding="utf-8")
    return f


def escribir_acceso(base, d):
    f = pathlib.Path(base) / "datos" / "cache" / "acceso.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d), encoding="utf-8")
    return f


def http_error(code, cuerpo=b"{}"):
    return urllib.error.HTTPError("http://x", code, "error", {}, io.BytesIO(cuerpo))


class Iniciar(unittest.TestCase):
    def setUp(self): nube.PENDIENTE.clear()
    def tearDown(self): nube.PENDIENTE.clear()

    def test_url_de_google_con_pkce_s256(self):
        with mock.patch.object(nube, "pedir", return_value={"google_client_id": "CID"}):
            url = nube.iniciar(8765)
        self.assertTrue(url.startswith("https://accounts.google.com/o/oauth2/v2/auth?"))
        q = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        self.assertEqual(q["client_id"], ["CID"])
        self.assertEqual(q["code_challenge_method"], ["S256"])
        self.assertEqual(q["redirect_uri"], ["http://127.0.0.1:8765/oauth"])
        self.assertEqual(q["prompt"], ["select_account"])
        state = q["state"][0]
        self.assertIn(state, nube.PENDIENTE)  # el state queda pendiente con su verifier
        verifier = nube.PENDIENTE[state][0]
        esperado = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(q["code_challenge"][0], esperado)

    def test_sin_client_id_none(self):
        with mock.patch.object(nube, "pedir", return_value={}):
            self.assertIsNone(nube.iniciar(8765))
        self.assertEqual(nube.PENDIENTE, {})


class Completar(unittest.TestCase):
    def setUp(self): nube.PENDIENTE.clear()
    def tearDown(self): nube.PENDIENTE.clear()

    def test_state_desconocido_valueerror(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(nube, "SESION_F", pathlib.Path(d) / "sesion.json"), \
                mock.patch.object(nube, "pedir") as p:
            with self.assertRaises(ValueError):
                nube.completar("code", "no-existe", 8765)
            p.assert_not_called()

    def test_state_vencido_valueerror(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(nube, "SESION_F", pathlib.Path(d) / "sesion.json"), \
                mock.patch.object(nube, "pedir") as p:
            nube.PENDIENTE["s"] = ("verifier", time.time() - 700)
            with self.assertRaises(ValueError):
                nube.completar("code", "s", 8765)
            p.assert_not_called()

    def test_403_del_backend_valueerror_con_su_mensaje(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(nube, "SESION_F", pathlib.Path(d) / "sesion.json"):
            nube.PENDIENTE["s"] = ("verifier", time.time())
            with mock.patch.object(nube, "pedir", side_effect=http_error(403, b'{"error": "Google rechazo el login"}')):
                with self.assertRaisesRegex(ValueError, "Google rechazo el login"):
                    nube.completar("code", "s", 8765)

    def test_exito_guarda_sesion_sin_perder_campos(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "sesion.json"
            nube.PENDIENTE["s"] = ("verifier", time.time())
            with mock.patch.object(nube, "SESION_F", f), mock.patch.object(nube.gui, "AJUSTES_F", pathlib.Path(d) / "ajustes.json"), \
                    mock.patch.object(nube, "pedir", return_value={"token": TOKEN, "email": "a@b.c", "nombre": "Cozi"}) as p:
                s = nube.completar("code", "s", 8765)
            self.assertEqual(s["token"], TOKEN)
            guardado = json.loads(f.read_text(encoding="utf-8"))
            self.assertEqual(guardado, {"token": TOKEN, "email": "a@b.c", "nombre": "Cozi", "sync": None})
            self.assertEqual(set(guardado), {"token", "email", "nombre", "sync"})
            # el POST lleva code, verifier y el redirect de la app
            self.assertEqual(p.call_args_list[0].args[:2], ("POST", "/v1/login"))
            self.assertEqual(p.call_args_list[0].args[2], {"code": "code", "verifier": "verifier", "redirect_uri": "http://127.0.0.1:8765/oauth"})


class Sincronizar(unittest.TestCase):
    def setUp(self): nube.PENDIENTE.clear()
    def tearDown(self): nube.PENDIENTE.clear()

    def test_sin_sesion_none(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(nube, "SESION_F", pathlib.Path(d) / "sesion.json"), \
                mock.patch.object(nube, "pedir") as p:
            self.assertIsNone(nube.sincronizar())
            p.assert_not_called()

    def test_manda_riot_ajustes_y_resumenes(self):
        with tempfile.TemporaryDirectory() as d:
            f = escribir_sesion(d, {"token": TOKEN, "email": "a", "nombre": "n", "sync": None})
            partidas = [dict(campeon="sin archivo")]  # sin «archivo»: no sube
            partidas += [dict(archivo=f"LA1_{i}", t=1000 + i, campeon="Sylas", rival="Zed", win=True,
                              kda="5/4/7", score=5, puesto_eq=1, fecha="hoy") for i in range(55)]  # 55: se recortan a 50
            rendimiento = {"resumen": {"partidas": partidas}}
            with mock.patch.object(nube, "SESION_F", f), mock.patch.object(nube, "pedir", return_value={}) as p:
                nube.sincronizar(rendimiento, "cozi#1134", "LAN", {"overlay": True})
            llamadas = p.call_args_list
            self.assertEqual([c.args[:2] for c in llamadas],
                             [("PUT", "/v1/yo/riot"), ("PUT", "/v1/yo/cuentas"), ("PUT", "/v1/yo/ajustes"), ("PUT", "/v1/yo/resumenes")])
            self.assertEqual(llamadas[0].args[2], {"riot_id": "cozi#1134", "region": "la1"})  # LAN → la1
            self.assertEqual(llamadas[1].args[2], {"riot_id": "cozi#1134", "region": "la1"})  # y queda vinculada a tu Google
            self.assertEqual(llamadas[2].args[2], {"overlay": True})
            filas = llamadas[3].args[2]
            self.assertEqual([f["match_id"] for f in filas], [f"LA1_{i}" for i in range(50)])  # máx. 50 y sin la partida sin archivo
            self.assertEqual((filas[0]["ts"], filas[0]["cuenta"]), (1000, "cozi#1134"))
            self.assertEqual(filas[0]["resumen"], {"campeon": "Sylas", "rival": "Zed", "win": True, "kda": "5/4/7",
                                                   "score": 5, "puesto_eq": 1, "fecha": "hoy"})

    def test_otra_cuenta_se_vincula_sin_pisar_la_principal(self):
        with tempfile.TemporaryDirectory() as d:
            f = escribir_sesion(d, {"token": TOKEN, "email": "a", "nombre": "n", "sync": None})
            r = {"cuentas": [{"riot_id": "cozi#1134"}, {"riot_id": "Alt#LAN"}]}
            with mock.patch.object(nube, "SESION_F", f), mock.patch.object(nube, "pedir", return_value=r) as p:
                nube.sincronizar({"resumen": {"partidas": [dict(archivo="LA1_1", t=1)]}}, "Alt#LAN", "la1", None, principal=False)
                self.assertEqual(nube.sesion()["cuentas"], ["cozi#1134", "Alt#LAN"])
            self.assertEqual([c.args[1] for c in p.call_args_list], ["/v1/yo/cuentas", "/v1/yo/resumenes"])  # sin /v1/yo/riot
            self.assertEqual(p.call_args_list[1].args[2][0]["cuenta"], "Alt#LAN")

    def test_401_borra_la_sesion_local(self):
        with tempfile.TemporaryDirectory() as d:
            f = escribir_sesion(d, {"token": TOKEN, "email": "a", "nombre": "n", "sync": None})
            with mock.patch.object(nube, "SESION_F", f), mock.patch.object(nube, "pedir", side_effect=http_error(401)):
                self.assertIsNone(nube.sincronizar(cuenta="cozi#1134", region="LAN"))
            self.assertFalse(f.exists())


class NubePublica(unittest.TestCase):
    def test_nunca_incluye_el_token(self):
        s = {"token": TOKEN, "email": "a@b.c", "nombre": "Cozi", "sync": 123.0, "extra": "x"}
        with mock.patch.object(nube, "sesion", return_value=s):
            self.assertEqual(w.nube_publica(), {"email": "a@b.c", "nombre": "Cozi", "sync": 123.0, "cuentas": None})
            self.assertNotIn("token", w.nube_publica())

    def test_sin_sesion_none(self):
        with mock.patch.object(nube, "sesion", return_value=None):
            self.assertIsNone(w.nube_publica())


class WebNube(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown(); cls.srv.server_close()

    def get(self, path):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("GET", path); r = c.getresponse(); b = r.read(); return r.status, b

    def post(self, path, cab):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", path, b"{}", cab); r = c.getresponse(); b = r.read(); return r.status, b

    def test_oauth_state_malo_200_con_mensaje_escapado(self):
        with mock.patch.object(nube, "completar", side_effect=ValueError("<script>alert(1)</script>")):
            st, b = self.get("/oauth?code=c&state=malo")
        self.assertEqual(st, 200)
        self.assertIn(b"&lt;script&gt;alert(1)&lt;/script&gt;", b)
        self.assertNotIn(b"<script>", b)

    def test_oauth_state_desconocido_200_con_aviso(self):
        nube.PENDIENTE.clear()
        st, b = self.get("/oauth?code=c&state=malo")
        self.assertEqual(st, 200)
        self.assertIn("venció".encode(), b)

    def test_post_google_sin_x_htc_403(self):
        with mock.patch.object(nube, "iniciar") as ini:
            st, _ = self.post("/api/google", {"Content-Type": "application/json"})
            self.assertEqual(st, 403)
            ini.assert_not_called()

    def test_post_google_sin_client_id_503(self):
        with mock.patch.object(nube, "iniciar", return_value=None), mock.patch.object(w.webbrowser, "open") as abrir:
            st, _ = self.post("/api/google", {"X-HTC": "1"})
            self.assertEqual(st, 503)
            abrir.assert_not_called()


class AccesoSesion(unittest.TestCase):
    def test_usa_el_token_de_sesion_si_no_hay_codigo(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            escribir_sesion(d, {"token": TOKEN, "email": "a"})
            self.assertEqual(w.companion.acceso(d), (w.companion.API_DEF, TOKEN))

    def test_el_codigo_gana_a_la_sesion(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            escribir_sesion(d, {"token": TOKEN})
            escribir_acceso(d, {"token": "codigo-ok"})
            self.assertEqual(w.companion.acceso(d), (w.companion.API_DEF, "codigo-ok"))

    def test_sesion_rota_none(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            f = pathlib.Path(d) / "datos" / "cache" / "sesion.json"
            f.parent.mkdir(parents=True, exist_ok=True); f.write_text("{no json", encoding="utf-8")
            self.assertIsNone(w.companion.acceso(d))


if __name__ == "__main__":
    unittest.main()
