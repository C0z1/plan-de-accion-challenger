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
        self.assertIsNone(companion.proximo(False, [], 0, ITEMS))  # «no hay build» (campeón sin partidas)
        raro = {"core": [("Ornn", "7000"), ("Zhonya", "3157")], "fuente": "tu"}
        self.assertEqual(companion.proximo(raro, [], 0, ITEMS)["id"], "3157")  # el que no está en Data Dragon se salta


META = {"campeon": "Sylas", "rival": "Ahri", "t": 700, "nivel": 9, "nivel_rival": 9, "items": [["1052", ""]],
        "proximo": {"id": "3152", "nombre": "Cinturón Cohete Hextech", "i": 1, "de": 3, "falta": 1250, "fuente": "mejores"}}


class BuildDeRespaldo(unittest.TestCase):  # campeón fuera de tu pool: la build sale de tus partidas con él (2+)
    def test_respaldo_y_no_hay(self):
        from unittest import mock
        import builds
        bs = [{"core": ["3032", "3085", "3031"], "botas": "3006", "runas": [8000, 8008, (8008,)], "skills": "QWE"}] * 2
        with mock.patch.object(builds, "guardado_dict", return_value=None), mock.patch.object(builds, "ddragon", return_value=({}, {}, {})),                 mock.patch.object(builds, "tuyas", return_value=[({"info": {"gameMode": "CLASSIC"}}, 2, 3)] * 2), mock.patch.object(builds, "build_de", side_effect=bs),                 mock.patch.object(builds, "resumir", return_value={"core": [("Yun Tal", .5, "3032"), ("Runaan", .5, "3085"), ("Filo", .5, "3031")]}):
            b = companion.build_partida("Zeri", "BOTTOM")
        self.assertEqual(([i for _, i in b["core"]], b["fuente"]), (["3032", "3085", "3031"], "tu"))
        with mock.patch.object(builds, "guardado_dict", return_value=None), mock.patch.object(builds, "ddragon", return_value=({}, {}, {})),                 mock.patch.object(builds, "tuyas", return_value=[]):
            self.assertIs(companion.build_partida("Zeri", "BOTTOM"), False)  # no hay: no se reintenta
        with mock.patch.object(builds, "guardado_dict", side_effect=OSError):
            self.assertIsNone(companion.build_partida("Zeri", "BOTTOM"))  # falló: se reintenta


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
        self.assertEqual(overlay.textos(e), ["Cinturón Cohete…", "build OTPs", "1 250", "oro que falta"])
        for t in overlay.textos(e): self.assertNotRegex(t.lower(), r"compra|vuelve|recall|backea")


PLAN = {"rival": "Ahri", "v": 3, "n": 4, "wr": 0.55, "n_rol": 80, "regla": "69+ minions al 10", "tu": {"media": 74, "cumple": 0.75},
        "nota": None, "m6": 0.5, "m6_ref": 0.7, "m6_pocas": False}


class Inicio(unittest.TestCase):  # fase 2: match, regla y nota los primeros 90 s
    def e(self, t, **kw): return overlay.estado({**META, "t": t, "plan": {**PLAN, **kw}}, 0)

    def test_tramos(self):
        self.assertEqual([self.e(t)["tipo"] for t in (0, 29, 30, 59, 60, 89, 90)], ["match", "match", "plan", "plan", "plan", "plan", "linea"])
        self.assertEqual(overlay.textos(self.e(10)), ["vs", "3–1", "tu récord", "WR 55%"])
        self.assertEqual(self.e(40)["lineas"], ["Tu regla · 69+ minions al 10", "tu media 74 · la cumples 75 %"])
        self.assertEqual(self.e(70)["lineas"], ["Contra Ahri: 0,5 muertes antes del 6", "tu media 0,7"])
        self.assertEqual(self.e(70, nota="pega fuerte al 6")["lineas"], ["Tu nota · pega fuerte al 6"])

    def test_sin_datos(self):
        self.assertEqual(self.e(10, n=0)["chip"], ("1ª vez", "gris"))
        self.assertEqual(self.e(70, m6=None)["tipo"], "linea")  # sin nota ni dato: sigue la línea
        self.assertEqual(self.e(40, regla=None)["tipo"], "linea")
        self.assertEqual(overlay.estado({**META, "t": 10}, 0)["tipo"], "linea")  # sin plan
        self.assertEqual(overlay.estado({**META, "t": 10, "plan": PLAN}, 0, {"franja_plan": False})["tipo"], "linea")

    def test_sin_ordenes_ni_prediccion(self):
        for t in (10, 40, 70):
            for x in overlay.textos(self.e(t)): self.assertNotRegex(x.lower(), r"compra|juega|evita|pelea|gana|estimado|probab")


if __name__ == "__main__":
    unittest.main()
