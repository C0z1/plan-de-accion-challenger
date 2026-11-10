// Racha · backend mínimo (Cloudflare Workers, plan gratis): proxy de solo lectura a la Riot API.
// - La key de Riot vive como secreto del Worker (RIOT_KEY); nunca va en el .exe ni en el repo.
// - Solo entra quien trae un código de acceso válido (secreto ACCESOS = «nombre:código,nombre:código»): comunidad
//   pequeña y privada, como pide Riot para una Personal API Key.
// - Solo deja pasar las 4 consultas que usa la app (cuenta, ids de partidas, partida/timeline, liga).
// - Las partidas y timelines no cambian: se guardan en la caché del borde y casi no gastan key.

import {cuenta, usuarioDeSesion} from "./cuenta.js";

const RUTEO = new Set(["americas", "europe", "asia", "sea"]);
const PLATAFORMAS = new Set(["na1", "la1", "la2", "br1", "euw1", "eun1", "tr1", "ru", "me1", "kr", "jp1", "oc1", "sg2", "tw2", "vn2"]);
const ID = "[A-Za-z0-9_-]{1,100}", NOMBRE = "[^/?#]{1,64}";
// [patrón del path, tipo de host, segundos de caché]
const PERMITIDO = [
  [new RegExp(`^/riot/account/v1/accounts/by-riot-id/${NOMBRE}/${NOMBRE}$`), RUTEO, 3600],
  [new RegExp(`^/lol/match/v5/matches/by-puuid/${ID}/ids$`), RUTEO, 60],
  [new RegExp(`^/lol/match/v5/matches/${ID}(/timeline)?$`), RUTEO, 30 * 86400],  // inmutables
  [new RegExp(`^/lol/league/v4/entries/by-puuid/${ID}$`), PLATAFORMAS, 300],
];
const PARAMS = new Set(["start", "count", "queue", "type", "startTime", "endTime"]);

const json = (cuerpo, status = 200, extra = {}) =>
  new Response(JSON.stringify(cuerpo), {status, headers: {"content-type": "application/json; charset=utf-8", ...extra}});

export function quienEs(token, accesos) {
  // nombre del amigo dueño del código, o null; comparación en tiempo constante por código
  if (!token || !accesos) return null;
  for (const par of accesos.split(",")) {
    const [nombre, codigo] = par.split(":").map(x => (x || "").trim());
    if (!codigo || codigo.length !== token.length) continue;
    let d = 0;
    for (let i = 0; i < codigo.length; i++) d |= codigo.charCodeAt(i) ^ token.charCodeAt(i);
    if (d === 0) return nombre || "amigo";
  }
  return null;
}

export function destino(url) {
  // /v1/riot/<host>/<path>?q → [url de Riot, segundos de caché] o null si no está permitido
  const m = url.pathname.match(/^\/v1\/riot\/([a-z0-9]{2,8})(\/.+)$/);
  if (!m) return null;
  const [, host, path] = m;
  const regla = PERMITIDO.find(([re]) => re.test(path));
  if (!regla || !regla[1].has(host)) return null;
  const q = new URLSearchParams();
  for (const [k, v] of url.searchParams) {
    if (!PARAMS.has(k) || !/^[0-9A-Za-z_]{1,20}$/.test(v)) return null;
    q.set(k, v);
  }
  const qs = q.toString();
  return [`https://${host}.api.riotgames.com${path}${qs ? "?" + qs : ""}`, regla[2]];
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const c = await cuenta(request, env, url);  // /v1/login y /v1/yo… (cuenta en la nube)
    if (c) return c;
    if (request.method !== "GET") return json({error: "solo GET"}, 405);
    if (url.pathname === "/v1/salud") return json({ok: true, version: 1});
    const quien = quienEs(request.headers.get("x-racha-token"), env.ACCESOS) || await usuarioDeSesion(request, env);  // código o sesión de Google
    if (!quien) return json({error: "código de acceso inválido"}, 401);
    const d = destino(url);
    if (!d) return json({error: "consulta no permitida"}, 404);
    const [riot, ttl] = d;
    const cache = caches.default, clave = new Request(riot);
    let r = await cache.match(clave);
    if (r) return new Response(r.body, {status: r.status, headers: {"content-type": "application/json; charset=utf-8", "x-racha-cache": "hit"}});
    const res = await fetch(riot, {headers: {"X-Riot-Token": (env.RIOT_KEY || "").trim(), "User-Agent": "racha.gg"}});
    const cuerpo = await res.text();
    if (res.status === 429) return json({error: "límite de Riot"}, 429, {"retry-after": res.headers.get("retry-after") || "10"});
    if (res.status === 401 || res.status === 403) return json({error: "la key del servidor caducó"}, 503);  // no culpar al amigo
    const out = new Response(cuerpo, {status: res.status, headers: {"content-type": "application/json; charset=utf-8", "cache-control": `public, max-age=${ttl}`}});
    if (res.ok) ctx.waitUntil(cache.put(clave, out.clone()));
    return out;
  },
};
