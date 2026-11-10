"""Pruebas de DeepSeek para los avisos como dict {texto, tipo, minuto} (turno 5, iteración 6). Sin red ni ventana.

Cubre los 3 bordes que pidió Opus: `_post_partida` con key caducada → aviso `error` con «RIOT_KEY»,
`aviso_minions` disparado en el trabajador a 630 s → `minuto == 10` y `tipo == "consejo"`, y
`builds.informe` con `mejores` lanzando HTTPError 429 → «sin datos» y no truena."""
import json, pathlib, queue, sys, tempfile, unittest
import urllib.error

AQUI = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import builds  # noqa: E402
import companion_gui as g  # noqa: E402


class AvisoDict(unittest.TestCase):
    def test_post_partida_key_caducada_es_aviso_error(self):
        q = queue.Queue()
        orig = g.script, g.time.sleep, g.puede_descargar
        g.script, g.time.sleep, g.puede_descargar = (lambda *a: (2, "")), (lambda s: None), (lambda: True)
        try:
            g._post_partida(q)
        finally:
            g.script, g.time.sleep, g.puede_descargar = orig
        avisos = [e[1] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(len(avisos), 1)
        self.assertEqual((avisos[0]["tipo"], avisos[0]["minuto"]), ("error", None))
        self.assertIn("RIOT_KEY", avisos[0]["texto"])

    def test_post_partida_sin_key_no_descarga_ni_avisa(self):  # beta para amigos sin key
        q, corridos = queue.Queue(), []
        orig = g.script, g.puede_descargar
        g.script, g.puede_descargar = (lambda *a: corridos.append(a) or (0, "")), (lambda: False)
        try:
            g._post_partida(q)
        finally:
            g.script, g.puede_descargar = orig
        self.assertEqual((corridos, list(q.queue)), ([], []))

    def test_recomendaciones_sin_partidas_no_truena(self):  # amigo sin historial en su primer champ select
        import os, subprocess, sys, tempfile
        with tempfile.TemporaryDirectory() as vacio:
            env = dict(os.environ, DATOS_DIR=vacio)
            codigo = "import companion_gui as g; print(g.recomendaciones('MIDDLE', ['Ahri']))"
            r = subprocess.run([sys.executable, "-c", codigo], cwd=os.path.dirname(os.path.abspath(__file__)), env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("[('Ahri', None)]", r.stdout)

    def test_minions_en_trabajador_a_630s_da_minuto_10(self):
        c = g.companion
        d = json.loads((AQUI / "fixtures" / "vivo" / "allgamedata.json").read_text(encoding="utf-8"))
        d["gameData"]["gameTime"] = 630
        d["allPlayers"][0]["scores"]["creepScore"] = 60  # Ekko, meta 69
        orig = c.lcu, c.vivo, c.capturar, c.CFG, g.time.sleep, g.time.time
        with tempfile.TemporaryDirectory() as tmp:
            cfg = pathlib.Path(tmp, "config.json")
            cfg.write_text(json.dumps({"minions10": {"campeon": "Ekko", "minimo": 69}}), encoding="utf-8")
            vueltas = iter(range(3))
            def dormir(_):
                if next(vueltas, None) is None: raise KeyboardInterrupt
            reloj = iter(range(0, 10_000, 100))
            c.lcu, c.vivo, c.capturar, c.CFG = (lambda path: "InProgress"), (lambda: d), (lambda a, f: a), cfg
            g.time.sleep, g.time.time = dormir, (lambda: next(reloj))
            q = queue.Queue()
            try:
                with self.assertRaises(KeyboardInterrupt): g.trabajador(q)
            finally:
                c.lcu, c.vivo, c.capturar, c.CFG, g.time.sleep, g.time.time = orig
        avisos = [e[1] for e in list(q.queue) if e[0] == "aviso"]
        self.assertEqual(len(avisos), 1)  # aviso_nivel no salta a los 630 s
        self.assertEqual((avisos[0]["tipo"], avisos[0]["minuto"]), ("consejo", 10))
        self.assertIn("60 de CS", avisos[0]["texto"])

    def test_informe_429_sin_datos_no_truena(self):
        items = {"3153": dict(name="Espada del Rey Arruinado", tags=[])}
        champs = {"yone": ("Yone", 777)}
        orig = builds.ddragon, builds.mejores, builds.tuyas
        def _429(*a, **k): raise urllib.error.HTTPError("url", 429, "Too Many Requests", {}, None)
        builds.ddragon, builds.mejores, builds.tuyas = (lambda: (items, {}, champs)), _429, (lambda *a: [])
        try:
            txt, rt, tu = builds.informe("Yone", "MIDDLE")
        finally:
            builds.ddragon, builds.mejores, builds.tuyas = orig
        self.assertIn("sin datos", txt)
        self.assertIsNone(rt)
        self.assertIn("Tú: sin partidas", txt)  # sigue con tu parte


if __name__ == "__main__":
    unittest.main()
