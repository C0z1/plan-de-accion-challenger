"""Ventana sin barra de título: lista blanca de acciones, sin ventana no hace nada, y el endpoint exige X-HTC."""
import unittest

import ventana


class TestVentana(unittest.TestCase):
    def test_lista_blanca(self):
        with self.assertRaises(ValueError): ventana.accion("borrar")

    def test_sin_ventana_no_hace_nada(self):
        orig, ventana.HWND[0] = ventana.HWND[0], None
        try: self.assertFalse(ventana.accion("cerrar"))
        finally: ventana.HWND[0] = orig

    def test_buscar_no_truena(self):
        self.assertIsNone(ventana.buscar("Racha-ventana-que-no-existe-123"))


if __name__ == "__main__":
    unittest.main()
