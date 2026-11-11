"""A1/A2/A3 (commits 08762e4, 2cb1c12, 9012a67) → overlay v0.11, casos borde. Sin red.
- companion.precios/valor_items/oro_lineas: ítem sin itemID, count 0/None, jugador sin ítems o None, rival None, Data Dragon caído.
- companion.completos/aviso_pico: rival sin position (ARAM/NONE), ítems repetidos, vender y recomprar (la clave es la cantidad).
- overlay.partes: minuto 14 y 25 exactos, muertes14 = 0, oro enorme/negativo.
- aviso_pico y oro_lineas sobre TODAS las fotos reales de datos/vivo/*.jsonl (skip si no existe; la foto puede venir como {"foto": ...}).
"""
import json, pathlib, unittest
from unittest import mock

import builds, companion, overlay

BASE = pathlib.Path(__file__).resolve().parent.parent
VIVO = BASE / "datos" / "vivo"

PR = {"3057": 900, "1055": 450, "2003": 50, "3100": 3100, "6692": 3200}
LEG = {"3100", "6692"}


class Precios(unittest.TestCase):
    def setUp(self): companion.PRECIOS.clear(); companion.LEGENDARIOS.clear()

    def test_data_dragon_caido_no_tumba_y_devuelve_vacio(self):
        with mock.patch.object(builds, "ddragon", side_effect=Exception("sin red / ddragon caído")):
            self.assertEqual(companion.precios(), {})
        self.assertEqual(companion.PRECIOS, {})
        self.assertEqual(companion.LEGENDARIOS, set())

    def test_llena_precios_y_legendarios_una_vez(self):
        items = {"3057": {"gold": {"total": 900}, "into": ["3118"], "tags": [], "maps": {"11": True}},
                 "3100": {"gold": {"total": 3100}, "tags": [], "maps": {"11": True}},
                 "3006": {"gold": {"total": 1100}, "tags": ["Boots"], "maps": {"11": True}}}
        with mock.patch.object(builds, "ddragon", return_value=(items, {}, {})):
            self.assertEqual(companion.precios(), {"3057": 900, "3100": 3100, "3006": 1100})
        self.assertEqual(companion.LEGENDARIOS, {"3100"})  # componente y botas no son «completos»


class ValorItems(unittest.TestCase):
    def test_item_sin_item_id_no_cuenta(self):
        self.assertEqual(companion.valor_items({"items": [{"price": 650}]}, PR), 0)

    def test_count_faltante_o_none_cuenta_uno(self):
        self.assertEqual(companion.valor_items({"items": [{"itemID": 3057}]}, PR), 900)
        self.assertEqual(companion.valor_items({"items": [{"itemID": 3057, "count": None}]}, PR), 900)

    def test_count_cero_cuenta_como_uno(self):  # (count or 1): el 0 cae al default; en vivo nunca aparece count 0
        self.assertEqual(companion.valor_items({"items": [{"itemID": 2003, "count": 0}]}, PR), 50)

    def test_count_varios_suma(self):
        self.assertEqual(companion.valor_items({"items": [{"itemID": 2003, "count": 3}]}, PR), 150)

    def test_jugador_sin_items_o_none(self):
        self.assertEqual(companion.valor_items({"items": []}, PR), 0)
        self.assertEqual(companion.valor_items({}, PR), 0)
        self.assertEqual(companion.valor_items(None, PR), 0)

    def test_sin_precios_devuelve_none(self):
        self.assertIsNone(companion.valor_items({"items": [{"itemID": 3057}]}, {}))


class OroLineas(unittest.TestCase):
    def test_data_dragon_caido_devuelve_none(self):
        self.assertIsNone(companion.oro_lineas({"allPlayers": []}, {"team": "ORDER"}, None, {}))

    def test_rival_none(self):
        yo = {"team": "ORDER", "items": [{"itemID": 3057}]}
        self.assertEqual(companion.oro_lineas({"allPlayers": [yo]}, yo, None, PR),
                         {"tu": 900, "rival": None, "equipo": 900, "equipo_rival": 0})

    def test_equipo_suma_por_lado(self):
        yo = {"team": "ORDER", "items": [{"itemID": 3057}]}
        al = {"team": "ORDER", "items": [{"itemID": 1055}]}
        ri = {"team": "CHAOS", "items": [{"itemID": 2003, "count": 2}]}
        self.assertEqual(companion.oro_lineas({"allPlayers": [yo, al, ri]}, yo, ri, PR),
                         {"tu": 900, "rival": 100, "equipo": 1350, "equipo_rival": 100})


class Completos(unittest.TestCase):
    def test_solo_completos_en_orden_de_casillas(self):
        p = {"items": [{"itemID": 1055, "displayName": "Daga"}, {"itemID": 3100, "displayName": "Liche"},
                       {"itemID": 6692, "displayName": "Eclipse"}]}
        self.assertEqual(companion.completos(p, LEG), ["Liche", "Eclipse"])

    def test_item_repetido_cuenta_cada_copia(self):
        p = {"items": [{"itemID": 3100, "displayName": "Liche"}, {"itemID": 3100, "displayName": "Liche"}]}
        self.assertEqual(companion.completos(p, LEG), ["Liche", "Liche"])

    def test_sin_items_o_none(self):
        self.assertEqual(companion.completos({}, LEG), [])
        self.assertEqual(companion.completos(None, LEG), [])


class AvisoPico(unittest.TestCase):
    def foto(self, mios, suyos, pos="MIDDLE", t=720):
        it = lambda ids: [{"itemID": i, "displayName": f"Item{i}"} for i in ids]
        ps = [{"riotId": "yo#1", "position": pos, "team": "ORDER", "championName": "Sylas", "items": it(mios)}]
        if suyos is not None:
            ps.append({"riotId": "el#2", "position": pos, "team": "CHAOS", "championName": "Zed", "items": it(suyos)})
        return {"activePlayer": {"riotId": "yo#1"}, "gameData": {"gameTime": t}, "allPlayers": ps}

    def test_rival_sin_position_devuelve_none(self):
        self.assertIsNone(companion.aviso_pico(self.foto([], [3100], pos="NONE"), LEG))  # ARAM/KIWI: position NONE

    def test_sin_rival_de_linea_devuelve_none(self):
        d = {"activePlayer": {"riotId": "yo#1"}, "gameData": {"gameTime": 720},
             "allPlayers": [{"riotId": "yo#1", "position": "MIDDLE", "team": "ORDER", "items": []}]}
        self.assertIsNone(companion.aviso_pico(d, LEG))

    def test_solo_avisa_si_te_saca_ventaja(self):
        self.assertIsNone(companion.aviso_pico(self.foto([], [1055]), LEG))       # componente: nada
        self.assertIsNone(companion.aviso_pico(self.foto([3100], [3100]), LEG))   # parejos
        self.assertIsNone(companion.aviso_pico(self.foto([3100, 6692], [3100]), LEG))  # vas arriba
        c, txt = companion.aviso_pico(self.foto([], [3100]), LEG)
        self.assertEqual((c, "Min 12" in txt, "Zed terminó Item3100" in txt), ("pico:1:Item3100", True, True))

    def test_vender_y_terminar_otro_si_reavisa(self):  # bug que halló DeepSeek: la clave ahora lleva el ítem
        a = companion.aviso_pico(self.foto([], [3100, 6692]), LEG)[0]
        b = companion.aviso_pico(self.foto([], [3100, 3142]), LEG | {"3142"})[0]  # vende 6692 y termina OTRO completo
        self.assertEqual((a, b), ("pico:2:Item6692", "pico:2:Item3142"))


class Partes(unittest.TestCase):
    META = {"nivel": 11, "nivel_rival": 12, "rival": "Ahri", "cs": 71, "rival_cs": 140, "recibido": 1000.0,
            "objetivos": {"dragon": 90, "baron": None}}

    def c(self, m, minuto):
        return dict(overlay.partes({**self.META, "muertes14": m, "minuto": minuto}, 1000.0))

    def test_minuto_14_exacto_entra_y_25_exacto_no(self):
        self.assertEqual(self.c(1, 14)["Muertes 14–25: 1/2"], overlay.TXT)
        self.assertFalse(any("Muertes" in x for x in self.c(3, 25)))  # 25 ya no entra en < 25

    def test_muertes14_cero_se_muestra(self):
        self.assertEqual(self.c(0, 18)["Muertes 14–25: 0/2"], overlay.TXT)

    def test_oro_enorme_y_negativo_no_tumba(self):
        m = {**self.META, "minuto": 8}  # el oro de línea se ve del 6 al 14 (prioridad por fase, F6)
        self.assertEqual(dict(overlay.partes({**m, "oro": {"tu": 10**9, "rival": 0}}, 1000.0))["Oro +1000000000"], overlay.TXT)
        self.assertEqual(dict(overlay.partes({**m, "oro": {"tu": 0, "rival": 10**9}}, 1000.0))["▼ Oro -1000000000"], overlay.ROSA)
        self.assertEqual(dict(overlay.partes({**m, "oro": {"tu": -5000, "rival": 0}}, 1000.0))["▼ Oro -5000"], overlay.ROSA)


@unittest.skipUnless(VIVO.exists() and any(VIVO.glob("*.jsonl")), "sin datos/vivo")
class VivoReal(unittest.TestCase):
    def test_aviso_pico_y_oro_lineas_sobre_todas_las_fotos(self):
        ids = set()
        for f in VIVO.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                d = json.loads(line.strip())
                if "foto" in d: d = d["foto"]
                for p in (d.get("allPlayers") or []):
                    ids |= {str(i["itemID"]) for i in (p.get("items") or []) if i.get("itemID") is not None}
        pr, leg = {i: 100 for i in ids}, set(ids)  # precio sintético (sin red): solo importa que no lance
        probadas = 0
        for f in VIVO.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                d = json.loads(line.strip())
                if "foto" in d: d = d["foto"]
                me, rival = companion.yo_rival(d)
                if me is not None:
                    self.assertEqual(set(companion.oro_lineas(d, me, rival, pr)), {"tu", "rival", "equipo", "equipo_rival"}, f.name)
                r = companion.aviso_pico(d, leg)
                self.assertTrue(r is None or (isinstance(r, tuple) and len(r) == 2), f.name)
                probadas += 1
        self.assertGreater(probadas, 0)


if __name__ == "__main__":
    unittest.main()
