"""Racha de oro al 14 (score.oro14 / racha_oro14) y Plan de regreso (companion.aviso_regreso). Datos sintéticos."""
import json, pathlib, sys, tempfile, unittest

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import companion, companion_gui, score


def timeline(oro_yo, oro_el, frames=16):
    fr = [{"participantFrames": {"1": {"totalGold": oro_yo}, "6": {"totalGold": oro_el}}} for _ in range(frames)]
    return {"info": {"frames": fr}}


class Oro14(unittest.TestCase):
    def g(self, tl, d, rival=True):
        f = pathlib.Path(d) / "EUW1_1.json"; (pathlib.Path(d) / "timeline").mkdir(exist_ok=True)
        if tl is not None: (pathlib.Path(d) / "timeline" / f.name).write_text(json.dumps(tl))
        return dict(f=f, pid=1, rival_id="r" if rival else None, pids={"r": 6})

    def test_diferencia(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(score.oro14(self.g(timeline(4000, 4300), d)), -300)

    def test_sin_datos_da_none(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(score.oro14(self.g(None, d)))                       # sin timeline
            self.assertIsNone(score.oro14(self.g(timeline(1, 2, frames=14), d)))  # acabó antes del 14
            self.assertIsNone(score.oro14(self.g(timeline(1, 2), d, rival=False)))  # sin rival
            (pathlib.Path(d) / "timeline" / "EUW1_1.json").write_text("{roto")
            self.assertIsNone(score.oro14(self.g({}, d)))  # timeline sin frames
        self.assertIsNone(score.oro14({}))

    def test_racha(self):
        r = score.racha_oro14([100, -50, None, 0, 300, 999])  # la más reciente primero; solo cuentan 5
        self.assertEqual(r, dict(marcas=[True, True, None, False, True], ok=3, n=4))

    def test_racha_vacia(self):
        self.assertEqual(score.racha_oro14([]), dict(marcas=[], ok=0, n=0))
        self.assertEqual(score.racha_oro14([None, None]), dict(marcas=[None, None], ok=0, n=0))


def foto(t, nivel, rival, cs=(50, 50), modo="CLASSIC"):
    p = lambda nom, eq, lv, c: dict(riotId=nom, summonerName=nom, team=eq, position="MIDDLE", level=lv, championName=nom, scores=dict(creepScore=c))
    return dict(gameData=dict(gameTime=t, gameMode=modo), activePlayer=dict(riotId="yo", summonerName="yo"),
                allPlayers=[p("yo", "ORDER", nivel, cs[0]), p("Zed", "CHAOS", rival, cs[1])])


class Regreso(unittest.TestCase):
    def test_avisa_abajo_de_nivel(self):
        txt = companion.aviso_regreso(foto(700, 5, 6))
        self.assertIn("1 nivel abajo de Zed", txt); self.assertIn("jungla", txt); self.assertNotIn("CS", txt)

    def test_con_farm_perdido(self):
        self.assertIn("2 niveles y 15 CS abajo", companion.aviso_regreso(foto(700, 5, 7, cs=(40, 55))))

    def test_sin_aviso(self):
        for d in (foto(700, 6, 6), foto(700, 7, 6), foto(500, 5, 7), foto(900, 5, 7), foto(700, 5, 7, modo="ARAM"), None, {}):
            self.assertIsNone(companion.aviso_regreso(d))

    def test_sin_rival_ni_nivel_null(self):
        d = foto(700, 5, 6); d["allPlayers"][1]["position"] = "TOP"
        self.assertIsNone(companion.aviso_regreso(d))
        d = foto(700, 5, 6); d["allPlayers"][1]["level"] = None
        self.assertIsNone(companion.aviso_regreso(d))

    def test_ajuste_por_defecto(self):
        self.assertIs(companion_gui.AJUSTES_DEF["aviso_regreso"], True)


if __name__ == "__main__": unittest.main()
