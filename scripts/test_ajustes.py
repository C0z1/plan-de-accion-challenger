"""Ajustes_Vino: los ajustes se guardan en disco, solo claves conocidas, y un archivo roto no tumba nada."""
import pathlib, tempfile, unittest

import companion_gui as g


class TestAjustes(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory(); self.orig = g.AJUSTES_F
        g.AJUSTES_F = pathlib.Path(self.d.name) / "ajustes.json"

    def tearDown(self):
        g.AJUSTES_F = self.orig; self.d.cleanup()

    def test_por_defecto_todo_encendido(self):
        self.assertEqual(g.ajustes(), g.AJUSTES_DEF)

    def test_guarda_y_lee(self):
        g.guardar_ajuste("aviso_muertes", False)
        self.assertFalse(g.ajustes()["aviso_muertes"]); self.assertTrue(g.ajustes()["overlay"])

    def test_lista_blanca(self):
        with self.assertRaises(ValueError): g.guardar_ajuste("../../algo", True)
        with self.assertRaises(ValueError): g.guardar_ajuste("overlay", "si")

    def test_archivo_roto(self):
        g.AJUSTES_F.write_text("{roto", encoding="utf-8")
        self.assertEqual(g.ajustes(), g.AJUSTES_DEF)


if __name__ == "__main__":
    unittest.main()
