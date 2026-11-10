"""Overlay en partida: el texto de la franja, el descuento de los timers entre fotos y que la ventana abre y cierra."""
import unittest

import overlay

META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "cs": 71, "rival_cs": 140, "recibido": 1000.0,
        "objetivos": {"dragon": 90, "baron": None}}


class TestPartes(unittest.TestCase):
    def test_franja_y_descuento(self):
        t = [x for x, _ in overlay.partes(META, 1000.0)]
        self.assertEqual(t, ["Dragón 1:30", "Barón vivo", "▼ Nv 11 vs 12 Ahri", "▼ CS 71 vs 140"])  # ▼: vas abajo, no solo por color
        p = dict(overlay.partes(META, 1045.0))  # 45 s después de la foto: el dragón sale en 0:45, en ámbar
        self.assertEqual(p["Dragón 0:45"], overlay.AMBAR)
        self.assertEqual(p["▼ Nv 11 vs 12 Ahri"], overlay.ROSA)  # nivel abajo: rosa
        self.assertIn("Dragón 0:00", dict(overlay.partes(META, 2000.0)))  # nunca negativo

    def test_sin_datos(self):
        self.assertEqual(overlay.partes(None, 0), [])
        self.assertEqual([x for x, _ in overlay.partes({"objetivos": {}}, 0)], [])


class TestVentana(unittest.TestCase):
    def test_abre_y_cierra_fuera_de_pantalla(self):
        try: import tkinter; tkinter.Tk().destroy()
        except Exception: self.skipTest("sin pantalla")  # CI Ubuntu sin display
        vueltas = iter(range(3))
        overlay.correr(lambda: {"fase": "InProgress", "meta": META}, lambda: next(vueltas, None) is not None, x=5)


if __name__ == "__main__":
    unittest.main()
