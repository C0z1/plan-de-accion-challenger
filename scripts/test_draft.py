"""python -m unittest discover scripts  (sin red ni key; draft.py lee datos/raw/perfil.json al importarse)"""
import contextlib, io, os, pathlib, subprocess, sys, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
HAY_DATOS = (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists()
if not HAY_DATOS:
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: una partida mínima para que draft.py importe
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

    def test_encoge_un_record_corto(self):
        # récord crudo elegiría Yone (1-0 = 100% contra 3-1 = 75%); encogido gana Ekko (~69% contra ~41%)
        js = [g("Yone", True, "Viktor")] + [g("Yone", i < 1) for i in range(10)]
        js += [g("Ekko", i < 3, "Viktor") for i in range(4)] + [g("Ekko", i < 12) for i in range(16)]
        self.assertIn("Recomendación: Ekko", self.correr(js, "viktor"))

    def test_rival_desconocido_avisa(self):
        out = self.correr([g("Ekko", True) for _ in range(5)], "Nadie")
        self.assertIn("no aparece", out)
        self.assertIn("Recomendación: Ekko", out)

    def test_rol_sin_partidas(self):
        self.assertIn("No tienes partidas en ese rol", self.correr([g("Ekko", True)], "Zed", "TOP"))


@unittest.skipUnless(HAY_DATOS, "sin datos/raw")
class Revision(unittest.TestCase):  # revision.py corre al importarse: se prueba como proceso sobre datos/raw
    def test_revision_1_corre(self):
        r = subprocess.run([sys.executable, str(AQUI / "revision.py"), "1"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("|", r.stdout)  # sale la tabla por partida


class Racha(unittest.TestCase):  # partidas sintéticas en un DATOS_DIR temporal (corre también en el CI)
    def correr(self, oros):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d); (d / "timeline").mkdir()
            (d / "perfil.json").write_text(json.dumps({"account": {"puuid": "yo"}}))
            for i, oro in enumerate(oros):  # la más nueva al final; gana si oro >= 0
                ps = [dict(puuid=u, participantId=p, teamId=t, teamPosition="MIDDLE", championName=c, win=(oro >= 0) == (u == "yo"))
                      for u, p, t, c in (("yo", 1, 100, "Ekko"), ("el", 2, 200, "Zed"))]
                (d / f"XX_{i}.json").write_text(json.dumps({"info": dict(gameDuration=1800, gameCreation=i * 10**8, participants=ps)}))
                pf = lambda o, xp, lv: dict(totalGold=5000 + o, minionsKilled=100, jungleMinionsKilled=0, xp=xp, level=lv)
                fr = [dict(events=[], participantFrames={"1": pf(oro, 7000 + oro, 6 if oro >= 0 else 5), "2": pf(0, 7000, 6)})
                      for _ in range(16)]
                (d / "timeline" / f"XX_{i}.json").write_text(json.dumps({"info": {"frames": fr}}))
            r = subprocess.run([sys.executable, str(AQUI / "revision.py"), "1"], capture_output=True, text=True,
                               encoding="utf-8", env={**os.environ, "DATOS_DIR": str(d)})
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def test_3_de_5_con_oro_bajo_marca_la_racha(self):
        out = self.correr([500, 500, 500, -300, 800, 400, -200, -900])  # últimas 5: 3 con oro < 0
        self.assertIn("en 3 de tus últimas 5", out)
        self.assertEqual(out.split("## Racha")[1].count("\n- "), 2)  # las 2 sugerencias
        self.assertIn("ganas -, abajo 0% (", out.split("Al minuto 6")[1])  # con oro < 0 todas van 1 nivel abajo y pierden
        import companion_gui
        self.assertEqual(len(companion_gui.parsear_revision(out)["racha"]), 3)

    def test_2_de_5_no_marca(self):
        out = self.correr([-500, -500, -500, 300, -800, 400, -200, 900])
        self.assertNotIn("Racha", out)


if __name__ == "__main__": unittest.main()
