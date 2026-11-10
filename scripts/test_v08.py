"""v0.8 (todo gratis): métricas anónimas opt-in, reportes privados e invitar amigos desde la app, sin red."""
import unittest, urllib.error
from unittest import mock

import companion_web as w


class V08(unittest.TestCase):
    def setUp(self): self.viejo = dict(w.ESTADO); w.PING[0] = None; w.USADO.clear()
    def tearDown(self): w.ESTADO.clear(); w.ESTADO.update(self.viejo); w.USADO.clear(); w.BAJADA[0] = 0

    def test_ping_solo_con_metricas_y_una_vez_al_dia(self):
        llamadas = []
        falso = lambda m, ruta, c=None, base=None: llamadas.append((ruta, c)) or {"ok": True}
        with mock.patch.object(w.companion, "backend", falso):
            with mock.patch.object(w.gui, "ajustes", lambda: {"metricas": False}): w.ping()
            self.assertEqual(llamadas, [])  # apagadas por defecto: no sale nada
            w.evento(("fase", "ChampSelect"))
            with mock.patch.object(w.gui, "ajustes", lambda: {"metricas": True}): w.ping(); w.ping()
        self.assertEqual(len(llamadas), 1)
        ruta, c = llamadas[0]
        self.assertEqual((ruta, c["champ_select"], c["revision"], c["version"]), ("/v1/ping", True, False, w.VERSION))
        self.assertEqual(set(c), {"version", "region", "overlay", "champ_select", "revision"})  # nada que identifique

    def test_reporte_ok_y_sin_red(self):
        w.ESTADO.update(fase="Lobby", descarga="falló (3)")
        enviado = {}
        with mock.patch.object(w.companion, "backend", lambda m, r, c=None, base=None: enviado.update(c) or {"ok": True}):
            w.reportar("no carga", "ajustes")
        self.assertIn("falló (3)", enviado["texto"]); self.assertEqual(enviado["fase"], "Lobby")
        self.assertIn("llegó", w.ESTADO["reporte"])
        def caido(*a, **k): raise urllib.error.URLError("x")
        with mock.patch.object(w.companion, "backend", caido): w.reportar("otra", "ajustes")
        self.assertIn("No se pudo", w.ESTADO["reporte"])

    def test_invitar_muestra_el_codigo_o_el_motivo(self):
        def falso(m, ruta, c=None, base=None):
            if m == "POST": return {"nombre": "carla", "email": None, "codigo": "abc123"}
            return [{"nombre": "carla"}]
        with mock.patch.object(w.companion, "backend", falso), mock.patch("builds.bajar", lambda: 0):
            w.invitar("Carla", "")
        self.assertEqual(w.ESTADO["invitacion"]["codigo"], "abc123"); self.assertEqual(w.ESTADO["admin"], [{"nombre": "carla"}])
        def prohibido(m, ruta, c=None, base=None): raise urllib.error.HTTPError(ruta, 403, "no", {}, None)
        with mock.patch.object(w.companion, "backend", prohibido), mock.patch("builds.bajar", lambda: 0):
            w.invitar("beto", "")
        self.assertIn("Solo quien administra", w.ESTADO["invitacion"]["error"]); self.assertIsNone(w.ESTADO["admin"])


if __name__ == "__main__": unittest.main()
