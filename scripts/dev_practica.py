"""Solo desarrollo (no va en el .exe): abre una Herramienta de práctica para probar Racha en una partida real.
  python scripts/dev_practica.py [campeónId, 245 = Ekko] [--seco] [--espera N]   lobby → selección (N s antes de elegir) → elige y confirma → espera InProgress
  python scripts/dev_practica.py salir                              termina la partida de práctica
  python scripts/dev_practica.py reconectar                         vuelve a la partida de práctica (prueba de Reconnect)
Nunca toca colas ranked/normales ni el ready-check: se niega fuera de las fases None/Lobby."""
import sys, time
sys.path.insert(0, __import__("os").path.dirname(__file__))
import companion as c

LOBBY = {"customGameLobby": {"configuration": {"gameMode": "PRACTICETOOL", "gameMutator": "", "gameServerRegion": "", "mapId": 11,
         "mutators": {"id": 1}, "spectatorPolicy": "AllAllowed", "teamSize": 1}, "lobbyName": "Racha prueba", "lobbyPassword": ""},
         "isCustom": True, "queueId": 3140}  # sin queueId 3140 y teamSize 1 el cliente responde INVALID_LOBBY (LA1, 2026-11-11)


def puede(fase): return fase in ("None", "Lobby")  # nunca interrumpir una cola, un ready-check ni una partida


def main(args, lcu=c.lcu, escribir=c.lcu_escribir, dormir=time.sleep):
    seco = "--seco" in args; args = [a for a in args if a != "--seco"]
    espera = 0
    if "--espera" in args: i = args.index("--espera"); espera = int(args[i + 1]); del args[i:i + 2]  # para capturar las vistas en la selección
    w = (lambda m, p, b=None: print("seco:", m, p) or True) if seco else escribir
    if args in (["salir"], ["reconectar"]):  # solo una partida de práctica: en una partida real early-exit sería abandonar
        s = lcu("/lol-gameflow/v1/session") or {}
        modo, fase = ((s.get("gameData") or {}).get("queue") or {}).get("gameMode"), s.get("phase")
        if modo != "PRACTICETOOL": print("no toco la partida: es", modo); return False
        if fase not in ("InProgress", "Reconnect"): print("no toco nada en fase", fase); return False
        return w("POST", "/lol-gameflow/v1/early-exit" if args == ["salir"] else "/lol-gameflow/v1/reconnect")
    champ = int(args[0]) if args else 245
    fase = lcu("/lol-gameflow/v1/gameflow-phase"); print("fase", fase)
    if not puede(fase): print("no toco nada en fase", fase); return False
    lobby = lcu("/lol-lobby/v2/lobby")
    if not (lobby and lobby.get("gameConfig", {}).get("gameMode") == "PRACTICETOOL") and not w("POST", "/lol-lobby/v2/lobby", LOBBY):
        print("no se pudo crear el lobby"); return False
    if not w("POST", "/lol-lobby/v1/lobby/custom/start-champ-select"): print("no arrancó la selección"); return False
    if seco: return True
    if espera: dormir(espera)
    for _ in range(60):
        dormir(2); s = lcu("/lol-champ-select/v1/session")
        for a in (a for g in (s or {}).get("actions", []) for a in g):
            if a["actorCellId"] == s["localPlayerCellId"] and a["type"] == "pick" and not a["completed"]:
                print("pick", w("PATCH", f"/lol-champ-select/v1/session/actions/{a['id']}", {"championId": champ, "completed": True}))
        fase = lcu("/lol-gameflow/v1/gameflow-phase")
        if fase in ("GameStart", "InProgress"): print("fase", fase); return True
    print("se acabó la espera en fase", fase); return False


if __name__ == "__main__": sys.exit(0 if main(sys.argv[1:]) else 1)
