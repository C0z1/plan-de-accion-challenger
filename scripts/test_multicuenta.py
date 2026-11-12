"""Multi-cuenta: la cuenta del dueño usa datos/raw; otra cuenta del cliente, datos/cuentas/<puuid>/raw, sin tocar la base."""
import json, os, pathlib, sys, tempfile, unittest
from unittest import mock

import companion_gui as gui

PUUID = "a" * 40


class TestMulticuenta(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp()); base = self.tmp / "raw"; base.mkdir()
        (base / "perfil.json").write_text(json.dumps({"account": {"gameName": "cozi", "tagLine": "1134"}}))
        (base / "LA1_1.json").write_text("{}")
        self.p = [mock.patch.object(gui, "BASE", base), mock.patch.object(gui, "RAW", base), mock.patch.dict(os.environ, {"DATOS_DIR": str(base)})]
        for p in self.p: p.start()
        import builds; self.braw = builds.RAW
        self.base = base

    def tearDown(self):
        import builds; builds.RAW = self.braw
        for p in self.p: p.stop()

    def test_otra_cuenta_su_carpeta(self):
        self.assertTrue(gui.usar_cuenta("Zeriously#cozi", PUUID))
        self.assertEqual(gui.RAW, self.tmp / "cuentas" / PUUID / "raw")
        self.assertEqual(os.environ["DATOS_DIR"], str(gui.RAW)); self.assertFalse(gui.es_base())
        self.assertFalse(gui.ajeno("Zeriously#cozi"))  # su carpeta: ya no se oculta nada
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), ["LA1_1.json", "perfil.json"])  # la base intacta

    def test_volver_al_dueno(self):
        gui.usar_cuenta("Zeriously#cozi", PUUID)
        self.assertTrue(gui.usar_cuenta("COZI#1134", "b" * 40)); self.assertEqual(gui.RAW, self.base); self.assertTrue(gui.es_base())
        self.assertFalse(gui.usar_cuenta("cozi#1134", "b" * 40))  # misma carpeta: no cambia nada

    def test_sin_puuid_o_sin_dueno_queda_la_base(self):
        self.assertFalse(gui.usar_cuenta("Zeriously#cozi", None)); self.assertTrue(gui.ajeno("Zeriously#cozi"))  # como antes (hallazgo 20)
        self.assertFalse(gui.usar_cuenta("Otro#1", "../../x"))  # puuid raro: no se usa como carpeta
        (self.base / "perfil.json").unlink()
        self.assertFalse(gui.usar_cuenta("Amigo#LAN", PUUID))  # amigo recién instalado: su historial va a la base

    def test_recarga_draft(self):
        sys.modules.setdefault("draft", mock.Mock())
        gui.usar_cuenta("Zeriously#cozi", PUUID); self.assertNotIn("draft", sys.modules)


if __name__ == "__main__":
    unittest.main()
