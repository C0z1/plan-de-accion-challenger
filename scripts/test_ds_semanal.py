"""Pruebas de scripts/semanal.py (plan semanal): funciones puras con datos sintéticos, sin red."""
import pathlib, sys, unittest
from datetime import date

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import semanal  # noqa: E402

HOY = date(2026, 11, 10)  # martes; su lunes es 2026-11-09
MS = semanal._medianoche(semanal._lunes(HOY))
HORA = 3600 * 1000
DIA = 86400 * 1000


def g(t, win=True, campeon="Sylas", rival="Zed", oro14=500, archivo=None):
    return dict(t=t, win=win, campeon=campeon, rival=rival, oro14=oro14,
                archivo=archivo or f"LA1_{t}", comp=dict(kp=0.0))


def resumen(*gs):
    return {"partidas": list(gs)}


class SemanaTest(unittest.TestCase):
    def test_semana_vacia(self):
        r = resumen(g(MS - DIA))  # solo la semana anterior
        p = semanal.plan(r, hoy=HOY)
        self.assertEqual(p["partidas"], 0)
        self.assertIsNone(p["wr"])
        self.assertIn("no jugaste", p["foco_texto"])

    def test_menos_de_5_partidas(self):
        r = resumen(g(MS + HORA, True), g(MS + 2 * HORA, False), g(MS + 3 * HORA, True))
        p = semanal.plan(r, hoy=HOY)
        self.assertEqual(p["partidas"], 3)
        self.assertEqual((p["v"], p["d"]), (2, 1))
        self.assertAlmostEqual(p["wr"], 2 / 3, places=3)
        self.assertIn("menos de 5", p["foco_texto"])

    def test_cruce_de_semana(self):
        # domingo 23:59:59 de la anterior fuera, lunes 00:00 dentro, domingo 23:59 dentro, lunes siguiente fuera
        r = resumen(g(MS - 1, archivo="prev"), g(MS, archivo="lunes"),
                    g(MS + 7 * DIA - 1, archivo="domingo"), g(MS + 7 * DIA, archivo="sig"))
        self.assertEqual([x["archivo"] for x in semanal.semana(r, MS, MS + 7 * DIA)], ["lunes", "domingo"])
        self.assertEqual(semanal.plan(r, hoy=HOY)["partidas"], 2)

    def test_wr_prev_sin_datos(self):
        r = resumen(*(g(MS + i * HORA, win=(i % 3 != 0)) for i in range(1, 6)))  # 5 de esta semana, ninguna anterior
        p = semanal.plan(r, hoy=HOY)
        self.assertIsNone(p["wr_prev"])
        self.assertNotIn("semana anterior", p["foco_texto"])


class ReglaFocoTest(unittest.TestCase):
    def test_elige_la_que_menos_cumples(self):
        r = resumen(g(MS + HORA, archivo="a"), g(MS + 2 * HORA, archivo="b"))
        vistas = dict(reglas=[dict(texto="R1", numero="n1"), dict(texto="R2", numero="n2")],
                      por_partida=dict(a=dict(reglas=[True, True]), b=dict(reglas=[False, True])))
        f = semanal.plan(r, vistas, HOY)["regla_foco"]
        self.assertEqual(f["texto"], "R1")
        self.assertEqual((f["ok"], f["n"]), (1, 2))
        self.assertAlmostEqual(f["cumple"], 0.5, places=3)

    def test_ignora_reglas_sin_dato(self):
        r = resumen(g(MS + HORA, archivo="a"))
        vistas = dict(reglas=[dict(texto="R1", numero="n1")], por_partida=dict(a=dict(reglas=[None])))
        self.assertIsNone(semanal.plan(r, vistas, HOY)["regla_foco"])

    def test_sin_vistas_no_hay_foco(self):
        self.assertIsNone(semanal.plan(resumen(g(MS + HORA)), hoy=HOY)["regla_foco"])


class DatosTest(unittest.TestCase):
    def test_oro14(self):
        gs = [g(MS + i * HORA, oro14=o) for i, o in enumerate([500, None, -200, 100, None])]
        self.assertEqual(semanal.plan(resumen(*gs), hoy=HOY)["oro14"], dict(ok=2, n=3))

    def test_tilt(self):
        wins = [False, False, True, False, False, False]  # llega a 2 en la 2.ª y otra vez en la 5.ª
        gs = [g(MS + i * HORA, win=w) for i, w in enumerate(wins)]
        self.assertEqual(semanal.plan(resumen(*gs), hoy=HOY)["tilt"], 2)

    def test_plan_sobre_datos_reales(self):
        import os, pathlib
        raw = pathlib.Path(os.environ.get("DATOS_DIR") or pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw")
        if not (raw / "perfil.json").exists():
            self.skipTest("sin datos/raw/perfil.json")
        import score, vistas  # vistas lee datos/raw y timelines: solo aquí y solo si hay datos
        res = score.resumen(200)
        p = semanal.plan(res, vistas.todo(res))
        self.assertIsInstance(p, dict)
        self.assertEqual(p["v"] + p["d"], p["partidas"])
        self.assertIsInstance(p["foco_texto"], str)


if __name__ == "__main__":
    unittest.main()
