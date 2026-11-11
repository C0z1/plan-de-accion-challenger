"""Pruebas de timers v0.12 (F10): sobre la partida real anonimizada, ningún DragonKill/BaronKill
ocurre antes de la aparición que companion.objetivos() predice en la foto previa. Sin red ni cliente."""
import json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import companion

FIXTURE = pathlib.Path(__file__).resolve().parent / "fixtures" / "vivo" / "partida_completa.jsonl"
ME = {"team": "ORDER"}  # el jugador «Yo» de la fixture es ORDER (ver allPlayers)


def _frames():
    with open(FIXTURE, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class Timers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fotos = _frames()

    def _nuevos(self, nombre):
        """Por cada kill nuevo de `nombre` (buffer de eventos creciente): (foto previa, EventTime)."""
        visto = set()
        for i, foto in enumerate(self.fotos):
            for e in ((foto.get("events") or {}).get("Events") or []):
                if e.get("EventName") != nombre:
                    continue
                k = (round(e.get("EventTime") or 0, 3), str(e.get("KillerName") or ""))
                if k in visto:
                    continue
                visto.add(k)
                yield (self.fotos[i - 1] if i else foto), e.get("EventTime") or 0

    def _verificar(self, nombre, campo):
        for previa, t in self._nuevos(nombre):
            o = companion.objetivos(previa, ME)
            falta = o[campo]
            if falta is None:  # ya estaba vivo en la foto previa: matarlo ahora es válido
                continue
            aparicion = ((previa.get("gameData") or {}).get("gameTime") or 0) + falta
            self.assertGreaterEqual(t, aparicion - 1e-6, f"{nombre} a los {t}s, antes de {aparicion}s")

    def test_dragon_solo_tras_su_aparicion(self):
        self._verificar("DragonKill", "dragon")

    def test_baron_solo_tras_su_aparicion(self):
        self._verificar("BaronKill", "baron")

    # arreglado: v0.12 F10: tras el alma (4 dragones) el siguiente es el Anciano a los 6:00, no un elemental a los 5:00
    def test_anciano_tras_el_alma_a_los_6_min(self):
        """Bug del shortcut de companion.objetivos: asume dragón cada 300 s también después del alma.
        Tras el 4.º dragón de un equipo, objectives() debería devolver 360 s (Anciano) y hoy devuelve 300."""
        ps = [{"riotIdGameName": "A1", "team": "ORDER", "scores": {"kills": 0}},
              {"riotIdGameName": "R1", "team": "CHAOS", "scores": {"kills": 0}}]
        ev = {"Events": [{"EventName": "DragonKill", "EventTime": t, "KillerName": "A1"} for t in (300, 600, 900, 1200)]}
        o = companion.objetivos({"allPlayers": ps, "events": ev, "gameData": {"gameTime": 1200}}, ME)
        self.assertEqual(o["dragon"], 360)


if __name__ == "__main__":
    unittest.main()
