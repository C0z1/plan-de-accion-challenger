"""Pruebas de scripts/replay.py y companion.paso_vivo: salida dorada de la partida anonimizada, invariantes de --validar y anonimizador."""
import contextlib, io, json, pathlib, unittest
from unittest import mock
import companion, replay

AQUI = pathlib.Path(__file__).resolve().parent
FIX = AQUI / "fixtures" / "vivo"
ORIGEN = pathlib.Path(r"C:\Users\felix\plan-de-accion-challenger\datos\vivo\20261109-175517.jsonl")


def jug(nombre, eq, nv=5, pos="BOTTOM", muertes=0):
    return {"riotId": nombre + "#T", "riotIdGameName": nombre, "summonerName": nombre + "#T", "team": eq, "position": pos, "level": nv,
            "championName": "C" + nombre, "scores": {"creepScore": 10, "deaths": muertes, "kills": 0, "assists": 0}, "items": []}


def foto(t, modo="CLASSIC", yo=5, rival=7, eventos=(), muertes=0):
    return {"activePlayer": {"riotId": "Yo#T", "summonerName": "Yo#T"}, "gameData": {"gameTime": t, "gameMode": modo},
            "allPlayers": [jug("Yo", "ORDER", yo, muertes=muertes), jug("El", "CHAOS", rival)], "events": {"Events": list(eventos)}}


def reg(t, franja=(), avisos=(), d=None):
    return {"t": t, "d": d or foto(t), "meta": {}, "franja": [(x, "") for x in franja], "avisos": list(avisos)}


class PasoVivo(unittest.TestCase):
    def setUp(self):
        p = replay.sin_precios(); p.__enter__(); self.addCleanup(p.__exit__, None, None, None)

    def test_aviso_una_vez_entre_llamadas(self):
        est = {}
        meta, av = companion.paso_vivo(foto(330), est, {})
        self.assertEqual([a[0] for a in av], ["aviso_nivel"]); self.assertEqual(av[0][2], 5); self.assertEqual(meta["minuto"], 5)
        self.assertEqual(companion.paso_vivo(foto(360), est, {})[1], [])
        self.assertEqual(est["avisado"], {"aviso_nivel"})

    def test_ajuste_apaga_el_aviso(self):
        self.assertEqual(companion.paso_vivo(foto(330), {}, {"aviso_nivel": False})[1], [])


class Validador(unittest.TestCase):
    def test_limpio(self): self.assertEqual(replay.validar([reg(0, ["Nv 1 vs 1"]), reg(30)]), [])

    def test_max_piezas(self):
        self.assertTrue(replay.validar([reg(0, ["a"] * (replay.MAX_PIEZAS + 1))]))
        self.assertEqual(replay.validar([reg(0, ["a"] * replay.MAX_PIEZAS)]), [])

    def test_dos_avisos_a_la_vez(self):
        self.assertTrue(replay.validar([reg(0, avisos=[("pico:1:x", "a", 0), ("pico:2:y", "b", 0)])]))

    def test_muertes_contra_eventos(self):
        ev = {"EventName": "ChampionKill", "EventID": 1, "EventTime": 5.0, "VictimName": "Yo"}
        self.assertEqual(replay.validar([reg(10, d=foto(10, eventos=[ev], muertes=1))]), [])
        self.assertTrue(replay.validar([reg(10, d=foto(10, eventos=[ev], muertes=2))]))

    def test_aviso_fuera_de_ventana(self):
        self.assertTrue(replay.validar([reg(0, avisos=[("aviso_nivel", companion.Texto("x", "x"), 9)])]))
        self.assertEqual(replay.validar([reg(0, avisos=[("aviso_nivel", companion.Texto("x", "x"), 6)])]), [])

    def test_linea_fuera_de_classic(self):
        self.assertTrue(replay.validar([reg(0, ["CS vs rival"], d=foto(0, modo="ARAM"))]))
        self.assertTrue(replay.validar([reg(0, ["ritmo 30"], d=foto(0, modo="ARAM"))]))
        self.assertEqual(replay.validar([reg(0, ["9 – 32", "kills"], d=foto(0, modo="ARAM"))]), [])

    def test_lista_negra(self):
        self.assertTrue(replay.validar([reg(0, ["Flash 3:00"])]))
        self.assertTrue(replay.validar([reg(0, avisos=[("pico:1:x", "Cuidado con su ELO", 1)])]))


class Anonimizador(unittest.TestCase):
    def test_sintetico(self):
        an = replay.anonimizar([foto(0, eventos=[{"EventName": "ChampionKill", "KillerName": "El", "VictimName": "Yo", "Assisters": ["El"]}])])
        txt = json.dumps(an)
        self.assertNotIn("El#T", txt); self.assertNotIn('"El"', txt)
        e = an[0]["events"]["Events"][0]
        self.assertEqual((e["KillerName"], e["VictimName"], e["Assisters"]), ("J1", "Yo", ["J1"]))
        self.assertEqual(an[0]["activePlayer"]["riotId"], "Yo#TEST")

    @unittest.skipUnless(ORIGEN.exists(), "sin la partida original")
    def test_no_sobrevive_ningun_riot_id(self):
        nombres = set()
        for d in replay.cargar(ORIGEN):
            for p in d["allPlayers"]: nombres |= {p.get(k) for k in ("riotId", "riotIdGameName", "summonerName")} - {None, ""}
        txt = (FIX / "partida_completa.jsonl").read_text(encoding="utf-8")
        self.assertEqual([n for n in nombres if n in txt], [])
        self.assertEqual([n for n in nombres if n in json.dumps(replay.anonimizar(replay.cargar(ORIGEN)))], [])


class Dorado(unittest.TestCase):
    def salida(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out): replay.main([str(FIX / "partida_completa.jsonl")])  # sin --precios: estable
        return out.getvalue()

    def test_salida_estable(self):  # regenerar: python scripts/replay.py scripts/fixtures/vivo/partida_completa.jsonl > scripts/fixtures/vivo/partida_completa.salida.txt
        esperado = (FIX / "partida_completa.salida.txt").read_text(encoding="utf-8")
        self.assertEqual(self.salida().splitlines(), esperado.splitlines())

    def test_invariantes_menos_piezas(self):
        with replay.sin_precios():
            fallos = replay.validar(replay.repetir(replay.cargar(FIX / "partida_completa.jsonl")))
        self.assertEqual([f for f in fallos if "piezas en la franja" not in f], [])

    # F6 aplicado: la franja nunca pasa de 4 piezas en la partida real
    def test_max_piezas_en_la_partida(self):
        with replay.sin_precios():
            self.assertEqual(replay.validar(replay.repetir(replay.cargar(FIX / "partida_completa.jsonl"))), [])


if __name__ == "__main__": unittest.main()
