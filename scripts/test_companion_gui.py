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


class TestTrabajador(unittest.TestCase):
    def test_banner_de_nivel_una_vez(self):
        import json, queue
        c = g.companion
        d = json.loads((AQUI / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))
        orig = c.lcu, c.vivo, c.capturar, g.time.sleep, g.time.time
        vueltas = iter(range(3))
        def dormir(_):  # el bucle no termina solo: KeyboardInterrupt no lo atrapa su except Exception
            if next(vueltas, None) is None: raise KeyboardInterrupt
        reloj = iter(range(0, 10_000, 100))
        c.lcu, c.vivo, c.capturar = (lambda path: "InProgress"), (lambda: d), (lambda a, f: a)
        g.time.sleep, g.time.time = dormir, (lambda: next(reloj))
        q = queue.Queue()
        try:
            with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
        finally: c.lcu, c.vivo, c.capturar, g.time.sleep, g.time.time = orig
        avisos = [e[1] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(len(avisos), 1); self.assertIn("abajo de Zed", avisos[0])


if __name__ == "__main__":
    unittest.main()
