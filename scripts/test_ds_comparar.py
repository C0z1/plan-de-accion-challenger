"""Pruebas de scripts/comparar.py (tú contra el onetrick del top): funciones puras con datos sintéticos
y comparar() contra un builds.json de mentira; sin red."""
import json, pathlib, sys, tempfile, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import builds  # noqa: E402
import comparar  # noqa: E402


def b(core, botas=None, runa="Conquistador", skills="Q>E>W"):
    return {"core": [[n, 0.5, "0"] for n in core],
            "botas": [botas, 0.5] if botas else None,
            "runa": [runa, 0.5],
            "skills": [skills, 0.5]}


MEJORES = b(["Cinturón Cohete Hextech", "Agrietador"], botas="Botas Jonias de la Lucidez", runa="Conquistador", skills="Q>E>W")
TUYA = b(["Cinturón Cohete Hextech", "Lumbría"], botas="Botas del Hechicero", runa="Conquistador", skills="W>Q>E")


class Diferencias(unittest.TestCase):
    def test_iguales(self):
        difs = comparar.diferencias(MEJORES, MEJORES)
        self.assertEqual([d["tema"] for d in difs], list(comparar.TEMAS))
        self.assertTrue(all(d["igual"] for d in difs))

    def test_distintas(self):
        difs = {d["tema"]: d for d in comparar.diferencias(MEJORES, TUYA)}
        self.assertTrue(difs["primer ítem"]["igual"])     # los dos abren Cinturón
        self.assertFalse(difs["core"]["igual"])
        self.assertFalse(difs["botas"]["igual"])
        self.assertTrue(difs["runa"]["igual"])
        self.assertFalse(difs["habilidades"]["igual"])
        self.assertEqual(difs["botas"]["ellos"], "Botas Jonias de la Lucidez")
        self.assertEqual(difs["botas"]["tu"], "Botas del Hechicero")

    def test_solo_temas_con_dato(self):
        sin_botas = b(["Cinturón Cohete Hextech"])        # botas None: ese tema no sale
        temas = [d["tema"] for d in comparar.diferencias(MEJORES, sin_botas)]
        self.assertNotIn("botas", temas)
        self.assertEqual(len(temas), 4)


class Frase(unittest.TestCase):
    def test_primer_distinto_con_record(self):
        difs = [{"tema": "primer ítem", "ellos": "Cinturón Cohete Hextech", "tu": "Ludens", "igual": False}]
        self.assertEqual(comparar.frase(difs, {"si": [3, 5], "no": [2, 4]}),
                         "Ellos abren Cinturón Cohete Hextech; tú, Ludens. Con su primer ítem vas 3/5.")

    def test_todo_igual(self):
        self.assertEqual(comparar.frase(comparar.diferencias(MEJORES, MEJORES)),
                         "Tu build es igual a la de los onetricks del top.")

    def test_sin_record_de_su_primer_item(self):
        difs = comparar.diferencias(MEJORES, TUYA)
        self.assertNotIn("Con su primer ítem", comparar.frase(difs))                        # sin primer
        self.assertNotIn("Con su primer ítem", comparar.frase(difs, {"si": [0, 0], "no": [1, 1]}))  # 0 partidas

    def test_varias_diferencias_en_una_frase(self):
        f = comparar.frase(comparar.diferencias(MEJORES, TUYA))
        self.assertIn("Ellos", f)
        self.assertIn("tú,", f)
        self.assertEqual(f.count(". "), 0)  # una sola frase cuando no hay récord de su primer ítem


class Comparar(unittest.TestCase):
    def _escribir(self, d):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (pathlib.Path(tmp.name) / "builds.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        return mock.patch.object(builds, "META", pathlib.Path(tmp.name))

    def test_completa(self):
        d = {"Sylas|MIDDLE": dict(MEJORES, primer={"item": "Cinturón Cohete Hextech", "si": [34, 62], "no": [10, 18]}),
             "Sylas|MIDDLE|tu": TUYA}
        with self._escribir(d):
            r = comparar.comparar("Sylas", "MIDDLE")
        self.assertIsNotNone(r)
        self.assertEqual(len(r["difs"]), 5)
        self.assertIn("Con su primer ítem vas 34/62", r["frase"])

    def test_sin_tuya(self):
        with self._escribir({"Sylas|MIDDLE": MEJORES}):
            self.assertIsNone(comparar.comparar("Sylas", "MIDDLE"))

    def test_sin_ellos(self):
        with self._escribir({"Sylas|MIDDLE|tu": TUYA}):
            self.assertIsNone(comparar.comparar("Sylas", "MIDDLE"))

    def test_json_roto(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        (pathlib.Path(tmp.name) / "builds.json").write_text("no es json", encoding="utf-8")
        with mock.patch.object(builds, "META", pathlib.Path(tmp.name)):
            self.assertIsNone(comparar.comparar("Sylas", "MIDDLE"))

    def test_sin_rol_usa_el_que_haya(self):
        d = {"Sylas|MIDDLE": MEJORES, "Sylas|MIDDLE|tu": TUYA}
        with self._escribir(d):
            self.assertIsNotNone(comparar.comparar("Sylas"))
            self.assertIsNone(comparar.comparar("Sylas", "TOP"))   # solo está MIDDLE

    def test_nombre_sin_distinguir_mayusculas(self):
        d = {"Sylas|MIDDLE": MEJORES, "Sylas|MIDDLE|tu": TUYA}
        with self._escribir(d):
            self.assertIsNotNone(comparar.comparar("sylas", "middle"))


class DatosReales(unittest.TestCase):
    def test_comparar_datos_reales(self):
        import os
        meta = pathlib.Path(os.environ.get("META_DIR") or AQUI.parent / "datos" / "meta")
        f = meta / "builds.json"
        if not f.exists():
            self.skipTest("sin datos/meta/builds.json")
        d = json.loads(f.read_text(encoding="utf-8"))
        k = next((k for k in d if k.count("|") == 1 and k + "|tu" in d), None)
        if not k:
            self.skipTest("builds.json sin un par «mejores|tu» completo")
        c, p = k.split("|", 1)
        r = comparar.comparar(c, p)
        self.assertIsNotNone(r)
        self.assertIsInstance(r["frase"], str)
        self.assertTrue(r["frase"])
        self.assertGreaterEqual(len(r["difs"]), 1)


if __name__ == "__main__":
    unittest.main()
