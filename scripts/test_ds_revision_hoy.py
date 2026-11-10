"""Revisión de los cambios de hoy (backend + amigo nuevo + 304): bugs reales, cada uno con una prueba
@unittest.expectedFailure que documenta el comportamiento actual. No toca datos/cache/acceso.json ni red."""
import json, os, pathlib, tempfile, unittest
from unittest import mock

import companion_web as w


class RevisionHoy(unittest.TestCase):
    def setUp(self): self.viejo = dict(w.ESTADO)
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo)

    def test_una_partida_malformada_no_vacia_el_rendimiento(self):
        # score.partidas no protege por archivo: un JSON sin "info" (KeyError) tira rendimiento() entero → None,
        # y Perfil/Partidas/Errores/Campeones quedan vacíos (el timeline roto sí se saltaba por partida).
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"DATOS_DIR": d}):
            pathlib.Path(d, "perfil.json").write_text(json.dumps({"account": {"gameName": "x", "tagLine": "1", "puuid": "p"}}))
            pathlib.Path(d, "LA1_2.json").write_text('{"noinfo": 1}')
            r = w.rendimiento_rapido(None, pathlib.Path(d) / "c.json")
            self.assertIsNotNone(r)  # hoy: None

    def test_descargar_no_pisa_la_cuenta_de_otro(self):
        # descargar_todo no consulta ajeno: con otra cuenta en el cliente, «Descargar» sobreescribe perfil.json
        # con esa cuenta ajena (los match de la dueña quedan huérfanos y ya no se muestran como suyos).
        with mock.patch.object(w.gui, "puede_descargar", return_value=True), \
                mock.patch.object(w.gui, "ajeno", return_value=True), \
                mock.patch.object(w.gui, "script", return_value=(0, "listo")) as sc, \
                mock.patch.object(w, "refrescar"):
            w.descargar_todo()
            sc.assert_not_called()  # hoy: sí descarga y pisa la cuenta

    def test_primera_vez_no_descarga_sin_cliente(self):
        # primera_vez se lanza al arrancar (--fondo con Windows arranca antes que LoL) y no mira si el cliente
        # está abierto: descargar.py sale «Falta tu cuenta» y no se reintenta al abrir LoL.
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"DATOS_DIR": d}), \
                mock.patch.object(w.gui, "puede_descargar", return_value=True), \
                mock.patch.object(w.companion, "lcu", return_value=None), \
                mock.patch.object(w, "descargar_todo") as dt:
            w.primera_vez()
            dt.assert_not_called()  # hoy: sí dispara la descarga sin cliente

    def test_sin_partidas_devuelve_resumen_vacio(self):
        # contraste con el bug de arriba: perfil válido y 0 partidas → resumen vacío (no None).
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, {"DATOS_DIR": d}):
            pathlib.Path(d, "perfil.json").write_text(json.dumps({"account": {"gameName": "x", "tagLine": "1", "puuid": "p"}}))
            r = w.rendimiento_rapido(None, pathlib.Path(d) / "c.json")
            self.assertIsNotNone(r); self.assertEqual(r["resumen"]["partidas"], [])


if __name__ == "__main__":
    unittest.main()
