"""Pruebas de score.py (sin red): la fórmula (las aserciones de score._prueba corren al importar), el CLI sobre
fixtures y la columna Score de revision.py que lee la ventana."""
import os, pathlib, subprocess, sys, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import score  # noqa: E402


def correr(nombre, *args):
    env = {**os.environ, "DATOS_DIR": str(AQUI / "fixtures" / "datos"), "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, str(AQUI / nombre), *args], capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, r.stdout + r.stderr


class Score(unittest.TestCase):
    def test_sin_rival_de_linea_ni_kills(self):
        ps = [dict(puuid=f"p{i}", teamPosition="", teamId=100 if i < 5 else 200, win=i < 5, kills=0, assists=0, deaths=0,
                   totalDamageDealtToChampions=0, goldEarned=500, damageDealtToObjectives=0, visionScore=0,
                   totalMinionsKilled=0, neutralMinionsKilled=0) for i in range(10)]
        r = score.de(score.z_partida(dict(mapId=11, gameDuration=600, participants=ps)), "p3", {})
        self.assertEqual((r["score"], r["puesto"], r["puesto_eq"]), (50, 1, 1))  # todos iguales: nada divide entre 0
        self.assertIsNone(r["linea"])  # sin teamPosition no hay rival de línea

    def test_resumen_dict_con_fixtures(self):
        r = score.resumen(5, AQUI / "fixtures" / "datos")
        self.assertEqual(r["ref"], 50)
        self.assertEqual(len(r["partidas"]), 1)  # el fixture tiene 1 partida
        p = r["partidas"][0]
        self.assertEqual(set(p["comp"]), set(score.COMP))
        self.assertIn(p["linea"], (1, 2, None))
        self.assertEqual(r["media"], p["score"]); self.assertIsNone(r["anteriores"])
        self.assertEqual(r["tendencia"], [p["score"]]); self.assertEqual(list(r["por_campeon"].values())[0]["n"], 1)

    def test_muertes14_25_desde_timeline(self):
        import json, tempfile
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d, "XX_1.json"); (f.parent / "timeline").mkdir()
            ev = lambda ms, v: dict(type="CHAMPION_KILL", timestamp=ms, victimId=v)
            fr = [dict(events=[ev(839999, 3), ev(840000, 3), ev(1499999, 3), ev(1500000, 3), ev(1000000, 4)])]
            (f.parent / "timeline" / f.name).write_text(json.dumps({"info": {"frames": fr}}))
            self.assertEqual(score.muertes14_25(dict(f=f, pid=3)), 2)  # 14:00 entra, 25:00 no, otra víctima no
            self.assertIsNone(score.muertes14_25(dict(f=pathlib.Path(d, "XX_2.json"), pid=3)))  # sin timeline
            for roto in ("{no es json", "{}", '{"info": {"frames": null}}'):
                (f.parent / "timeline" / f.name).write_text(roto)
                self.assertIsNone(score.muertes14_25(dict(f=f, pid=3)), roto)  # roto: None solo para esa partida
        self.assertIsNone(score.resumen(5, AQUI / "fixtures" / "datos")["partidas"][0]["muertes14_25"])

    def test_clave_tendencia_y_por_campeon(self):
        from unittest import mock
        comp = lambda lo, hi: {c: (-1.0 if c == lo else 1.5 if c == hi else 0.0) for c in score.COMP}
        gs = [dict(t=1, win=i % 2 == 0, champ="Ekko" if i < 30 else "Yone", kda="1/1/1", score=40 + i % 2 * 20, puesto=5,
                   puesto_eq=3, linea=None, comp=comp("muertes", "oro")) for i in range(45)]
        with mock.patch.object(score, "partidas", return_value=(gs, {}, "yo")):
            r = score.resumen(2)
        self.assertEqual([p["clave"] for p in r["partidas"]], [("oro", 1.5), ("muertes", -1.0)])  # V: lo que más subió; D: lo que más bajó
        self.assertEqual(r["tendencia"], [50.0, 50.0, 48.0])  # bloques de 20, el último corto (5 partidas: 3 V)
        self.assertEqual(list(r["por_campeon"]), ["Ekko", "Yone"])
        self.assertEqual(r["por_campeon"]["Yone"], dict(n=15, wr=0.53, score=49.3))

    def test_tilt(self):
        from unittest import mock
        from datetime import datetime, timedelta
        t0, m = datetime(2026, 11, 8, 12, 0), lambda x: (t0 + timedelta(minutes=x)).timestamp() * 1000
        # sesión 1: D D D V D; 3 h después, sesión 2: D D (la racha no se suma con la D final de la sesión 1)
        ts, ws = [0, 40, 80, 120, 160, 340, 380], [0, 0, 0, 1, 0, 0, 0]
        gs = [dict(t=m(t), win=bool(w), champ="Ekko", score=50.0) for t, w in zip(ts, ws)]
        with mock.patch.object(score, "partidas", return_value=(gs, {}, "yo")):
            r = score.tilt(hoy=t0.date())
            otro = score.tilt(hoy=(t0 + timedelta(days=1)).date())
        self.assertEqual(r["tras2"], dict(n=2, v=1, wr=0.5, ic=score.wilson(1, 2)))  # la 3.ª D y la V de la sesión 1
        self.assertEqual((r["racha"], r["llegas"], len(r["hoy"]), r["base"]["n"]), (2, 2, 7, 7))
        self.assertEqual(r["hoy"][0], dict(fecha="12:00", campeon="Ekko", win=False, score=50.0))
        self.assertEqual((otro["racha"], otro["hoy"]), (0, []))  # la última sesión no fue hoy

    def test_remake_y_ajeno(self):
        self.assertEqual(score.z_partida(dict(mapId=11, gameDuration=200, participants=[])), [])
        self.assertIsNone(score.de([], "yo", {}))

    def test_cli_y_revision_con_fixtures(self):
        code, out = correr("score.py", "1")
        self.assertEqual(code, 0, out); self.assertIn("## Últimas 1", out)
        code, out = correr("revision.py", "1")
        self.assertEqual(code, 0, out)
        import companion_gui
        r = companion_gui.parsear_revision(out)
        self.assertTrue(r["score"].isdigit(), r)
        from test_companion_gui import SALIDA  # salida vieja, sin columna Score
        self.assertEqual(companion_gui.parsear_revision(SALIDA)["score"], "-")


if __name__ == "__main__":
    unittest.main()
