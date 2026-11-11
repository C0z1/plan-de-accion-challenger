"""Overlay en partida: el texto de la franja, el descuento de los timers entre fotos y que la ventana abre y cierra."""
import unittest

import overlay

META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "cs": 71, "rival_cs": 140, "recibido": 1000.0,
        "objetivos": {"dragon": 90, "baron": None}}


class TestPartes(unittest.TestCase):
    def test_franja_y_descuento(self):
        t = [x for x, _ in overlay.partes(META, 1000.0)]  # minuto 0–6: línea primero; dragón solo si sale en ≤ 90 s; barón no
        self.assertEqual(t, ["▼ Nv 11 vs 12 Ahri", "▼ CS 71 vs 140", "Dragón 1:30"])  # ▼: vas abajo, no solo por color
        p = dict(overlay.partes(META, 1045.0))  # 45 s después de la foto: el dragón sale en 0:45, en ámbar y con «!»
        self.assertEqual(p["! Dragón 0:45"], overlay.AMBAR)
        self.assertEqual(p["▼ Nv 11 vs 12 Ahri"], overlay.ROSA)  # nivel abajo: rosa
        self.assertIn("! Dragón 0:00", dict(overlay.partes(META, 2000.0)))  # nunca negativo

    def test_oro_por_linea(self):  # oro en ítems (Tab) contra tu rival, redondeado a 50
        m = {**META, "minuto": 8}  # el oro de línea manda del 6 al 14
        p = dict(overlay.partes({**m, "oro": {"tu": 2500, "rival": 2830}}, 1000.0))
        self.assertEqual(p["▼ Oro -350"], overlay.ROSA)
        self.assertEqual(dict(overlay.partes({**m, "oro": {"tu": 10, "rival": 0}}, 1000.0))["Oro +0"], overlay.TXT)  # parejo: sin ▼
        self.assertFalse(any(x.startswith(("Oro", "▼ Oro")) for x, _ in overlay.partes({**m, "oro": {"tu": 100, "rival": None}}, 1000.0)))

    def test_prioridad_por_fase_y_tope(self):  # F6: nunca más de 4 piezas; cada fase muestra lo suyo, en orden fijo
        oro = {"tu": 5000, "rival": 5600, "equipo": 20000, "equipo_rival": 19000}
        f = lambda minuto, **k: [x for x, _ in overlay.partes({**META, "oro": oro, "muertes14": 1, "minuto": minuto, **k}, 1000.0)]
        for minuto in (3, 9, 18, 30): self.assertLessEqual(len(f(minuto)), overlay.MAX_PIEZAS)
        self.assertEqual(f(9), ["▼ Nv 11 vs 12 Ahri", "▼ CS 71 vs 140", "▼ Oro -600", "Dragón 1:30"])  # 6–14: sin regla aún; orden fijo
        self.assertEqual(f(18), ["Muertes 14–25: 1/2", "Equipo +1000", "Dragón 1:30", "Barón vivo"])  # 14–25: la regla primero
        self.assertNotIn("Barón 7:00", f(18, objetivos={"dragon": 90, "baron": 420}))  # barón solo desde 3 min antes
        self.assertEqual(f(30)[0], "Equipo +1000")

    def test_regla_muertes_14_25(self):  # A3: el contador solo del 14 al 25, ámbar en 2 y rosa con ▼ al pasarse
        c = lambda m, minuto: dict(overlay.partes({**META, "muertes14": m, "minuto": minuto}, 1000.0))
        self.assertEqual(c(1, 15)["Muertes 14–25: 1/2"], overlay.TXT)
        self.assertEqual(c(2, 20)["Muertes 14–25: 2/2"], overlay.AMBAR)
        self.assertEqual(c(3, 24)["▼ Muertes 14–25: 3/2"], overlay.ROSA)
        self.assertFalse(any("Muertes" in x for x in c(3, 26)))
        self.assertFalse(any("Muertes" in x for x in c(None, 10)))

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
