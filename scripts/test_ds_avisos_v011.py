"""Avisos v0.11 (noche-challenger/avisos-v011.md): pruebas sobre el código ACTUAL de scripts/companion.py.
- corto ≤ 48 caracteres: hoy los avisos son una sola frase larga, así que superan 48 (expectedFailure).
- largo ≤ 25 palabras: hoy lo superan aviso_pico, aviso_regreso (con CS) y aviso_muertes (expectedFailure).
- sin órdenes en 2ª persona («No pelees…» → «Tu regla: …») y sin palabras de la lista negra.
Los expectedFailure llevan «pasa cuando Opus aplique avisos-v011.md». Sin red.
"""
import re, unittest

import companion

# Lista negra (igual que avisos-v011.md): lo que la franja nunca debe decir, como subcadena en minúsculas.
PROHIBIDO = [
    "cooldown", "enfriamiento",       # timers de hechizos: no se ven en Tab (información obfuscada)
    "flash", "destello",              # cooldown del Flash rival, no visible en la partida
    "ultimate", "definitiva",         # cooldown de la definitiva rival, no visible
    "smite", "castigo",               # cooldown del smite del jungla, no visible
    "respawn", "reaparece",           # timer de reaparición del rival, no visible
    "mmr", "elo",                     # rating/ELO que no sale en la partida
    "probabilidad",                   # probabilidad de ganar: conclusión sobre el resultado
    "campamento",                     # posición de campamentos de jungla (no visible)
    "el jungla está", "el jungla va", # posición de un jugador que no ves
    "troll", "inting", "afk",         # juicios de compañeros
]

# Imperativos tácticos en 2ª persona que los avisos deben cambiar a infinitivo («Tu regla: …»).
IMPERATIVOS = ["no pelees", "no tradees", "no roamees", "farmea", "espera", "quédate", "juega"]


def _jugador(riot_id, pos, team, champ, nivel, cs, items=None):
    return {"riotId": riot_id, "position": pos, "team": team, "championName": champ,
            "level": nivel, "scores": {"creepScore": cs}, "items": items or []}


def _rival(nivel=6, cs=60, items=None, champ="Zed"):
    return _jugador("el#2", "MIDDLE", "CHAOS", champ, nivel, cs, items)


def _foto(t, rival=None, events=None):
    return {"activePlayer": {"riotId": "yo#1"},
            "gameData": {"gameTime": t, "gameMode": "CLASSIC"},
            "allPlayers": [_jugador("yo#1", "MIDDLE", "ORDER", "Sylas", 5, 55)] + ([rival] if rival else []),
            "events": {"Events": events or []}}


def t_nivel():
    return companion.aviso_nivel(_foto(360, _rival(nivel=6)))  # min 6, 1 nivel abajo


def t_regreso():
    return companion.aviso_regreso(_foto(720, _rival(nivel=6, cs=70)))  # min 12, 1 nivel y 15 CS abajo


def t_muertes():
    evs = [{"EventName": "ChampionKill", "VictimName": "yo#1", "EventTime": 900},
           {"EventName": "ChampionKill", "VictimName": "yo#1", "EventTime": 930}]
    return companion.aviso_muertes(_foto(960, _rival(nivel=9, cs=100), evs))  # min 16, 2 muertes desde el 14


def t_minions():
    return companion.aviso_minions(_foto(630, _rival(nivel=6)), {"campeon": "Sylas", "minimo": 69})  # min 10, 55 CS


def t_pico():
    leg = {"6692"}
    r = _rival(nivel=9, cs=100, items=[{"itemID": 6692, "displayName": "Eclipse"}])
    return companion.aviso_pico(_foto(720, r), leg)[1]  # min 12, el rival termina un completo


TEXTOS = {"nivel": t_nivel, "regreso": t_regreso, "muertes": t_muertes, "minions": t_minions, "pico": t_pico}


def _palabras(t):
    return len(t.split())


class Fixtures(unittest.TestCase):
    def test_los_cinco_disparan(self):
        for nombre, f in TEXTOS.items():
            with self.subTest(aviso=nombre):
                t = f()
                self.assertIsInstance(t, str, t)
                self.assertTrue(t, t)


class Corto(unittest.TestCase):
    """La franja: corto ≤ 48 caracteres (hoy los avisos son una sola frase larga)."""
    # avisos-v011.md aplicado
    def test_nivel(self): self.assertLessEqual(len(t_nivel().corto), 48, t_nivel().corto)

    # avisos-v011.md aplicado
    def test_regreso(self): self.assertLessEqual(len(t_regreso().corto), 48, t_regreso().corto)

    # avisos-v011.md aplicado
    def test_muertes(self): self.assertLessEqual(len(t_muertes().corto), 48, t_muertes().corto)

    # avisos-v011.md aplicado
    def test_minions(self): self.assertLessEqual(len(t_minions().corto), 48, t_minions().corto)

    # avisos-v011.md aplicado
    def test_pico(self): self.assertLessEqual(len(t_pico().corto), 48, t_pico().corto)


class Largo(unittest.TestCase):
    """En vivo y post-partida: largo ≤ 25 palabras."""
    def test_nivel(self): self.assertLessEqual(_palabras(t_nivel()), 25, t_nivel())

    def test_minions(self): self.assertLessEqual(_palabras(t_minions()), 25, t_minions())

    # avisos-v011.md aplicado
    def test_regreso(self): self.assertLessEqual(_palabras(t_regreso()), 25, t_regreso())

    # avisos-v011.md aplicado
    def test_muertes(self): self.assertLessEqual(_palabras(t_muertes()), 25, t_muertes())

    # avisos-v011.md aplicado
    def test_pico(self): self.assertLessEqual(_palabras(t_pico()), 25, t_pico())


class SinImperativos(unittest.TestCase):
    """Sin órdenes tácticas en 2ª persona (hoy todas las tienen)."""
    # avisos-v011.md aplicado
    def test_nivel(self): self.assertEqual([w for w in IMPERATIVOS if re.search(rf"\b{w}\b", t_nivel().lower())], [], t_nivel())

    # avisos-v011.md aplicado
    def test_regreso(self): self.assertEqual([w for w in IMPERATIVOS if re.search(rf"\b{w}\b", t_regreso().lower())], [], t_regreso())

    # avisos-v011.md aplicado
    def test_muertes(self): self.assertEqual([w for w in IMPERATIVOS if re.search(rf"\b{w}\b", t_muertes().lower())], [], t_muertes())

    # avisos-v011.md aplicado
    def test_minions(self): self.assertEqual([w for w in IMPERATIVOS if re.search(rf"\b{w}\b", t_minions().lower())], [], t_minions())

    # avisos-v011.md aplicado
    def test_pico(self): self.assertEqual([w for w in IMPERATIVOS if re.search(rf"\b{w}\b", t_pico().lower())], [], t_pico())


class ListaNegra(unittest.TestCase):
    """Ningún aviso usa palabras de la lista negra (hoy ya cumple)."""
    def test_ningun_aviso(self):
        for nombre, f in TEXTOS.items():
            with self.subTest(aviso=nombre):
                t = f().lower()
                self.assertEqual([w for w in PROHIBIDO if w in t], [], f())


if __name__ == "__main__":
    unittest.main()
