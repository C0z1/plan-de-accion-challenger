"""python -m unittest discover scripts  (sin red, sin cliente y sin abrir ventana)"""
import os, pathlib, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import companion_gui as g

SALIDA = """# Revisión
## Partida por partida (más reciente primero)

| Fecha | Campeón | | Oro @14 | CS @14 | Muertes <14 | Muertes 14–25 | Control wards |
|---|---|---|---|---|---|---|---|
| 11-07 21:36 | Veigar (fuera del pool) | D | -789 | -8 | 3 | 5 | 0 |
| 11-07 21:06 | Ekko | V | +120 | - | 0 | 0 | 1 |
"""


class TestParsear(unittest.TestCase):
    def test_toma_la_mas_reciente(self):
        r = g.parsear_revision(SALIDA)
        self.assertEqual((r["champ"], r["pool"], r["win"], r["oro"], r["m25"]), ("Veigar", False, False, "-789", "5"))

    def test_sin_tabla(self):
        self.assertIsNone(g.parsear_revision("nada"))


if __name__ == "__main__":
    unittest.main()
