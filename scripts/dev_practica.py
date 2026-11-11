"""Solo desarrollo (no va en el .exe): abre una Herramienta de práctica para probar Racha en una partida real.
  python scripts/dev_practica.py [campeónId, 245 = Ekko] [--seco]   lobby → selección → elige y confirma → espera InProgress
  python scripts/dev_practica.py salir                              termina la partida de práctica
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
    w = (lambda m, p, b=None: print("seco:", m, p) or True) if seco else escribir
    if args == ["salir"]:  # solo una partida de práctica: en una partida real early-exit sería abandonar
        modo = (((lcu("/lol-gameflow/v1/session") or {}).get("gameData") or {}).get("queue") or {}).get("gameMode")
        if modo != "PRACTICETOOL": print("no salgo: la partida es", modo); return False
        return w("POST", "/lol-gameflow/v1/early-exit")
    champ = int(args[0]) if args else 245
    fase = lcu("/lol-gameflow/v1/gameflow-phase"); print("fase", fase)
    if not puede(fase): print("no toco nada en fase", fase); return False
    lobby = lcu("/lol-lobby/v2/lobby")
    if not (lobby and lobby.get("gameConfig", {}).get("gameMode") == "PRACTICETOOL") and not w("POST", "/lol-lobby/v2/lobby", LOBBY):
        print("no se pudo crear el lobby"); return False
    if not w("POST", "/lol-lobby/v1/lobby/custom/start-champ-select"): print("no arrancó la selección"); return False
    if seco: return True
    for _ in range(60):
        dormir(2); s = lcu("/lol-champ-select/v1/session")
        for a in (a for g in (s or {}).get("actions", []) for a in g):
            if a["actorCellId"] == s["localPlayerCellId"] and a["type"] == "pick" and not a["completed"]:
                print("pick", w("PATCH", f"/lol-champ-select/v1/session/actions/{a['id']}", {"championId": champ, "completed": True}))
        fase = lcu("/lol-gameflow/v1/gameflow-phase")
        if fase in ("GameStart", "InProgress"): print("fase", fase); return True
    print("se acabó la espera en fase", fase); return False


if __name__ == "__main__": sys.exit(0 if main(sys.argv[1:]) else 1)
