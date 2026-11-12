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

    def test_caja_max(self):  # 1080p con barra de tareas de 48 px, bordes de 7 px y barra de Edge de 37 px (medido en la PC del usuario)
        x, y, an, al = ventana.caja_max((0, 0, 1920, 1032), 7, 37, 7)
        self.assertEqual((x, y, an, al), (-7, -37, 1934, 1076))
        self.assertEqual((y + 37, y + al - 7), (0, 1032))  # recortada (de 37 al borde de abajo): llena justo el área de trabajo
        self.assertEqual(ventana.caja_max((1920, 0, 3840, 1080), 9, 46, 9), (1911, -46, 1938, 1135))  # 2.º monitor, 125 %


if __name__ == "__main__":
    unittest.main()
