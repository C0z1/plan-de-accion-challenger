"""Descarga partidas de Solo/Duo de Riot API a datos/raw/. Uso: RIOT_KEY=... python scripts/descargar.py [N]"""
import json, os, sys, time, urllib.request, urllib.error, pathlib

KEY = os.environ["RIOT_KEY"]  # nunca commitear la key
NAME, TAG = "cozi", "1134"
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100
RAW = pathlib.Path(__file__).resolve().parent.parent / "datos" / "raw"
RAW.mkdir(parents=True, exist_ok=True)


def get(url):
    while True:
        req = urllib.request.Request(url, headers={"X-Riot-Token": KEY, "User-Agent": "plan-challenger"})  # Riot 403 al UA de urllib
        try:
            with urllib.request.urlopen(req) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:  # rate limit de dev key: esperar lo que pida Riot
                time.sleep(int(e.headers.get("Retry-After", 10)))
                continue
            raise


acc = get(f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{NAME}/{TAG}")
puuid = acc["puuid"]
league = get(f"https://la1.api.riotgames.com/lol/league/v4/entries/by-puuid/{puuid}")
(RAW / "perfil.json").write_text(json.dumps({"account": acc, "league": league}, indent=1))

ids = []
for start in range(0, N, 100):
    ids += get(f"https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
               f"?queue=420&start={start}&count={min(100, N - start)}")

TL = RAW / "timeline"
TL.mkdir(exist_ok=True)
for i, mid in enumerate(ids):
    base = f"https://americas.api.riotgames.com/lol/match/v5/matches/{mid}"
    for f, url in ((RAW / f"{mid}.json", base), (TL / f"{mid}.json", base + "/timeline")):
        if not f.exists():
            f.write_text(json.dumps(get(url)))
    print(f"{i + 1}/{len(ids)}", end="\r")
print(f"\nlisto: {len(ids)} partidas")
