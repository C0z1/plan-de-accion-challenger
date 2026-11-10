// node --test backend/  · D1 simulada con node:sqlite (mismo SQL que producción) y Google simulado
import {test} from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {DatabaseSync} from "node:sqlite";
import worker from "./worker.js";
import {permitido, payloadJWT} from "./cuenta.js";

function d1() {  // adaptador mínimo de la API de D1 sobre SQLite en memoria
  const db = new DatabaseSync(":memory:");
  db.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
  return {prepare: sql => ({bind: (...a) => ({
    first: async () => db.prepare(sql).get(...a) ?? null,
    all: async () => ({results: db.prepare(sql).all(...a)}),
    run: async () => db.prepare(sql).run(...a)})})};
}
const jwt = p => "x." + Buffer.from(JSON.stringify(p)).toString("base64url") + ".y";
const ID = {aud: "cliente-racha", iss: "https://accounts.google.com", exp: Math.floor(Date.now() / 1000) + 600, email_verified: true, sub: "g-1", email: "ana@gmail.com", name: "Ana"};
function entorno(idPayload = ID, googleOk = true) {
  globalThis.caches = {default: {match: async () => undefined, put: async () => {}}};
  globalThis.fetch = async (url, opt) => {
    if (String(url).startsWith("https://oauth2.googleapis.com/token")) {
      const b = new URLSearchParams(opt.body);
      assert.equal(b.get("client_secret"), "secreto"); assert.equal(b.get("code_verifier"), "v".repeat(43));
      return new Response(JSON.stringify(googleOk ? {id_token: jwt(idPayload)} : {}), {status: googleOk ? 200 : 400});
    }
    return new Response("{\"riot\":1}", {status: 200});
  };
  return {env: {DB: d1(), GOOGLE_CLIENT_ID: "cliente-racha", GOOGLE_CLIENT_SECRET: "secreto", GOOGLE_EMAILS: "ana@gmail.com, beto@gmail.com", RIOT_KEY: "k", ACCESOS: ""}, ctx: {waitUntil: () => {}}};
}
const req = (path, {method = "GET", body, token} = {}) => new Request("https://racha.test" + path,
  {method, body: body === undefined ? undefined : JSON.stringify(body), headers: {"content-type": "application/json", ...(token ? {authorization: "Bearer " + token} : {})}});
const LOGIN = {code: "c0de", verifier: "v".repeat(43), redirect_uri: "http://127.0.0.1:51234/oauth"};

test("lista de correos y JWT", () => {
  assert.ok(permitido("Ana@Gmail.com", "ana@gmail.com, b@x")); assert.ok(!permitido("eve@x", "ana@gmail.com")); assert.ok(!permitido("", ""));
  assert.equal(payloadJWT(jwt({a: 1})).a, 1); assert.equal(payloadJWT("basura"), null);
});

test("login → sesión → cuenta, Riot ID, ajustes, resúmenes y proxy con sesión", async () => {
  const {env, ctx} = entorno();
  const r = await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx);
  assert.equal(r.status, 200);
  const {token, email} = await r.json(); assert.equal(email, "ana@gmail.com"); assert.match(token, /^[0-9a-f]{64}$/);
  assert.equal((await worker.fetch(req("/v1/yo/riot", {method: "PUT", body: {riot_id: "Ana#LAN", region: "la1"}, token}), env, ctx)).status, 200);
  assert.equal((await worker.fetch(req("/v1/yo/ajustes", {method: "PUT", body: {overlay: false}, token}), env, ctx)).status, 200);
  const rs = [{match_id: "LA1_9", ts: 5, resumen: {campeon: "Ahri", win: true}}];
  assert.equal((await worker.fetch(req("/v1/yo/resumenes", {method: "PUT", body: rs, token}), env, ctx)).status, 200);
  const yo = await (await worker.fetch(req("/v1/yo", {token}), env, ctx)).json();
  assert.deepEqual([yo.riot_id, yo.region, yo.ajustes.overlay, yo.partidas], ["Ana#LAN", "la1", false, 1]);
  const lista = await (await worker.fetch(req("/v1/yo/resumenes", {token}), env, ctx)).json();
  assert.equal(lista[0].resumen.campeon, "Ahri");
  const proxy = await worker.fetch(req("/v1/riot/americas/lol/match/v5/matches/LA1_9", {token}), env, ctx);
  assert.equal(proxy.status, 200);  // la sesión de Google sirve igual que un código
  assert.equal((await worker.fetch(req("/v1/yo/salir", {method: "POST", body: {}, token}), env, ctx)).status, 200);
  assert.equal((await worker.fetch(req("/v1/yo", {token}), env, ctx)).status, 401);  // sesión cerrada
});

test("borrar mis datos", async () => {
  const {env, ctx} = entorno();
  const {token} = await (await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).json();
  await worker.fetch(req("/v1/yo/resumenes", {method: "PUT", body: [{match_id: "LA1_1", resumen: {}}], token}), env, ctx);
  assert.equal((await worker.fetch(req("/v1/yo", {method: "DELETE", token}), env, ctx)).status, 200);
  const {token: t2} = await (await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).json();
  assert.equal((await (await worker.fetch(req("/v1/yo", {token: t2}), env, ctx)).json()).partidas, 0);
});

test("correo no invitado, Google que rechaza, aud ajeno y redirect raro", async () => {
  let e = entorno({...ID, email: "eve@gmail.com"});
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), e.env, e.ctx)).status, 403);
  e = entorno(ID, false);
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), e.env, e.ctx)).status, 401);
  e = entorno({...ID, aud: "otro-cliente"});
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), e.env, e.ctx)).status, 401);
  e = entorno();
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: {...LOGIN, redirect_uri: "https://evil.example/oauth"}}), e.env, e.ctx)).status, 400);
});

test("sin sesión o con datos raros", async () => {
  const {env, ctx} = entorno();
  assert.equal((await worker.fetch(req("/v1/yo"), env, ctx)).status, 401);
  assert.equal((await worker.fetch(req("/v1/yo", {token: "f".repeat(64)}), env, ctx)).status, 401);
  const {token} = await (await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).json();
  assert.equal((await worker.fetch(req("/v1/yo/riot", {method: "PUT", body: {riot_id: "sin-tag", region: "la1"}, token}), env, ctx)).status, 400);
  assert.equal((await worker.fetch(req("/v1/yo/resumenes", {method: "PUT", body: [{match_id: "../x"}], token}), env, ctx)).status, 400);
});

test("config pública con el client_id", async () => {
  const {env, ctx} = entorno();
  assert.equal((await (await worker.fetch(req("/v1/config"), env, ctx)).json()).google_client_id, "cliente-racha");
});
