"""A1 (ronda 2): companion.unir_eventos(d, previos) y la pausa de overlay.partes. Sin red. Hoy fallan porque aun no existen
(expectedFailure); cuando Opus los implemente se les quita el decorador.
unir_eventos(d, previos): d con events.Events unidos por clave (EventName, EventTime); previos = la foto o lista de eventos previa.
Se asume que `previos` es una foto completa (dict con events.Events); si Opus elige otra forma, ajustar _previos()."""
import copy, json, unittest

import companion, overlay

YO, RIVAL = "Yo#LAN", "Rival#EUW"


def _jugadores():
    return [{"riotId": YO, "summonerName": "Yo", "riotIdGameName": "Yo", "team": "ORDER", "position": "MIDDLE", "level": 14, "scores": {"kills": 1, "deaths": 2, "assists": 0, "creepScore": 100}},
            {"riotId": RIVAL, "summonerName": "Rival", "riotIdGameName": "Rival", "team": "CHAOS", "position": "MIDDLE", "level": 13, "scores": {"kills": 2, "deaths": 1, "assists": 0, "creepScore": 90}}]


def foto(eventos, t=1050):
    return {"activePlayer": {"riotId": YO, "summonerName": "Yo"}, "allPlayers": _jugadores(),
            "gameData": {"gameMode": "CLASSIC", "gameTime": t}, "events": {"Events": eventos}}


GS0 = {"EventName": "GameStart", "EventTime": 0.0}
DRAGON = {"EventName": "DragonKill", "EventTime": 600.0, "KillerName": "Yo"}
MUERTE1 = {"EventName": "ChampionKill", "EventTime": 900.0, "VictimName": YO, "KillerName": RIVAL}
MUERTE2 = {"EventName": "ChampionKill", "EventTime": 1000.0, "VictimName": YO, "KillerName": RIVAL}
PREVIA = foto([GS0, DRAGON, MUERTE1, MUERTE2])
TRAS_RECONNECT = foto([{"EventName": "GameStart", "EventTime": 1043.0}])


def unir():
    f = getattr(companion, "unir_eventos", None)
    if f is None: raise AssertionError("companion.unir_eventos(d, previos) no existe todavia")
    return f


def nombres(d): return [(e["EventName"], e["EventTime"]) for e in d["events"]["Events"]]


def clave(e):
    """Clave de dedupe del cambio pedido: el evento completo menos EventID."""
    return json.dumps({k: v for k, v in sorted(e.items()) if k != "EventID"}, sort_keys=True)


class UnirEventos(unittest.TestCase):

    def test_reinicio_tras_reconnect_da_lo_mismo_que_la_foto_previa(self):
        d = unir()(copy.deepcopy(TRAS_RECONNECT), copy.deepcopy(PREVIA))
        me, _ = companion.yo_rival(PREVIA)
        self.assertEqual(companion.objetivos(d, me), companion.objetivos(PREVIA, me))
        self.assertEqual(companion.muertes14(d), companion.muertes14(PREVIA))
        self.assertEqual(companion.muertes14(d), 2)


    def test_game_start_con_tiempo_mayor_que_cero_se_descarta(self):
        d = unir()(copy.deepcopy(TRAS_RECONNECT), copy.deepcopy(PREVIA))
        self.assertEqual([x for x in nombres(d) if x[0] == "GameStart"], [("GameStart", 0.0)])


    def test_superconjunto_no_duplica(self):
        nueva = foto([GS0, DRAGON, MUERTE1, MUERTE2, {"EventName": "TurretKilled", "EventTime": 1040.0, "TurretKilled": "Turret_TChaos_L1", "KillerName": "Yo"}])
        d = unir()(copy.deepcopy(nueva), copy.deepcopy(PREVIA))
        n = nombres(d); self.assertEqual(len(n), len(set(n)))
        self.assertEqual(len(n), 5)


    def test_mismo_tiempo_con_distinto_nombre_se_conservan_ambos(self):
        previa = foto([GS0, {"EventName": "DragonKill", "EventTime": 600.0, "KillerName": "Yo"}])
        nueva = foto([{"EventName": "ChampionKill", "EventTime": 600.0, "VictimName": RIVAL, "KillerName": "Yo"}])
        n = nombres(unir()(nueva, previa))
        self.assertIn(("DragonKill", 600.0), n); self.assertIn(("ChampionKill", 600.0), n)


    def test_previos_none_o_d_sin_events_deja_d_intacta(self):
        d = copy.deepcopy(TRAS_RECONNECT)
        self.assertEqual(unir()(copy.deepcopy(d), None), d)
        sin = {"activePlayer": {}, "allPlayers": [], "gameData": {"gameTime": 5}}
        self.assertEqual(unir()(copy.deepcopy(sin), copy.deepcopy(PREVIA)), sin)
        self.assertIsNone(unir()(None, copy.deepcopy(PREVIA)))


    def test_no_modifica_los_previos(self):
        previa = copy.deepcopy(PREVIA)
        unir()(copy.deepcopy(TRAS_RECONNECT), previa)
        self.assertEqual(previa, PREVIA)


    def test_dos_kills_del_mismo_tick_se_conservan_ambos(self):
        """Falla hoy: la clave es solo (EventName, EventTime) y descarta el segundo kill del mismo tick."""
        k1 = {"EventName": "ChampionKill", "EventTime": 900.0, "VictimName": YO, "KillerName": RIVAL, "EventID": 1}
        k2 = {"EventName": "ChampionKill", "EventTime": 900.0, "VictimName": RIVAL, "KillerName": YO, "EventID": 2}
        previa = foto([GS0, k1, k2])
        d = foto([{"EventName": "GameStart", "EventTime": 500.0}, {**k1, "EventID": 99}])
        kills = [e for e in unir()(d, previa)["events"]["Events"] if e["EventName"] == "ChampionKill"]
        self.assertEqual(len(kills), 2)
        self.assertEqual({k["VictimName"] for k in kills}, {YO, RIVAL})


    def test_sin_reinicio_devuelve_la_lista_identica_y_en_su_orden(self):
        """Falla hoy: siempre ordena por EventTime aunque no hubo reinicio."""
        evs = [MUERTE2, GS0, DRAGON, MUERTE1]  # desordenada, sin GameStart > 0 y con tantos eventos como PREVIA (menos eventos contaría como reinicio)
        d = foto(evs); original = d["events"]["Events"]
        out = unir()(d, copy.deepcopy(PREVIA))
        self.assertIs(out, d); self.assertIs(out["events"]["Events"], original)
        self.assertEqual([(e["EventName"], e["EventTime"]) for e in out["events"]["Events"]],
                         [(e["EventName"], e["EventTime"]) for e in evs])


    def test_reinicio_solo_por_menos_eventos_une(self):
        """Menos eventos que previos cuenta como reinicio aunque no haya GameStart > 0."""
        previa = foto([GS0, DRAGON, MUERTE1])
        d = foto([GS0, DRAGON])
        n = unir()(copy.deepcopy(d), copy.deepcopy(previa))
        self.assertEqual(sorted(clave(e) for e in n["events"]["Events"]),
                         sorted(clave(e) for e in [GS0, DRAGON, MUERTE1]))


    def test_doble_reconexion_no_duplica(self):
        """Unir la foto cruda dos veces no repite eventos."""
        previa = foto([GS0, DRAGON, MUERTE1])
        cruda = foto([{"EventName": "GameStart", "EventTime": 500.0}, MUERTE1])
        dos = unir()(copy.deepcopy(cruda), unir()(copy.deepcopy(cruda), copy.deepcopy(previa)))
        self.assertEqual(len(dos["events"]["Events"]), 3)
        self.assertEqual(len({clave(e) for e in dos["events"]["Events"]}), 3)


    def test_gamestart_cero_previo_y_dragon_nuevo(self):
        """GameStart@0 previo se conserva y el DragonKill del reinicio se suma."""
        previa = foto([GS0])
        d = foto([{"EventName": "GameStart", "EventTime": 500.0}, {"EventName": "DragonKill", "EventTime": 520.0, "KillerName": "Yo"}])
        n = unir()(copy.deepcopy(d), copy.deepcopy(previa))
        self.assertEqual([(e["EventName"], e["EventTime"]) for e in n["events"]["Events"]],
                         [("GameStart", 0.0), ("DragonKill", 520.0)])


    def test_otra_partida_queda_intacta(self):
        """t(previos) > t(d): otra partida, d se devuelve sin tocar."""
        previa = foto([GS0, DRAGON, MUERTE1], t=1100)
        d = foto([GS0, MUERTE2], t=1000); original = d["events"]["Events"]
        out = unir()(d, copy.deepcopy(previa))
        self.assertIs(out, d); self.assertIs(out["events"]["Events"], original)
        self.assertEqual([(e["EventName"], e["EventTime"]) for e in original],
                         [("GameStart", 0.0), ("ChampionKill", 1000.0)])


    def test_temblor_float32_no_cuenta_como_otra_partida(self):
        """El gameTime tiembla un paso de float32 al reconectar (122.41705322 → 122.41704559): misma partida."""
        previa = foto([GS0, {"EventName": "MinionsSpawning", "EventTime": 30.0}], t=122.41705322)
        d = foto([{"EventName": "GameStart", "EventTime": 122.41704559}], t=122.41704559)
        self.assertEqual(nombres(unir()(d, copy.deepcopy(previa))),
                         [("GameStart", 0.0), ("MinionsSpawning", 30.0)])


    def test_cadena_de_dos_reconexiones_y_foto_en_pausa_siempre_dos_eventos(self):
        previa = foto([GS0, {"EventName": "MinionsSpawning", "EventTime": 30.0}], t=122.4)
        unida = unir()(foto([{"EventName": "GameStart", "EventTime": 500.0}], t=500.0), copy.deepcopy(previa))
        self.assertEqual(len(unida["events"]["Events"]), 2)
        pausa = foto([GS0, {"EventName": "MinionsSpawning", "EventTime": 30.0}], t=122.4)  # reloj congelado, mismos eventos
        unida = unir()(pausa, copy.deepcopy(unida))
        self.assertEqual(len(unida["events"]["Events"]), 2)
        unida = unir()(foto([{"EventName": "GameStart", "EventTime": 600.0}], t=600.0), copy.deepcopy(unida))
        self.assertEqual(len(unida["events"]["Events"]), 2)
        self.assertEqual(len({clave(e) for e in unida["events"]["Events"]}), 2)


    def test_dragon_previo_se_conserva_con_temblor_de_49e4_tras_reinicio(self):
        previa = foto([GS0, {"EventName": "DragonKill", "EventTime": 400.0, "KillerName": "Yo"}], t=8220.0)
        d = foto([{"EventName": "GameStart", "EventTime": 8219.99951}], t=8219.99951)
        self.assertEqual(nombres(unir()(d, copy.deepcopy(previa))),
                         [("GameStart", 0.0), ("DragonKill", 400.0)])


    def test_diferencia_de_11_s_es_otra_partida(self):
        previa = foto([GS0], t=123.5)
        d = foto([GS0, DRAGON], t=122.4); original = d["events"]["Events"]
        out = unir()(d, copy.deepcopy(previa))
        self.assertIs(out, d); self.assertIs(out["events"]["Events"], original)


    def test_reloj_mucho_menor_es_otra_partida(self):
        previa = foto([GS0, DRAGON], t=1500)
        d = foto([GS0], t=12); original = d["events"]["Events"]
        out = unir()(d, copy.deepcopy(previa))
        self.assertIs(out, d); self.assertIs(out["events"]["Events"], original)


if __name__ == "__main__": unittest.main()
