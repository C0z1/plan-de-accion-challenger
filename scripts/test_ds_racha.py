"""Pruebas de DeepSeek para revision.racha (turno 4). Proceso sobre un DATOS_DIR temporal; sin red ni cliente."""
import json, os, pathlib, subprocess, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent


def correr(juegos):
    """juegos: lista de dicts {oro (gd14 o None), opp (hay rival de línea), tl (escribe timeline)}.
    Corre revision.py 1 en un DATOS_DIR temporal y devuelve (returncode, stdout)."""
    with __import__("tempfile").TemporaryDirectory() as d:
        d = pathlib.Path(d); (d / "timeline").mkdir()
        (d / "perfil.json").write_text(json.dumps({"account": {"puuid": "yo"}}))
        for i, j in enumerate(juegos):
            oro, opp, tl = j["oro"], j.get("opp", True), j.get("tl", True)
            ps = [dict(puuid="yo", participantId=1, teamId=100, teamPosition="MIDDLE",
                       championName="Ekko", win=oro is not None and oro >= 0)]
            ps.append(dict(puuid="el", participantId=2, teamId=200, teamPosition="MIDDLE" if opp else "JUNGLE",
                           championName="Zed", win=not (oro is not None and oro >= 0)))
            (d / f"XX_{i}.json").write_text(json.dumps(
                {"info": dict(gameDuration=1800, gameCreation=i * 10**8, participants=ps)}))
            if tl and oro is not None:
                pf = lambda o, xp, lv: dict(totalGold=5000 + o, minionsKilled=100, jungleMinionsKilled=0, xp=xp, level=lv)
                fr = [dict(events=[], participantFrames={"1": pf(oro, 7000 + oro, 6 if oro >= 0 else 5),
                                                         "2": pf(0, 7000, 6)}) for _ in range(16)]
                (d / "timeline" / f"XX_{i}.json").write_text(json.dumps({"info": {"frames": fr}}))
        r = subprocess.run([sys.executable, str(AQUI / "revision.py"), "1"], capture_output=True,
                           text=True, encoding="utf-8", env={**os.environ, "DATOS_DIR": str(d)})
    return r.returncode, r.stdout


class Racha(unittest.TestCase):
    def test_menos_de_5_partidas_y_3_con_oro_bajo_marca(self):
        code, out = correr([{"oro": -300}, {"oro": -200}, {"oro": -100}, {"oro": 400}])  # 4 partidas, 3 abajo
        self.assertEqual(code, 0)
        self.assertIn("## Racha de oro bajo al 14", out)
        self.assertIn("en 3 de tus últimas 5", out)

    def test_sin_timeline_no_cuenta_como_oro_bajo(self):
        code, out = correr([{"oro": -300}, {"oro": -200}] + [{"oro": None, "tl": False}] * 3)  # solo 2 abajo
        self.assertEqual(code, 0)
        self.assertNotIn("Racha", out)

    def test_sin_rival_de_linea_no_truena(self):
        code, out = correr([{"oro": -300}, {"oro": -200}] + [{"oro": None, "opp": False}] * 3)  # gd14 None: no cuenta
        self.assertEqual(code, 0)
        self.assertNotIn("Racha", out)


if __name__ == "__main__":
    unittest.main()
