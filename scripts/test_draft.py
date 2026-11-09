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

    def test_counter_duro_avisa_y_da_alternativa(self):
        # Ekko es el mejor estimado (gana mucho en general) pero va 0-5 contra Viktor: techo Wilson 43% < base 50%
        js = [g("Ekko", True) for _ in range(30)] + [g("Ekko", False, "Viktor") for _ in range(5)]
        js += [g("Yone", i < 5) for i in range(10)]
        out = self.correr(js, "Viktor")
        self.assertIn("Recomendación: Ekko", out)
        self.assertIn("(counter duro). Alternativa: Yone", out)

    def test_pocas_partidas_en_el_rol_avisa(self):
        # sin nadie con 5+ en top: Yone 2-0 sale primero, alternativa Mordekaiser (4 partidas)
        js = [g("Yone", True, pos="TOP") for _ in range(2)] + [g("Mordekaiser", i < 2, pos="TOP") for i in range(4)]
        out = self.correr(js, "Zed", "TOP")
        self.assertIn("Yone tiene solo 2 partidas en TOP", out)
        self.assertIn("Alternativa: Mordekaiser (4 partidas", out)

    def test_sin_avisos_con_pool_sano(self):
        js = [g("Ekko", i < 6) for i in range(10)] + [g("Ekko", True, "Viktor") for _ in range(3)]
        self.assertNotIn("Aviso:", self.correr(js, "Viktor"))

    def test_build_del_pick_en_datos_draft(self):
        import builds, json, tempfile
        r = dict(n=3, wr=.67, core=[["Rey Arruinado", 1.0, "3153"]], botas=["Grebas", 1.0], runa=["Ritmo Letal", 1.0],
                 pagina=["Ritmo Letal", "a", "b", "c", "Brujería"], skills=["Q>E>W", 1.0])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(builds, "META", pathlib.Path(tmp)), \
                mock.patch.object(draft, "games", [g("Ekko", True) for _ in range(5)]), mock.patch.object(draft, "base", .5):
            self.assertEqual(draft.datos_draft("Zed", "MIDDLE")["build"], [])  # sin builds.json
            (pathlib.Path(tmp) / "builds.json").write_text(json.dumps({"Ekko|MIDDLE": r}), encoding="utf-8")
            d = draft.datos_draft("Zed", "MIDDLE")
        self.assertEqual(len(d["build"]), 3); self.assertIn("Rey Arruinado", d["build"][0])

    def test_rol_sin_partidas(self):
        self.assertIn("No tienes partidas en ese rol", self.correr([g("Ekko", True)], "Zed", "TOP"))


class Ficha(unittest.TestCase):  # draft.ficha(): pedidos 1, 3 y 4 del Diseñador, como dict
    def ficha(self, juegos, rival, champ=None, notas=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(draft, "games", juegos), mock.patch.object(draft, "base", .5), \
                mock.patch.object(draft, "NOTAS", pathlib.Path(tmp) / "notas.json"):
            if notas is not None: draft.NOTAS.write_text(notas, encoding="utf-8")
            return draft.ficha(rival, "MIDDLE", champ)

    def juegos(self):
        js = [g("Ekko", i < 3, "Viktor", gd14=-500) for i in range(4)] + [g("Ekko", i < 9) for i in range(12)]
        js += [g("Ekko", False, "Fizz") for _ in range(3)] + [g("Ekko", True, "Ahri") for _ in range(3)]
        js += [g("Yone", i < 3) for i in range(6)]
        for j in js[16:19]: j.update(cs14=-10, xp14=-200, nivel6=0, muertes6=1)  # las de Fizz; las demás sin timeline
        return js

    def test_por_que_con_record(self):
        f = self.ficha(self.juegos(), "Viktor")
        p = f["por_que"]
        self.assertEqual((f["champ"], p["v"], p["n"], p["oro14"], p["pocas"]), ("Ekko", 3, 4, -500, True))
        self.assertIn("Ekko va 3-1 contra Viktor (oro @14 −500)", p["frase"])
        self.assertIn("por encima de Yone", p["frase"])

    def test_por_que_casi_igual(self):  # estimados a < 2 puntos: no decir «por encima»
        js = [g("Ekko", i < 6) for i in range(10)] + [g("Yone", i < 7) for i in range(12)]  # 55% contra 54.5%
        p = self.ficha(js, "Lux")["por_que"]
        self.assertIn("casi igual que", p["frase"])
        self.assertNotIn("por encima", p["frase"])

    def test_por_que_sin_partidas_y_pick_elegido_peor(self):
        p = self.ficha(self.juegos(), "Lux", champ="yone")["por_que"]
        self.assertEqual((p["champ"], p["n"], p["alternativa"]["champ"]), ("Yone", 0, "Ekko"))
        self.assertTrue(p["frase"].startswith("Sin partidas de Yone contra Lux: "))
        self.assertIn("por debajo de Ekko", p["frase"])

    def test_counters_solo_los_que_bajan_con_su_porque(self):
        c = self.ficha(self.juegos(), "Viktor")["counters"]
        self.assertEqual([x["rival"] for x in c["lista"]], ["Fizz"])  # Ahri 3-0 y Viktor 3-1 no te bajan; Zed tiene 12 (y no baja)
        fz = c["lista"][0]
        self.assertEqual((fz["v"], fz["n"], fz["cs14"], fz["xp14"], fz["pocas"]), (0, 3, -10, -200, True))
        self.assertEqual(c["ref"]["n"], 22)

    def test_cuidado_y_notas_a_mano(self):
        js = self.juegos()
        c = self.ficha(js, "Fizz", notas='{"fizz": "pega fuerte al 3", "Zed": ["x"]}')["cuidado"]
        self.assertEqual((c["n"], c["v"], c["cs14"], c["muertes6"], c["notas"]), (3, 0, -10, 1, ["pega fuerte al 3"]))
        self.assertEqual(c["ref"]["n"], 28)
        self.assertEqual(self.ficha(js, "Fizz")["cuidado"]["notas"], [])            # sin tabla
        self.assertEqual(self.ficha(js, "Fizz", notas="{roto")["cuidado"]["notas"], [])  # tabla rota: no truena
        self.assertEqual(self.ficha(js, "Fizz", notas="[1]")["cuidado"]["notas"], [])

    def test_reglas_del_plan(self):  # pedido 2: la del campeón primero; la del 6 al frente si contra el rival llegas abajo
        textos = lambda rs: [r["texto"][:12] for r in rs]
        r = self.ficha(self.juegos(), "Viktor")["reglas"]
        self.assertEqual(len(r), 3)
        self.assertTrue(r[0]["texto"].startswith("Si pierdes la línea") and r[0]["pista"] and r[0]["n"] == 30)
        js = self.juegos()
        for j in js[16:19]: j["nivel6"] = -1  # contra Fizz llegas al 6 abajo
        r = self.ficha(js, "Fizz")["reglas"]
        self.assertTrue(r[0]["texto"].startswith("No salgas del 6") and "-1.0" in r[0]["contra"])
        self.assertEqual(len(r), 3); self.assertEqual(len(set(textos(r))), 3)
        self.assertNotIn("contra", draft.R_NIVEL6)  # no muta la tabla
        self.assertEqual(textos(draft.reglas("Zeri", "TOP")), textos([draft.R_NIVEL6, draft.R_MUERTES, draft.R_RIO]))

    def test_sin_partidas_en_el_rol(self):
        self.assertIsNone(self.ficha([g("Ekko", True, pos="TOP")], "Zed"))


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
