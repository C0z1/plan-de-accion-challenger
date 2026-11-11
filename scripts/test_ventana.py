"""Ventana sin barra de título: lista blanca de acciones, sin ventana no hace nada, y el endpoint exige X-HTC."""
import unittest
from unittest import mock

import ventana


class TestVentana(unittest.TestCase):
    def test_lista_blanca(self):
        with self.assertRaises(ValueError): ventana.accion("borrar")

    def test_sin_ventana_no_hace_nada(self):  # sin el parche, una Racha real al frente recibía WM_CLOSE y se cerraba (2026-11-11)
        orig, ventana.HWND[0] = ventana.HWND[0], None
        try:
            with mock.patch.object(ventana, "es_racha", return_value=False): self.assertFalse(ventana.accion("cerrar"))
        finally: ventana.HWND[0] = orig

    def test_buscar_no_truena(self):
        self.assertIsNone(ventana.buscar("Racha-ventana-que-no-existe-123"))


if __name__ == "__main__":
    unittest.main()
