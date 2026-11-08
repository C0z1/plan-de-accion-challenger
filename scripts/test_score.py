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
