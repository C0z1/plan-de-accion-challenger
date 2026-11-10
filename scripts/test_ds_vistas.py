"""Pruebas de DeepSeek para las ventanas nuevas de HTC (turno 8, v0.3.0): vistas.errores, vistas.cumple y evento(pos).
Sin red ni ventanas; solo librería estándar. Los timelines de errores son sintéticos (chicos, sin nombres ni PUUID reales)."""
import json, os, pathlib, sys, tempfile, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
if not (pathlib.Path(os.environ.get("DATOS_DIR") or AQUI.parent / "datos" / "raw") / "perfil.json").exists():
    os.environ["DATOS_DIR"] = str(AQUI / "fixtures" / "datos")  # CI o clon nuevo, como test_draft

import companion_web as web  # noqa: E402
import vistas  # noqa: E402


class Cumple(unittest.TestCase):
    def test_cumple_con_none_y_regla_sin_campo(self):
        # turno 8 (b): una regla sin campo queda {ok: None, n: 0} (no truena) y un dato None se descarta del conteo
        r_ok = {"texto": "x", "numero": "n", "minuto": "6", "metrica": "nivel", "campo": "nivel6", "ok": lambda x: x >= 0}
        r_sin = {"texto": "y", "numero": "n", "minuto": "14", "metrica": "vision"}  # sin campo ni ok
        gs = [{"nivel6": -1}, {"nivel6": 1}, {"nivel6": None}, {}]
        out = vistas.cumple([r_ok, r_sin], gs)
        self.assertEqual(out[0]["ok"], 1)  # solo el +1; None y la ausencia se descartan
        self.assertEqual(out[0]["n"], 2)
        self.assertIsNone(out[1]["ok"])
        self.assertEqual(out[1]["n"], 0)


class Evento(unittest.TestCase):
    def test_pos_se_guarda_y_champselect_la_resetea(self):
        # turno 8 (c): pos llega a ESTADO y la fase ChampSelect la borra (y borra draft/meta/fin)
        viejo = dict(web.ESTADO)
        try:
            web.evento(("pos", "TOP"))
            self.assertEqual(web.ESTADO["pos"], "TOP")
            web.evento(("fase", "ChampSelect"))
            self.assertIsNone(web.ESTADO["pos"])
            self.assertIsNone(web.ESTADO["draft"])
            self.assertEqual(web.ESTADO["fase"], "ChampSelect")
        finally:
            web.ESTADO.clear(); web.ESTADO.update(viejo)


class Errores(unittest.TestCase):
    """turno 8 (a): la definición de sin_objetivo usa killerTeamId (épico) y teamId (torre dueña) como asume Opus."""

    def _juego(self, d, eventos):
        raw = pathlib.Path(d); (raw / "timeline").mkdir()
        match = raw / "XX_999.json"
        match.write_text(json.dumps({"info": {"participants": [
            {"participantId": 1, "teamId": 100, "teamPosition": "MIDDLE", "championName": "Sylas"},
            {"participantId": 2, "teamId": 200, "teamPosition": "MIDDLE", "championName": "Zed"}]}}), encoding="utf-8")
        (raw / "timeline" / match.name).write_text(json.dumps({"info": {"frames": [{"events": eventos}]}}), encoding="utf-8")
        return [dict(f=match, pid=1, champ="Sylas")]

    def _sin_objetivo(self, eventos):
        with tempfile.TemporaryDirectory() as d:
            return vistas.errores(self._juego(d, eventos), 20)["partidas"]["sin_objetivo"]

    def test_sin_objetivo_solo_si_no_hay_objetivo_de_tu_equipo_en_60s(self):
        muerte = {"type": "CHAMPION_KILL", "timestamp": 900000, "victimId": 1, "killerId": 2}
        dragon_tuyo = {"type": "ELITE_MONSTER_KILL", "timestamp": 930000, "killerTeamId": 100}
        torre_rival = {"type": "BUILDING_KILL", "timestamp": 920000, "teamId": 200}
        torre_tuya = {"type": "BUILDING_KILL", "timestamp": 920000, "teamId": 100}
        self.assertEqual(self._sin_objetivo([muerte]), 1)               # morir sin nada después: error
        self.assertEqual(self._sin_objetivo([muerte, dragon_tuyo]), 0)  # tu equipo mata dragón en el minuto siguiente
        self.assertEqual(self._sin_objetivo([muerte, torre_rival]), 0)  # tu equipo tira una torre rival
        self.assertEqual(self._sin_objetivo([muerte, torre_tuya]), 1)   # perder tu propia torre no es objetivo tuyo

    def test_sin_objetivo_borde_60s_exactos(self):
        # turno 9 iter 3 (b): la ventana es inclusiva, así que a exactamente 60 s (antes o después) no es error
        muerte = {"type": "CHAMPION_KILL", "timestamp": 900000, "victimId": 1, "killerId": 2}
        drag = lambda t: {"type": "ELITE_MONSTER_KILL", "timestamp": t, "killerTeamId": 100}
        self.assertEqual(self._sin_objetivo([muerte, drag(900000 + 60000)]), 0)  # 60 s después: no es error
        self.assertEqual(self._sin_objetivo([muerte, drag(900000 - 60000)]), 0)  # 60 s antes: no es error
        self.assertEqual(self._sin_objetivo([muerte, drag(900000 + 61000)]), 1)  # 61 s: ya es error

    def test_sin_objetivo_objetivo_antes_del_14_cuenta(self):
        # turno 9 iter 3 (c): un objetivo de tu equipo antes del 14:00 anula igual la muerte de las 14:30
        muerte = {"type": "CHAMPION_KILL", "timestamp": 870000, "victimId": 1, "killerId": 2}   # 14:30
        drag_antes = {"type": "ELITE_MONSTER_KILL", "timestamp": 820000, "killerTeamId": 100}    # 13:40
        self.assertEqual(self._sin_objetivo([muerte, drag_antes]), 0)


if __name__ == "__main__":
    unittest.main()
