"""Franja 0.20 (PLAN-OVERLAY-2): tu próximo ítem con el oro que falta, al morir (tras 6 s) o al comprar (8 s). Sin red."""
import unittest

import companion
import overlay

ITEMS = {"1052": {"gold": {"base": 435}}, "3145": {"gold": {"base": 615}, "from": ["1052"]},  # Tomo amplificador, Alternador
         "3152": {"gold": {"base": 950}, "from": ["3145", "1052"]}, "1026": {"gold": {"base": 850}},
         "3157": {"gold": {"base": 1450}, "from": ["1026", "1052"]}}
BUILD = {"core": [("Cinturón Cohete", "3152"), ("Zhonya", "3157")], "fuente": "mejores"}


class Proximo(unittest.TestCase):
    def test_costo_recursivo_con_componentes(self):
        self.assertEqual(companion.costo_falta("3152", {}, ITEMS), 950 + 615 + 435 + 435)
        self.assertEqual(companion.costo_falta("3152", {"3145": 1}, ITEMS), 950 + 435)  # el Alternador ya lo llevas
        self.assertEqual(companion.costo_falta("3152", {"1052": 2}, ITEMS), 950 + 615)  # dos tomos: uno por cada receta
        self.assertIsNone(companion.costo_falta("9999", {}, ITEMS))

    def test_proximo(self):
        p = companion.proximo(BUILD, [["3145", "Alternador"]], 300, ITEMS)
        self.assertEqual((p["id"], p["i"], p["de"], p["falta"]), ("3152", 1, 2, 1100))  # 1385 - 300, redondeado a 50
        self.assertEqual(companion.proximo(BUILD, [], 99999, ITEMS)["falta"], 0)  # oro de sobra: 0, nunca negativo
        self.assertEqual(companion.proximo(BUILD, [["3152", ""]], 0, ITEMS)["id"], "3157")
        self.assertIsNone(companion.proximo(BUILD, [["3152", ""], ["3157", ""]], 0, ITEMS))  # core completo
        self.assertIsNone(companion.proximo(None, [], 0, ITEMS)); self.assertIsNone(companion.proximo(BUILD, [], 0, {}))


META = {"campeon": "Sylas", "rival": "Ahri", "t": 700, "nivel": 9, "nivel_rival": 9, "items": [["1052", ""]],
        "proximo": {"id": "3152", "nombre": "Cinturón Cohete Hextech", "i": 1, "de": 3, "falta": 1250, "fuente": "mejores"}}


class Momentos(unittest.TestCase):
    def test_muerte_espera_6_s_y_dura_hasta_revivir(self):
        m = {}; overlay.marcar(m, META, 100.0); overlay.marcar(m, {**META, "muerto": True}, 101.0)
        e = lambda ahora: overlay.estado({**META, "muerto": True}, ahora, marcas=m)["tipo"]
        self.assertEqual((e(106.9), e(107.1), e(140.0)), ("linea", "item", "item"))
        overlay.marcar(m, META, 141.0); self.assertEqual(overlay.estado(META, 141.0, marcas=m)["tipo"], "linea")  # reviviste

    def test_compra_8_s(self):
        m = {}; overlay.marcar(m, META, 100.0); overlay.marcar(m, {**META, "items": [["3145", ""]]}, 110.0)
        e = lambda ahora: overlay.estado(META, ahora, marcas=m)["tipo"]
        self.assertEqual((e(117.9), e(118.1)), ("item", "linea"))

    def test_no_antes_de_1_30_ni_apagado_ni_sobre_aviso(self):
        m = {"compra": 100.0}
        self.assertEqual(overlay.estado({**META, "t": 80}, 101.0, marcas=m)["tipo"], "linea")
        self.assertEqual(overlay.estado(META, 101.0, {"franja_build": False}, marcas=m)["tipo"], "linea")
        self.assertEqual(overlay.estado(META, 101.0, marcas=m, aviso={"franja": 100.0, "corto": "Min 11: x"})["tipo"], "aviso")

    def test_textos_sin_ordenes(self):
        e = overlay.estado(META, 101.0, marcas={"compra": 100.0})
        self.assertEqual(overlay.textos(e), ["Cinturón Cohete", "build OTPs", "1 250", "oro que falta"])
        for t in overlay.textos(e): self.assertNotRegex(t.lower(), r"compra|vuelve|recall|backea")


if __name__ == "__main__":
    unittest.main()
