"""Pruebas de DeepSeek para score.py (turno 5, iteración 5). Sin red: el duelo de línea (`de` → `linea`) y
`score.resumen` con cero partidas.

Cubre los 3 bordes que pidió Opus: empate exacto de score con el rival (lo pierdes), dos `teamPosition`
vacíos (no empareja vacíos) y `resumen` sobre una carpeta con `perfil.json` y ninguna partida."""
import json, pathlib, sys, tempfile, unittest

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import score  # noqa: E402

Z = {c: 0.0 for c in score.COMP}


class Duelo(unittest.TestCase):
    def test_empate_con_el_rival_lo_pierdes(self):
        # mismo z para ambos (sin medias de rol): score 50 los dos → 50 > 50 es falso → linea 2
        zs = [("yo", "MIDDLE", 100, True, dict(Z)), ("rival", "MIDDLE", 200, False, dict(Z))]
        r = score.de(zs, "yo", {})
        self.assertEqual((r["score"], r["puesto"]), (50, 1))
        self.assertEqual(r["linea"], 2)

    def test_posicion_vacia_no_empareja_con_otro_vacio(self):
        # dos con teamPosition "" en equipos distintos: sin rol no se sabe el rival → linea None
        zs = [("yo", "", 100, True, dict(Z)), ("rival", "", 200, False, dict(Z))]
        r = score.de(zs, "yo", {})
        self.assertIsNone(r["linea"])

    def test_resumen_sin_partidas_no_truena(self):
        with tempfile.TemporaryDirectory() as tmp:
            pathlib.Path(tmp, "perfil.json").write_text(json.dumps({"account": {"puuid": "yo"}}), encoding="utf-8")
            r = score.resumen(3, tmp)
        self.assertEqual(r["partidas"], [])
        self.assertIsNone(r["media"]); self.assertIsNone(r["ultimas20"]); self.assertIsNone(r["anteriores"])
        self.assertEqual(r["ref"], 50)


if __name__ == "__main__":
    unittest.main()
