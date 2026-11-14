"""Pruebas de DeepSeek para companion.resumen_fin()/linea_fin() (turno 6, iteración 6). Sin red ni key.

Cubre los bordes que pidió Opus: (a) muerte a 25:00 exacto no cuenta en 14–25 (y 14:00 sí),
(b) reinicio del cliente en EndOfGame no repite la línea, (c) sin foto no hay línea y no truena,
(d) scores con kills null → «0». Aísla config.json del usuario para no depender de él."""
import contextlib, io, pathlib, sys, unittest

AQUI = pathlib.Path(__file__).parent
sys.path.insert(0, str(AQUI))
import companion


def foto(gameTime=1510, eventos=None, scores=None):
    s = {"kills": 5, "deaths": 4, "assists": 7, "creepScore": 245}
    if scores is not None: s = scores
    return {
        "activePlayer": {"riotId": "cozi#1134", "summonerName": "cozi"},
        "allPlayers": [
            {"riotId": "cozi#1134", "summonerName": "cozi", "riotIdGameName": "cozi",
             "position": "MIDDLE", "team": "ORDER", "championName": "Sylas", "level": 13, "scores": s},
            {"riotId": "Zed#LAN", "summonerName": "Zed", "position": "MIDDLE", "team": "CHAOS",
             "championName": "Zed", "level": 13, "scores": {}},
        ],
        "events": {"Events": eventos or []},
        "gameData": {"gameTime": gameTime},
    }


def muerte(t): return {"EventName": "ChampionKill", "VictimName": "cozi#1134", "EventTime": t}


class LineaFin(unittest.TestCase):
    def setUp(self):
        self._cfg = companion.CFG
        companion.CFG = AQUI / "__no_config__.json"  # aísla config.json del usuario (meta_fase lo lee)

    def tearDown(self):
        companion.CFG = self._cfg

    def test_borde_1400_cuenta_y_2500_no(self):
        # (a) 839 (antes del 14) y 1500 (25:00 exacto) fuera de 14–25; 840 y 1499 dentro.
        r = companion.resumen_fin(foto(1510, [muerte(t) for t in (839, 840, 1499, 1500)]))
        self.assertEqual(r["muertes14_25"], 2)   # 840 y 1499
        self.assertEqual(r["muertes14"], 3)      # sin tope: 840, 1499 y 1500
        self.assertIn("muertes del 14 al 25: 2 (meta ≤ 2) ✓", companion.linea_fin(r))

    def test_acaba_antes_del_14_sin_segmento(self):
        r = companion.resumen_fin(foto(700))
        self.assertIsNone(r["muertes14_25"])
        self.assertNotIn("muertes del 14 al 25", companion.linea_fin(r))
        self.assertIn("CS 245", companion.linea_fin(r))

    def test_scores_null_da_0_y_cs_pregunta(self):
        # (d) kills/deaths/assists/creepScore null → «0/0/0» y «CS ?» sin tronar.
        r = companion.resumen_fin(foto(1510, scores={"kills": None, "deaths": None, "assists": None, "creepScore": None}))
        self.assertEqual(r["kda"], "0/0/0")
        self.assertIn("CS ?", companion.linea_fin(r))

    def test_sin_foto_no_hay_linea_ni_truena(self):
        # (c) companion abierto en EndOfGame sin ninguna foto: nada y sin excepción.
        for x in (None, {}, {"gameData": {"gameTime": 1500}}):
            self.assertIsNone(companion.resumen_fin(x))
            self.assertIsNone(companion.linea_fin(companion.resumen_fin(x)))
        orig = companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida
        fases = iter(["EndOfGame", "EndOfGame"])
        companion.lcu = lambda path: next(fases); companion.vivo = lambda: None
        companion.capturar = lambda a, d: a; companion.time.sleep = lambda _: None; companion.post_partida = lambda: None
        out = io.StringIO()
        try:
            with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
        finally:
            companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida = orig
        self.assertNotIn("Min ", out.getvalue())  # sin foto: no hay línea

    def test_reinicio_en_endofgame_no_repite(self):
        # (b) el cliente cae (None) entre dos EndOfGame: la línea sale una sola vez.
        orig = companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida
        fases = iter(["InProgress", "EndOfGame", None, "EndOfGame"])
        companion.lcu = lambda path: next(fases); companion.vivo = lambda: foto(362)
        companion.capturar = lambda a, d: a; companion.time.sleep = lambda _: None; companion.post_partida = lambda: None
        out = io.StringIO()
        try:
            with self.assertRaises(StopIteration), contextlib.redirect_stdout(out): companion.main([])
        finally:
            companion.lcu, companion.vivo, companion.capturar, companion.time.sleep, companion.post_partida = orig
        self.assertEqual(out.getvalue().count("Min 6 · Sylas 5/4/7 contra Zed · CS 245"), 1)

    def test_meta_2_corte(self):
        muertes = [muerte(900 + i) for i in range(3)]
        self.assertIn("3 (meta ≤ 2) · para trabajar", companion.linea_fin(companion.resumen_fin(foto(1510, muertes))))
        self.assertIn("2 (meta ≤ 2) ✓", companion.linea_fin(companion.resumen_fin(foto(1510, muertes[:2]))))


if __name__ == "__main__":
    unittest.main()
