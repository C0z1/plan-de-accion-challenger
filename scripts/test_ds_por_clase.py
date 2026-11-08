"""Pruebas de DeepSeek para builds.por_clase() (turno 5, iteración 12). Sin red ni key.

Cubre los bordes que pidió Opus: empate en la clase más común del rival (no truena y da una de las dos),
un rival que no está en `clase` (esas partidas no cuentan) e `informe` con ddragon mock de 2 valores por
campeón (sin clase → sin línea «Solo contra» y sin tronar)."""
import os, pathlib, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
HAY_DATOS = (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists()
if not HAY_DATOS:
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: fixture mínima
import builds  # noqa: E402

ITEMS = {"3153": dict(name="Rey Arruinado", gold=dict(total=3200), tags=[])}
CLASE = {"Zed": "Assassin", "Lux": "Mage", "Ahri": "Mage"}
PERKS = (8000, 8008, (8008, 9111, 9104, 8299, 8400, 8444, 8453))


def b(core, rival=None, win=True):
    return dict(champ="Yone", pos="MIDDLE", win=win, core=[core], rival=rival, botas=None, runas=PERKS, skills="Q>E>W")


class PorClase(unittest.TestCase):
    def test_empate_en_clase_da_una_de_las_dos(self):
        # Mage (Lux/Ahri) y Assassin (Zed), 10 cada una y 2 ítems con 5+ en cada una
        bs = ([b("1", "Lux", True)] * 5 + [b("2", "Lux", False)] * 5 +
              [b("1", "Zed", True)] * 5 + [b("2", "Zed", False)] * 5)
        c, pp = builds.por_clase(bs, {"1": {"name": "Uno"}, "2": {"name": "Dos"}}, CLASE)
        self.assertIn(c, ("Mage", "Assassin"))  # no truena y da una de las dos
        self.assertEqual([(nm, len(v)) for nm, v in pp], [("Uno", 5), ("Dos", 5)])

    def test_rival_fuera_de_clase_no_cuenta(self):
        bs = ([b("1", "Lux", True)] * 5 + [b("2", "Lux", False)] * 5 +
              [b("1", "Desconocido", True)] * 5 + [b("3", None, True)] * 5)  # fuera de clase y sin rival
        c, pp = builds.por_clase(bs, {"1": {"name": "Uno"}, "2": {"name": "Dos"}}, CLASE)
        self.assertEqual(c, "Mage")
        self.assertEqual([(nm, len(v)) for nm, v in pp], [("Uno", 5), ("Dos", 5)])  # solo las de Lux cuentan

    def test_informe_sin_clase_no_saca_solo_contra(self):
        champs = {"yone": ("Yone", 777)}  # 2 valores, sin clase (como los mocks viejos)
        with mock.patch.object(builds, "ddragon", lambda: (ITEMS, {}, champs)), \
                mock.patch.object(builds, "mejores", lambda cid, nombre, pos=None: []), \
                mock.patch.object(builds, "tuyas", lambda nombre, pos=None: [(None, None, "yo")] * 6), \
                mock.patch.object(builds, "build_de", lambda m, t, u, items: b("3153", "Zed")):
            texto, rt, tu = builds.informe("Yone", "MIDDLE")
        self.assertIn("por primer ítem", texto)     # la línea principal sí sale (6 ≥ 5)
        self.assertNotIn("Solo contra", texto)      # sin clase no hay línea de matchup


if __name__ == "__main__":
    unittest.main()
