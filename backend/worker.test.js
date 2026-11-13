// node --test backend/  (sin red: fetch y caches simulados)
import {test} from "node:test";
import assert from "node:assert/strict";
import worker, {destino, quienEs} from "./worker.js";

const ACCESOS = "ana:abc12345,beto:zzz99999";
function entorno(respuesta = {status: 200, body: "{\"ok\":1}"}) {
  const guardado = new Map(), llamadas = [];
  globalThis.caches = {default: {match: async r => guardado.get(r.url), put: async (r, res) => guardado.set(r.url, res)}};
  globalThis.fetch = async (url, opt) => { llamadas.push([url, opt]); return new Response(respuesta.body, {status: respuesta.status, headers: respuesta.headers || {}}); };
  return {env: {RIOT_KEY: "RGAPI-x", ACCESOS}, ctx: {waitUntil: p => p}, llamadas, guardado};
}
const pedir = (path, token = "abc12345") => new Request("https://racha.test" + path, {headers: token ? {"x-racha-token": token} : {}});

test("código de acceso", () => {
  assert.equal(quienEs("abc12345", ACCESOS), "ana");
  assert.equal(quienEs("zzz99999", ACCESOS), "beto");
  assert.equal(quienEs("abc1234", ACCESOS), null);
  assert.equal(quienEs("", ACCESOS), null);
  assert.equal(quienEs("abc12345", ""), null);
});

test("solo las consultas de la app", () => {
  const d = p => destino(new URL("https://racha.test" + p));
  assert.equal(d("/v1/riot/la1/lol/league/v4/entries/by-puuid/abc")[0], "https://la1.api.riotgames.com/lol/league/v4/entries/by-puuid/abc");
  assert.equal(d("/v1/riot/americas/lol/match/v5/matches/LA1_1/timeline")[1], 30 * 86400);
  assert.equal(d("/v1/riot/americas/lol/match/v5/matches/by-puuid/p/ids?start=0&count=100&queue=420")[0],
    "https://americas.api.riotgames.com/lol/match/v5/matches/by-puuid/p/ids?start=0&count=100&queue=420");
  assert.ok(d("/v1/riot/americas/riot/account/v1/accounts/by-riot-id/cozi/1134"));
  assert.equal(d("/v1/riot/la1/lol/spectator/v5/active-games/by-summoner/abc")[0], "https://la1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/abc");
  assert.equal(d("/v1/riot/americas/lol/spectator/v5/active-games/by-summoner/abc"), null);  // spectator va por plataforma
  assert.equal(d("/v1/riot/la1/lol/match/v5/matches/LA1_1"), null);          // match en host de plataforma
  assert.equal(d("/v1/riot/americas/lol/summoner/v4/summoners/x"), null);    // no permitida
  assert.equal(d("/v1/riot/evil.com/lol/match/v5/matches/LA1_1"), null);     // host inventado
  assert.equal(d("/v1/riot/americas/lol/match/v5/matches/by-puuid/p/ids?api_key=x"), null);
});

test("sin código: 401 y no llama a Riot", async () => {
  const e = entorno();
  const r = await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_1", null), e.env, e.ctx);
  assert.equal(r.status, 401); assert.equal(e.llamadas.length, 0);
});

test("con código: pasa la key del servidor y cachea la partida", async () => {
  const e = entorno();
  const r = await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_1"), e.env, e.ctx);
  assert.equal(r.status, 200); assert.equal(e.llamadas[0][1].headers["X-Riot-Token"], "RGAPI-x");
  await new Promise(r => setTimeout(r, 0));
  const r2 = await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_1"), e.env, e.ctx);
  assert.equal(r2.headers.get("x-racha-cache"), "hit"); assert.equal(e.llamadas.length, 1);
});

test("límite de Riot y key caducada", async () => {
  let e = entorno({status: 429, body: "{}", headers: {"retry-after": "7"}});
  let r = await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_1"), e.env, e.ctx);
  assert.equal(r.status, 429); assert.equal(r.headers.get("retry-after"), "7");
  e = entorno({status: 403, body: "{}"});
  r = await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_1"), e.env, e.ctx);
  assert.equal(r.status, 503);
});

test("salud sin código y solo GET", async () => {
  const e = entorno();
  assert.equal((await worker.fetch(pedir("/v1/salud", null), e.env, e.ctx)).status, 200);
  const post = new Request("https://racha.test/v1/salud", {method: "POST"});
  assert.equal((await worker.fetch(post, e.env, e.ctx)).status, 405);
});

test("la key del secreto se limpia (un salto de línea de la terminal no la rompe)", async () => {
  const e = entorno(); e.env.RIOT_KEY = "RGAPI-x" + String.fromCharCode(13, 10);
  await worker.fetch(pedir("/v1/riot/americas/lol/match/v5/matches/LA1_2"), e.env, e.ctx);
  assert.equal(e.llamadas[0][1].headers["X-Riot-Token"], "RGAPI-x");
});
