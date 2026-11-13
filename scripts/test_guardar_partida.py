"""Al salir de la partida se guarda sola (pedido del usuario, 2026-11-12): sin key o con otra cuenta, desde el cliente."""
import queue, unittest
from unittest import mock

import cliente_v5
import companion_gui as g
import companion_web as w


class GuardarDelCliente(unittest.TestCase):
    def test_reintenta_hasta_que_el_cliente_la_publica(self):
        q = queue.Queue()
        with mock.patch.object(cliente_v5, "descargar", side_effect=[(0, "ya"), (0, "ya"), (1, "1 nueva")]) as d:
            self.assertTrue(g.guardar_del_cliente(q, espera=0, intentos=5, dormir=lambda s: None))
        self.assertEqual(d.call_count, 3)

    def test_se_rinde_y_avisa(self):
        q = queue.Queue()
        with mock.patch.object(cliente_v5, "descargar", return_value=(0, "ya")):
            self.assertFalse(g.guardar_del_cliente(q, espera=0, intentos=3, dormir=lambda s: None))
        msgs = [q.get_nowait()[1] for _ in range(q.qsize())]
        self.assertTrue(any("próxima vez" in m for m in msgs))

    def test_cliente_que_falla_no_truena(self):
        with mock.patch.object(cliente_v5, "descargar", side_effect=[OSError("cerrándose"), (1, "ok")]):
            self.assertTrue(g.guardar_del_cliente(queue.Queue(), espera=0, intentos=3, dormir=lambda s: None))

    def test_post_partida_sin_key_usa_el_cliente(self):
        q = queue.Queue()
        with mock.patch.object(g, "puede_descargar", return_value=False), mock.patch.object(g, "guardar_del_cliente", return_value=True) as gc, \
                mock.patch.object(g, "script", return_value=(0, "")) as sc, mock.patch.object(g, "parsear_revision", return_value={"champ": "Ekko"}), \
                mock.patch.object(g, "ultima_partida", return_value={}):
            g._post_partida(q)
        gc.assert_called_once(); sc.assert_called_once_with("revision.py", "1")  # sin descargar.py; la revisión sí
        self.assertEqual(q.get_nowait()[0], "revision")

    def test_otra_cuenta_tambien_usa_el_cliente(self):
        with mock.patch.object(g, "puede_descargar", return_value=True), mock.patch.object(g, "es_base", return_value=False), \
                mock.patch.object(g, "guardar_del_cliente", return_value=False) as gc, mock.patch.object(g, "script") as sc:
            g._post_partida(queue.Queue())
        gc.assert_called_once(); sc.assert_not_called()  # no corre descargar.py con el Riot ID del dueño

    def test_key_caducada_guarda_desde_el_cliente(self):  # 2026-11-12: RIOT_KEY puesta pero Riot responde 401
        q = queue.Queue()
        with mock.patch.object(g, "puede_descargar", return_value=True), mock.patch.object(g, "es_base", return_value=True),                 mock.patch.object(g.time, "sleep"), mock.patch.object(g, "script", side_effect=[(2, ""), (0, "")]),                 mock.patch.object(g, "guardar_del_cliente", return_value=True) as gc, mock.patch.object(g, "parsear_revision", return_value={"champ": "Zeri"}),                 mock.patch.object(g, "ultima_partida", return_value={}):
            g._post_partida(q)
        gc.assert_called_once()
        tipos = [q.get_nowait()[0] for _ in range(q.qsize())]
        self.assertIn("revision", tipos)

    def test_al_dia_recalcula_si_entra_algo(self):
        with mock.patch.object(cliente_v5, "descargar", return_value=(2, "2 nuevas")), mock.patch.object(w, "refrescar") as r:
            w.al_dia()
        r.assert_called_once()
        with mock.patch.object(cliente_v5, "descargar", return_value=(0, "ya")), mock.patch.object(w, "refrescar") as r:
            w.al_dia()
        r.assert_not_called()


if __name__ == "__main__":
    unittest.main()
