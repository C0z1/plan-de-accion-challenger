"""python -m unittest discover scripts  (sin red ni key; draft.py lee datos/raw/perfil.json al importarse)"""
import contextlib, io, pathlib, subprocess, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import draft


def g(champ, win, opp="Zed", pos="MIDDLE", gd14=0):
    return dict(win=win, champ=champ, pos=pos, opp=opp, enemies={opp}, gd14=gd14, t=0)


class Funciones(unittest.TestCase):
    def test_key_y_alias(self):
        self.assertEqual(draft.key("Kai'Sa"), "kaisa")
        self.assertEqual(draft.key("Wukong"), draft.key("MonkeyKing"))

    def test_wilson(self):
        self.assertEqual(draft.wilson(0, 0), (0, 0))
        lo, hi = draft.wilson(5, 10)
        self.assertTrue(lo < .5 < hi and round(lo, 2) == .24 and round(hi, 2) == .76)

    def test_shrink_sin_partidas_es_el_prior(self):
        self.assertAlmostEqual(draft.shrink(0, 0, .6), .6)


class Draft(unittest.TestCase):
    def correr(self, juegos, rival, pos="MIDDLE"):
        out = io.StringIO()
        with mock.patch.object(draft, "games", juegos), mock.patch.object(draft, "base", .5), contextlib.redirect_stdout(out):
            draft.draft(rival, pos)
        return out.getvalue()

    def test_recomienda_el_mejor_estimado(self):
        # Ekko gana en general pero pierde 0-4 contra Viktor; Yone va 3-1 contra Viktor
        js = [g("Ekko", True) for _ in range(8)] + [g("Ekko", False, "Viktor") for _ in range(4)]
        js += [g("Yone", i < 3, "Viktor") for i in range(4)] + [g("Yone", i < 2) for i in range(4)]
        self.assertIn("Recomendación: Yone", self.correr(js, "viktor"))

    def test_rival_desconocido_avisa(self):
        out = self.correr([g("Ekko", True) for _ in range(5)], "Nadie")
        self.assertIn("no aparece", out)
        self.assertIn("Recomendación: Ekko", out)

    def test_rol_sin_partidas(self):
        self.assertIn("No tienes partidas en ese rol", self.correr([g("Ekko", True)], "Zed", "TOP"))


@unittest.skipUnless((AQUI.parent / "datos" / "raw" / "perfil.json").exists(), "sin datos/raw")
class Revision(unittest.TestCase):  # revision.py corre al importarse: se prueba como proceso sobre datos/raw
    def test_revision_1_corre(self):
        r = subprocess.run([sys.executable, str(AQUI / "revision.py"), "1"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("|", r.stdout)  # sale la tabla por partida


if __name__ == "__main__": unittest.main()
