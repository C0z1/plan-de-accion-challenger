"""Pruebas de DeepSeek del launcher (otro_htc y main): tarea de Opus, turno 9 iter 8."""
import pathlib, socket, tempfile, unittest
from unittest import mock

import companion_web as w


class OtroHtc(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.port = pathlib.Path(self.tmp.name) / "htc.port"
        self.addCleanup(self.tmp.cleanup)

    def test_basura_en_el_puerto_es_none(self):
        self.port.write_text("abc")
        with mock.patch.object(w, "PUERTO", self.port):
            self.assertIsNone(w.otro_htc())  # int("abc") -> ValueError, atrapado

    def test_archivo_inexistente_es_none(self):
        with mock.patch.object(w, "PUERTO", self.port):  # no existe: FileNotFoundError
            self.assertIsNone(w.otro_htc())

    def test_puerto_muerto_es_none(self):
        with socket.socket() as s:  # puerto libre recién cerrado -> conexión rechazada
            s.bind(("127.0.0.1", 0)); puerto = s.getsockname()[1]
        self.port.write_text(str(puerto))
        with mock.patch.object(w, "PUERTO", self.port):
            self.assertIsNone(w.otro_htc())  # URLError -> OSError, atrapado


class MainConHtcVivo(unittest.TestCase):
    def test_sin_fondo_abre_el_otro_y_no_sirve(self):
        url = "http://127.0.0.1:9/"
        with mock.patch.object(w, "otro_htc", return_value=url) as otro, \
                mock.patch.object(w, "abrir") as a, \
                mock.patch.object(w.http.server, "ThreadingHTTPServer") as srv:
            w.main([])
            otro.assert_called_once()
            a.assert_called_once_with(url)  # abre la ventana del HTC que ya corre
            srv.assert_not_called()         # y sale sin abrir otro servidor

    def test_fondo_con_htc_vivo_no_abre_ni_sirve(self):
        url = "http://127.0.0.1:9/"
        with mock.patch.object(w, "otro_htc", return_value=url), \
                mock.patch.object(w, "abrir") as a, \
                mock.patch.object(w.http.server, "ThreadingHTTPServer") as srv:
            w.main(["--fondo"])
            a.assert_not_called()  # --fondo no abre ventana: otro arranque sale en silencio
            srv.assert_not_called()
