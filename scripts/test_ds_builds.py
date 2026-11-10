"""Pruebas de DeepSeek para builds.py (turno 5, iteración 2). Sin red: casos borde de build_de, resumir y mejores.

Cubre los bordes que pidió Opus: dos ITEM_UNDO seguidos del mismo ítem, una partida sin ningún
legendario (core vacío), una región con la liga vacía, un legendario vendido (ITEM_SOLD, ya arreglado),
botas vendidas y `guardado` sin la clave pedida."""
import json, pathlib, sys, tempfile, time, unittest
from unittest import mock

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import builds  # noqa: E402

ITEMS = {"1055": dict(name="Espada de Doran", gold=dict(total=450), tags=[]),
         "1001": dict(name="Botas", gold=dict(total=300), tags=["Boots"]),
         "3006": dict(name="Grebas del Berserker", gold=dict(total=1100), tags=["Boots"]),
         "3153": dict(name="Espada del Rey Arruinado", gold=dict(total=3200), tags=[]),
         "6673": dict(name="Arcoescudo Inmortal", gold=dict(total=3000), tags=[])}
PERKS = dict(styles=[dict(style=8000, selections=[dict(perk=8008), dict(perk=9111), dict(perk=9104), dict(perk=8299)]),
                     dict(style=8400, selections=[dict(perk=8444), dict(perk=8453)])])


def mk(puuid="yo", champ="Yone", pos="MIDDLE", win=True, mid="KR_1", eventos=None):
    ps = [dict(puuid=puuid, participantId=1, championName=champ, teamPosition=pos, win=win, perks=PERKS)]
    return (dict(metadata=dict(matchId=mid), info=dict(participants=ps, gameDuration=1800)),
            dict(info=dict(participants=[dict(participantId=1, puuid=puuid)], frames=[dict(events=eventos or [])])))


def compra(iid, pid=1): return dict(type="ITEM_PURCHASED", participantId=pid, itemId=iid)
def undo(iid, pid=1): return dict(type="ITEM_UNDO", participantId=pid, beforeId=iid, afterId=0)
def venta(iid, pid=1): return dict(type="ITEM_SOLD", participantId=pid, itemId=iid)


class Borde(unittest.TestCase):
    def test_dos_undo_del_mismo_item_no_dejan_ninguno(self):
        ev = [compra(6673), compra(3153), compra(3153), undo(3153), undo(3153)]
        b = builds.build_de(*mk(eventos=ev), "yo", ITEMS)
        self.assertEqual(b["core"], ["6673"])  # los dos 3153 se deshicieron; queda el 6673

    def test_sin_legendarios_core_vacio_y_lineas_no_truena(self):
        ev = [compra(1055), compra(1001)]  # solo inicio y botas tier 1: nada legendario
        b = builds.build_de(*mk(eventos=ev), "yo", ITEMS)
        self.assertEqual((b["core"], b["botas"]), ([], None))
        r = builds.resumir([b], ITEMS, {})
        self.assertEqual(r["core"], [])
        ls = builds.lineas(r, "Tú")
        self.assertEqual(len(ls), 3)
        self.assertIn("-; botas -", ls[0])

    def test_mejores_una_region_vacia(self):
        ahora = 1_700_000_000.0
        match, tl = mk(puuid="top1", champ="Yone", pos="MIDDLE", mid="KR_M1")

        def fake_get(url, ttl=None, riot=False):
            if "la1.api.riotgames.com" in url and "leagues" in url:
                return dict(entries=[])                    # la1 sin Challenger ni GM
            if "kr.api.riotgames.com" in url and "challengerleagues" in url:
                return dict(entries=[dict(puuid="top1", leaguePoints=1000)])
            if "kr.api.riotgames.com" in url and "grandmasterleagues" in url:
                return dict(entries=[])
            if "/by-puuid/top1/by-champion/" in url:
                return dict(lastPlayTime=ahora * 1000)
            if "/accounts/by-puuid/top1" in url:
                return dict(gameName="Uno", tagLine="KR1")
            if "/matches/by-puuid/top1/ids" in url:
                return ["KR_M1"]
            if url.endswith("/matches/KR_M1/timeline"):
                return tl
            if url.endswith("/matches/KR_M1"):
                return match
            if "/top?count=1" in url: return []           # nadie del top lo tiene de más jugado: va al respaldo
            raise AssertionError(f"URL inesperada: {url}")

        with mock.patch.object(builds, "get", fake_get), mock.patch.object(builds, "REGIONES", {"la1": "americas", "kr": "asia"}):
            top = builds.mejores(777, "Yone", "MIDDLE", ahora=ahora)
        self.assertEqual([(m["metadata"]["matchId"], q) for m, _, _, q in top],
                         [("KR_M1", "Uno#KR1 (kr, 1000 LP)")])

    def test_onetrick_del_top_con_su_puesto(self):  # pedido del usuario: Challenger del top cuyo campeón más jugado es este
        ahora = time.time()
        _, tl = mk(); match = {"metadata": {"matchId": "KR_9"}, "info": {"participants": [{"puuid": "rank1", "championName": "Yone", "teamPosition": "MIDDLE"}]}}
        def fake_get(url, ttl=None, riot=False):
            if "challengerleagues" in url:
                return dict(entries=[dict(puuid="otro", leaguePoints=2100), dict(puuid="rank1", leaguePoints=2000)] if "kr." in url else [])
            if "/by-puuid/otro/top?count=1" in url: return [dict(championId=1, lastPlayTime=ahora * 1000)]   # main de otro campeón
            if "/by-puuid/rank1/top?count=1" in url: return [dict(championId=777, lastPlayTime=ahora * 1000)]
            if "/accounts/by-puuid/rank1" in url: return dict(gameName="Faker", tagLine="KR1")
            if "/matches/by-puuid/rank1/ids" in url: return ["KR_9"]
            if url.endswith("/timeline"): return tl
            if url.endswith("/matches/KR_9"): return match
            raise AssertionError(f"URL inesperada: {url}")
        with mock.patch.object(builds, "get", fake_get), mock.patch.object(builds, "REGIONES", {"la1": "americas", "kr": "asia"}):
            top = builds.mejores(777, "Yone", "MIDDLE", ahora=ahora)
        self.assertEqual([q for *_, q in top], ["Faker#KR1 (KR, #2 Challenger, 2000 LP)"])
        self.assertFalse(builds.onetrick([dict(championId=777, lastPlayTime=0)], 777, ahora))  # no lo juega hace meses

    def test_item_sold_no_cuenta_en_core(self):
        # un legendario vendido sale del core (arreglado en bb6b9b8; antes quedaba ["3153", "6673"])
        ev = [compra(3153), compra(6673), venta(3153)]
        b = builds.build_de(*mk(eventos=ev), "yo", ITEMS)
        self.assertEqual(b["core"], ["6673"])

    def test_botas_vendidas_siguen_contando(self):
        # las botas tier 2 vendidas al final (por el 6.º ítem) no son legendarias: siguen como `botas`
        ev = [compra(3006), venta(3006)]
        b = builds.build_de(*mk(eventos=ev), "yo", ITEMS)
        self.assertEqual(b["botas"], "3006")

    def test_guardado_sin_la_clave_pedida(self):
        r = builds.resumir([builds.build_de(*mk(eventos=[compra(3153)]), "yo", ITEMS)], ITEMS, {})
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(builds, "META", pathlib.Path(tmp)):
            (builds.META / "builds.json").write_text(json.dumps({"Yone|MIDDLE|tu": r}), encoding="utf-8")
            self.assertEqual(builds.guardado("Yone", "TOP"), [])          # solo existe Yone|MIDDLE|tu
            self.assertEqual(len(builds.guardado("Yone", "MIDDLE")), 3)  # y MIDDLE sí la da (la tuya)


if __name__ == "__main__":
    unittest.main()
