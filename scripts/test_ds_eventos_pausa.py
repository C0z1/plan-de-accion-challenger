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


class Pausa(unittest.TestCase):
    META = {"minuto": 17, "objetivos": {"dragon": 400, "baron": None}, "recibido": 1000.0}

    def _dragon(self, meta, ahora):
        return next((t for t, _ in overlay.partes(meta, ahora, {}) if t.startswith(("Dragón", "! Dragón"))), None)

    def test_sin_pausa_el_timer_baja_con_la_edad(self):  # contraste: ya pasa hoy
        self.assertEqual(self._dragon(self.META, 1100.0), "Dragón 5:00")


    def test_con_pausa_usa_edad_cero(self):  # el timer no baja aunque recibido sea viejo
        pausado = {**self.META, "pausa": True}
        self.assertEqual(self._dragon(pausado, 1100.0), "Dragón 6:40")
        self.assertEqual(self._dragon(pausado, 5000.0), "Dragón 6:40")

    def test_pausa_false_o_ausente_no_congela(self):
        self.assertEqual(self._dragon({**self.META, "pausa": False}, 1100.0), "Dragón 5:00")
        # y pausa True no cambia nada si no hay timers (no lanza)
        self.assertEqual(overlay.partes({**self.META, "pausa": True, "objetivos": {}}, 1100.0, {}), overlay.partes({**self.META, "objetivos": {}}, 1000.0, {}))


if __name__ == "__main__": unittest.main()
