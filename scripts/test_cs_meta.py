"""F9: meta de CS al 10 automática por campeón (mediana de tus victorias, 8+ partidas)."""
import json, os, pathlib, sys, unittest
AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo: vistas importa draft, que lee perfil.json
import companion, vistas

FOTO = pathlib.Path(__file__).resolve().parent / "fixtures" / "vivo" / "allgamedata.json"


def gs(n, champ="Ekko", pos="MIDDLE", win=True, base=60):
    return [dict(win=win, champ=champ, pos=pos, min10=base + i) for i in range(n)]


def foto(cs=50, pos="MIDDLE"):
    d = json.loads(FOTO.read_text(encoding="utf-8")); d["gameData"]["gameTime"] = 610
    d["allPlayers"][0]["scores"]["creepScore"] = cs; d["allPlayers"][0]["position"] = pos
    return d


class MetasCs(unittest.TestCase):
    def test_mediana_solo_de_victorias(self):
        derrotas = gs(20, win=False, base=10)  # no cuentan
        self.assertEqual(vistas.metas_cs(gs(9) + derrotas)[("Ekko", "MIDDLE")], 64)  # 60..68 -> 64

    def test_umbral_de_8_victorias(self):
        self.assertEqual(vistas.MIN_PARTIDAS_META, 8)
        self.assertIn(("Ekko", "MIDDLE"), vistas.metas_cs(gs(8)))
        self.assertNotIn(("Ekko", "MIDDLE"), vistas.metas_cs(gs(7) + gs(30, win=False)))
        self.assertNotIn(("Ekko", "MIDDLE"), vistas.metas_cs(gs(8, pos="TOP") + gs(7)))  # por rol

    def test_jungla_sin_meta_y_sin_dato(self):
        self.assertEqual(vistas.metas_cs(gs(12, pos="JUNGLE")), {})
        self.assertEqual(vistas.metas_cs([dict(win=True, champ="Ekko", pos="MIDDLE")] * 12), {})  # sin timeline


class AvisoAuto(unittest.TestCase):
    def setUp(self): self.orig, self.cfg = companion._METAS, companion.CFG; companion.CFG = pathlib.Path("no-existe.json")
    def tearDown(self): companion._METAS, companion.CFG = self.orig, self.cfg

    def test_aviso_con_meta_automatica(self):
        companion._METAS = {("Ekko", "MIDDLE"): 64}
        t = companion.aviso_minions(foto(50)); self.assertIn("llevas 50 de CS con Ekko (tu meta: 64)", t)
        self.assertLessEqual(len(t.corto), 48)
        self.assertIsNone(companion.aviso_minions(foto(64)))
        self.assertEqual(companion.meta_fase(foto(50))["cs_meta"], 64)

    def test_sin_meta_no_hay_nada(self):
        companion._METAS = {("Ekko", "TOP"): 64}  # otro rol
        self.assertIsNone(companion.aviso_minions(foto(5))); self.assertIsNone(companion.meta_fase(foto(5))["cs_meta"])
        self.assertIsNone(companion.aviso_minions(foto(5, pos="")))  # normales: sin rol

    def test_config_manda(self):
        companion._METAS = {("Ekko", "MIDDLE"): 64}
        m10 = {"campeon": "Ekko", "minimo": 70}
        self.assertIn("tu meta: 70", companion.aviso_minions(foto(65), m10))
        self.assertEqual(companion.meta_fase(foto(65), m10)["cs_meta"], 70)


if __name__ == "__main__": unittest.main()
