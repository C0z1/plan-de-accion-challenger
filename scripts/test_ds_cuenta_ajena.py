"""Pruebas del hallazgo 20 (DeepSeek, 2026-11-12): refrescar decide si la cuenta es ajena ANTES de
calcular rendimiento_rapido(); si la cuenta del cliente llega mientras calcula, el historial ajeno
queda en ESTADO[rendimiento] y ESTADO[previa] con el rival frecuente de esa otra cuenta.
Sin red, sin cliente de LoL ni key."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixtures de draft

import companion_web as w  # noqa: E402


class CuentaAjena(unittest.TestCase):
    def setUp(self):
        self.viejo = dict(w.ESTADO)
        self.cuenta = w.gui.CUENTA[0]

    def tearDown(self):
        w.ESTADO.clear()
        w.ESTADO.update(self.viejo)
        w.gui.CUENTA[0] = self.cuenta

    def test_cuenta_ajena_que_llega_durante_el_calculo_no_mancha_rendimiento_ni_previa(self):
        def otra_cuenta():
            w.gui.CUENTA[0] = "Zeriously#cozi"  # la cuenta del cliente llega mientras calcula
            return {"vistas": {}}

        w.ESTADO["previa"] = {"pos": "MIDDLE"}
        with mock.patch.object(w.gui, "dueno", return_value="cozi#1134"), \
             mock.patch.object(w, "rendimiento_rapido", side_effect=otra_cuenta), \
             mock.patch.object(w, "aplicar_coach", side_effect=lambda r: r), \
             mock.patch.object(w, "vistas_previas"), \
             mock.patch.object(w, "tus_builds"), \
             mock.patch.object(w, "builds_del_backend"), \
             mock.patch.object(w, "sync_nube"):
            w.refrescar()
        self.assertIsNone(w.ESTADO["rendimiento"])
        self.assertIsNone(w.ESTADO["previa"])

    def test_cuenta_propia_desde_el_inicio_deja_el_rendimiento(self):
        w.gui.CUENTA[0] = "cozi#1134"  # tu propia cuenta desde el inicio
        with mock.patch.object(w.gui, "dueno", return_value="cozi#1134"), \
             mock.patch.object(w, "rendimiento_rapido", return_value={"vistas": {}}), \
             mock.patch.object(w, "aplicar_coach", side_effect=lambda r: r), \
             mock.patch.object(w, "vistas_previas"), \
             mock.patch.object(w, "tus_builds"), \
             mock.patch.object(w, "builds_del_backend"), \
             mock.patch.object(w, "sync_nube"):
            w.refrescar()
        self.assertEqual(w.ESTADO["rendimiento"], {"vistas": {}})

    def test_ajena_desde_el_inicio_deja_rendimiento_y_previa_none(self):
        w.gui.CUENTA[0] = "Zeriously#cozi"  # otra cuenta desde el principio
        with mock.patch.object(w.gui, "dueno", return_value="cozi#1134"), \
             mock.patch.object(w, "vistas_previas") as vp, \
             mock.patch.object(w, "builds_del_backend"), \
             mock.patch.object(w, "sync_nube"):
            w.refrescar()
        self.assertIsNone(w.ESTADO["rendimiento"])
        self.assertIsNone(w.ESTADO["previa"])
        vp.assert_called_once_with(None)  # «ultima» sí se calcula aunque la cuenta sea ajena (ronda 4)

    def _r(self):
        return {"vistas": {"pos": "MIDDLE", "draft": {"MIDDLE": {"frecuentes": [{"rival": "Zed"}]}}}}

    def _vistas_previas(self, recomendaciones):
        import json, tempfile
        foto = (pathlib.Path(w.__file__).parent / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as d, \
             mock.patch.object(w.gui, "dueno", return_value="cozi#1134"), \
             mock.patch.object(w.gui, "recomendaciones", side_effect=recomendaciones), \
             mock.patch.object(w.companion, "VIVO", pathlib.Path(d)):
            pathlib.Path(d, "20261110-1.jsonl").write_text(json.dumps(json.loads(foto)) + "\n", encoding="utf-8")
            w.vistas_previas(self._r())

    def test_cuenta_que_se_vuelve_ajena_dentro_de_recomendaciones_deja_previa_none_y_conserva_ultima(self):
        w.gui.CUENTA[0] = "cozi#1134"  # propia al entrar

        def se_vuelve_ajena(pos, rivales):
            w.gui.CUENTA[0] = "Zeriously#cozi"  # la cuenta ajena llega mientras recomienda
            return [(r, None) for r in rivales]

        self._vistas_previas(se_vuelve_ajena)
        self.assertIsNone(w.ESTADO["previa"])
        self.assertIsNotNone(w.ESTADO["ultima"])

    def test_propia_conserva_previa(self):
        w.gui.CUENTA[0] = "cozi#1134"
        self._vistas_previas(lambda pos, rivales: [(r, None) for r in rivales])
        self.assertIsNotNone(w.ESTADO["previa"])
        self.assertTrue(w.ESTADO["previa"].get("previa"))


if __name__ == "__main__":
    unittest.main()
