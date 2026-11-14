"""Pruebas del backend de Racha sin red ni backend real: companion.acceso(), gui.guardar_acceso() y los POST
de companion_web (/api/acceso, /api/descargar con su candado DESCARGANDO). Nada toca datos/cache/acceso.json
real (gui.REPO se parchea a una carpeta temporal) ni sale a internet.

El caso «descargar.py con una RIOT_KEY que responde 401 cae sola al backend» no se prueba aquí: no hay forma
de redirigir *.api.riotgames.com a un servidor falso. En su lugar se prueba companion.acceso(), que es lo que
descargar.py consulta en ese 401 (companion.py:68)."""
import http.client, http.server, json, os, pathlib, tempfile, threading, time, unittest
from unittest import mock

import companion_web as w

SIN_ENV = {"RACHA_API": "", "RACHA_TOKEN": ""}


class ContadorLock:  # threading.Lock no se deja parchear (atributos de C solo lectura): este cuenta los acquire
    def __init__(self):
        self._l = threading.Lock(); self.adquiridos = 0

    def acquire(self, blocking=True):
        self.adquiridos += 1
        return self._l.acquire(blocking)

    def release(self): self._l.release()
    def locked(self): return self._l.locked()


def escribir_acceso(base, d):
    f = pathlib.Path(base) / "datos" / "cache" / "acceso.json"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(json.dumps(d), encoding="utf-8")
    return f


class Acceso(unittest.TestCase):
    def test_env_racha_api_y_token(self):
        with mock.patch.dict(os.environ, {**SIN_ENV, "RACHA_API": "http://api.local", "RACHA_TOKEN": "t-env"}):
            self.assertEqual(w.companion.acceso(), ("http://api.local", "t-env"))

    def test_archivo_token_solo_usa_api_def(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            escribir_acceso(d, {"token": "t-archivo"})
            self.assertEqual(w.companion.acceso(d), (w.companion.API_DEF, "t-archivo"))

    def test_archivo_api_y_token_sin_barra_final(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            escribir_acceso(d, {"api": "http://api.local/", "token": "t-archivo"})
            self.assertEqual(w.companion.acceso(d), ("http://api.local", "t-archivo"))

    def test_env_gana_al_archivo(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {**SIN_ENV, "RACHA_API": "http://env", "RACHA_TOKEN": "t-env"}):
            escribir_acceso(d, {"api": "http://archivo", "token": "t-archivo"})
            self.assertEqual(w.companion.acceso(d), ("http://env", "t-env"))

    def test_sin_nada_none(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            self.assertIsNone(w.companion.acceso(d))

    def test_archivo_roto_none(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV):
            f = pathlib.Path(d) / "datos" / "cache" / "acceso.json"
            f.parent.mkdir(parents=True, exist_ok=True); f.write_text("{no json", encoding="utf-8")
            self.assertIsNone(w.companion.acceso(d))


class GuardarAcceso(unittest.TestCase):
    def test_codigos_validos_se_guardan(self):
        for tok in ("codigo-ok", "ABC123", "a-b-c-d", "a" * 64):
            with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
                w.gui.guardar_acceso(tok)  # no lanza
                f = pathlib.Path(d) / "datos" / "cache" / "acceso.json"
                self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["token"], tok)

    def test_codigos_invalidos_valueerror(self):
        for tok in ("abc", "ab/cd", "ab cd", "abc_", "", "a" * 65, 123, None, ["x"]):
            with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
                with self.assertRaises(ValueError):
                    w.gui.guardar_acceso(tok)
                self.assertFalse((pathlib.Path(d) / "datos" / "cache" / "acceso.json").exists())

    def test_guarda_sin_pisar_lo_que_habia(self):
        with tempfile.TemporaryDirectory() as d:
            escribir_acceso(d, {"api": "http://x"})
            with mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
                w.gui.guardar_acceso("codigo-ok")
            f = pathlib.Path(d) / "datos" / "cache" / "acceso.json"
            self.assertEqual(json.loads(f.read_text(encoding="utf-8")), {"api": "http://x", "token": "codigo-ok"})


class PuedeDescargar(unittest.TestCase):
    def test_con_token_en_archivo_true(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV), \
                mock.patch.object(w.gui, "REPO", pathlib.Path(d)), mock.patch.object(w.gui, "hay_key", return_value=False):
            escribir_acceso(d, {"token": "codigo-ok"})
            self.assertTrue(w.gui.puede_descargar())

    def test_sin_key_ni_token_false(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, SIN_ENV), \
                mock.patch.object(w.gui, "REPO", pathlib.Path(d)), mock.patch.object(w.gui, "hay_key", return_value=False):
            self.assertFalse(w.gui.puede_descargar())


class PostBackend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), w.H)
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls): cls.srv.shutdown()

    def setUp(self):
        self.viejo = dict(w.ESTADO)
        p = mock.patch.object(w, "primera_vez"); p.start(); self.addCleanup(p.stop)  # su hilo sobreviviría a la prueba y bajaría partidas reales al repo

    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def post(self, path, cuerpo=b"{}", cab=None):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_port, timeout=5)
        c.request("POST", path, cuerpo, cab or {"X-HTC": "1"})
        r = c.getresponse(); b = r.read(); return r.status, b

    def test_acceso_valido_200_y_aviso(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
            st, _ = self.post("/api/acceso", json.dumps({"token": "codigo-ok"}).encode())
        self.assertEqual(st, 200)
        self.assertEqual(w.ESTADO["descarga"], "Código guardado. Ya puedes descargar tus partidas.")

    def test_acceso_invalido_400(self):
        for token in ("abc", "ab cd", "ab/cd"):
            with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
                self.assertEqual(self.post("/api/acceso", json.dumps({"token": token}).encode())[0], 400)
        with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)):
            self.assertEqual(self.post("/api/acceso", b"{mal json")[0], 400)

    def test_acceso_sin_x_htc_403(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(w.gui, "REPO", pathlib.Path(d)), \
                mock.patch.object(w.gui, "guardar_acceso") as g:
            st, _ = self.post("/api/acceso", json.dumps({"token": "codigo-ok"}).encode(), cab={"Content-Type": "application/json"})
            self.assertEqual(st, 403); g.assert_not_called()

    def test_descargar_codigo_0_o_3_refresca(self):
        for code in (0, 3):
            with mock.patch.object(w.gui, "puede_descargar", return_value=True), \
                    mock.patch.object(w.gui, "descargar", return_value=(code, "listo")) as sc, \
                    mock.patch.object(w, "refrescar") as rf:
                w.descargar_todo()
                self.assertEqual(sc.call_args[0][0], "todo")  # sin gui.script: no toca sys.argv ni stdout del proceso
                rf.assert_called_once(); self.assertIn("al día", w.ESTADO["descarga"])

    def test_descargar_codigo_malo_no_refresca(self):
        with mock.patch.object(w.gui, "puede_descargar", return_value=True), \
                mock.patch.object(w.gui, "descargar", return_value=(1, "falló")), mock.patch.object(w, "registrar_salud"), \
                mock.patch.object(w, "refrescar") as rf:
            w.descargar_todo(); rf.assert_not_called(); self.assertEqual(w.ESTADO["descarga"], "falló")

    def test_descargar_sin_puede_no_corre_script(self):
        import cliente_v5  # sin invitación ni key: no corre descargar.py; baja las 20 del cliente (simulado: no toca tu cliente)
        with mock.patch.object(w, "DESCARGANDO", threading.Lock()), mock.patch.object(w.gui, "es_base", return_value=True), \
                mock.patch.object(w.gui, "puede_descargar", return_value=False), mock.patch.object(w.gui, "script") as sc, \
                mock.patch.object(cliente_v5, "descargar", return_value=(0, "Tus partidas del cliente ya estaban bajadas.")) as cl:
            w.descargar_todo(); sc.assert_not_called(); cl.assert_called_once()
            self.assertIn("ya estaban bajadas", w.ESTADO["descarga"])

    def test_descargar_dos_post_encola_una_vez(self):  # 0.30: una sola cola; el 2.º pedido igual no se duplica
        import queue
        with mock.patch.object(w, "COLA", queue.PriorityQueue()), mock.patch.object(w, "EN_COLA", set()):
            self.post("/api/descargar", b"{}"); self.post("/api/descargar", b"{}")
            self.assertEqual(w.COLA.qsize(), 1)

    def test_progreso_y_refresco_en_tiempo_real(self):
        def falso(n, raw, rid, eco):
            for a in range(1, 61): eco(f"progreso {a}/60")
            eco("pausa 12"); estados.append(w.ESTADO["descarga"]); eco("detalles 3/40"); estados.append(w.ESTADO["descarga"])
            return 0, "listo"
        estados = []
        with mock.patch.object(w.gui, "puede_descargar", return_value=True), mock.patch.object(w.gui, "descargar", side_effect=falso), \
             mock.patch.object(w, "refrescar") as rf, mock.patch.object(w.threading, "Thread") as th:
            w.descargar_todo()
        self.assertEqual(th.call_count, 2)  # refrescos a mitad de descarga: cada 25 partidas
        self.assertIn("límite de Riot", estados[0]); self.assertIn("3 de 40", estados[1]); rf.assert_called_once()

    def test_encolar_sin_trabajador_no_baja(self):  # las pruebas y la demo nunca bajan nada
        import queue
        with mock.patch.object(w, "COLA", queue.PriorityQueue()), mock.patch.object(w, "EN_COLA", set()), \
             mock.patch.object(w.gui, "descargar") as d:
            w.encolar(1); w.encolar(1); w.encolar(0, n=5)
            self.assertEqual([x[0] for x in sorted(w.COLA.queue)], [0, 1]); d.assert_not_called()

if __name__ == "__main__":
    unittest.main()
