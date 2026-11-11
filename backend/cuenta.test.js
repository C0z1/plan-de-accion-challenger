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

// v0.8: builds compartidas, invitados, reportes y métricas (extra.js)
const conCodigo = (path, codigo, opt = {}) => { const r = req(path, opt); r.headers.set("x-racha-token", codigo); return r; };

test("admin sube builds y un invitado las lee; un no-admin no puede subir", async () => {
  const {env, ctx} = entorno(); env.ACCESOS = "cozi:codigo-admin1,beto:codigo-beto1"; env.ADMINS = "cozi";
  const builds = {"Ahri|MIDDLE": {items: [1, 2], jugadores: ["X#KR"]}};
  assert.equal((await worker.fetch(conCodigo("/v1/builds", "codigo-beto1", {method: "PUT", body: builds}), env, ctx)).status, 403);
  assert.equal((await worker.fetch(conCodigo("/v1/builds", "codigo-admin1", {method: "PUT", body: {"../x": {}}}), env, ctx)).status, 400);
  assert.equal((await worker.fetch(conCodigo("/v1/builds", "codigo-admin1", {method: "PUT", body: builds}), env, ctx)).status, 200);
  const b = await (await worker.fetch(conCodigo("/v1/builds/" + encodeURIComponent("Ahri|MIDDLE"), "codigo-beto1"), env, ctx)).json();
  assert.deepEqual(b.datos.items, [1, 2]);
  assert.equal((await (await worker.fetch(conCodigo("/v1/builds", "codigo-beto1"), env, ctx)).json())[0].clave, "Ahri|MIDDLE");
  assert.equal((await worker.fetch(conCodigo("/v1/builds/" + encodeURIComponent("Zed|MIDDLE"), "codigo-beto1"), env, ctx)).status, 404);
  assert.equal((await worker.fetch(req("/v1/builds"), env, ctx)).status, 401);
});

test("invitar por correo: el código nuevo entra al proxy y el correo puede iniciar sesión", async () => {
  const {env, ctx} = entorno({...ID, email: "carla@gmail.com", sub: "g-2"}); env.ACCESOS = "cozi:codigo-admin1"; env.ADMINS = "cozi";
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).status, 403);  // aún no invitada
  const inv = await (await worker.fetch(conCodigo("/v1/admin/invitados", "codigo-admin1", {method: "POST", body: {nombre: "Carla", email: "Carla@Gmail.com"}}), env, ctx)).json();
  assert.equal(inv.nombre, "carla"); assert.match(inv.codigo, /^[0-9a-f]{24}$/);
  assert.equal((await worker.fetch(conCodigo("/v1/admin/invitados", "codigo-admin1", {method: "POST", body: {nombre: "carla"}}), env, ctx)).status, 409);
  assert.equal((await worker.fetch(conCodigo("/v1/riot/americas/lol/match/v5/matches/LA1_9", inv.codigo), env, ctx)).status, 200);
  assert.equal((await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).status, 200);  // ya invitada
  const ls = await (await worker.fetch(conCodigo("/v1/admin/invitados", "codigo-admin1"), env, ctx)).json();
  assert.equal(ls[0].codigo, undefined);  // el código no se vuelve a mostrar
  assert.equal((await worker.fetch(conCodigo("/v1/admin/invitados", inv.codigo), env, ctx)).status, 403);  // el invitado no es admin
  await worker.fetch(conCodigo("/v1/admin/invitados/carla", "codigo-admin1", {method: "DELETE"}), env, ctx);
  assert.equal((await worker.fetch(conCodigo("/v1/riot/americas/lol/match/v5/matches/LA1_9", inv.codigo), env, ctx)).status, 401);
});

test("reportes privados y métricas anónimas: solo el admin los lee", async () => {
  const {env, ctx} = entorno(); env.ACCESOS = "cozi:codigo-admin1,beto:codigo-beto1"; env.ADMINS = "cozi";
  assert.equal((await worker.fetch(conCodigo("/v1/reporte", "codigo-beto1", {method: "POST", body: {texto: ""}}), env, ctx)).status, 400);
  assert.equal((await worker.fetch(conCodigo("/v1/reporte", "codigo-beto1", {method: "POST", body: {texto: "no carga", version: "0.8.0", vista: "partidas"}}), env, ctx)).status, 200);
  for (const o of [true, false]) await worker.fetch(conCodigo("/v1/ping", "codigo-beto1", {method: "POST", body: {version: "0.8.0", region: "la1", overlay: o}}), env, ctx);
  assert.equal((await worker.fetch(conCodigo("/v1/admin/reportes", "codigo-beto1"), env, ctx)).status, 403);
  const rep = await (await worker.fetch(conCodigo("/v1/admin/reportes", "codigo-admin1"), env, ctx)).json();
  assert.equal(rep[0].texto, "no carga"); assert.ok(!JSON.stringify(rep).includes("beto"));  // no guarda quién
  const met = await (await worker.fetch(conCodigo("/v1/admin/metricas", "codigo-admin1"), env, ctx)).json();
  assert.deepEqual([met[0].usos, met[0].overlay, met[0].region], [2, 1, "la1"]);
});

test("seguridad v0.8: cuerpo enorme, URL rota, invitado con nombre de admin y códigos de otra longitud", async () => {
  const {env, ctx} = entorno(); env.ACCESOS = "cozi:codigo-admin1"; env.ADMINS = "cozi,carla";
  const grande = new Request("https://racha.test/v1/reporte", {method: "POST", body: "x", headers: {"content-length": "999999", "x-racha-token": "codigo-admin1"}});
  assert.equal((await worker.fetch(grande, env, ctx)).status, 413);
  assert.equal((await worker.fetch(conCodigo("/v1/builds/%E0%A4%A", "codigo-admin1"), env, ctx)).status, 404);
  const inv = await (await worker.fetch(conCodigo("/v1/admin/invitados", "codigo-admin1", {method: "POST", body: {nombre: "carla"}}), env, ctx)).json();
  assert.equal((await worker.fetch(conCodigo("/v1/admin/invitados", inv.codigo), env, ctx)).status, 403);  // se llama como un admin, pero no lo es
  assert.equal((await worker.fetch(conCodigo("/v1/riot/americas/lol/match/v5/matches/LA1_9", "codigo-admin"), env, ctx)).status, 401);  // prefijo de un código
  assert.equal((await worker.fetch(conCodigo("/v1/riot/americas/lol/match/v5/matches/LA1_9", "codigo-admin12"), env, ctx)).status, 401);
});

test("límites: login por IP, reportes y ping por usuario; correo inválido al invitar", async () => {
  const {env, ctx} = entorno({...ID, email: "eve@gmail.com"}); env.ACCESOS = "cozi:codigo-admin1,beto:codigo-beto1"; env.ADMINS = "cozi";
  const login = () => { const r = req("/v1/login", {method: "POST", body: LOGIN}); r.headers.set("cf-connecting-ip", "1.2.3.4"); return worker.fetch(r, env, ctx); };
  for (let i = 0; i < 10; i++) assert.equal((await login()).status, 403);  // no invitada, pero cuenta como intento
  assert.equal((await login()).status, 429);
  for (let i = 0; i < 10; i++) assert.equal((await worker.fetch(conCodigo("/v1/reporte", "codigo-beto1", {method: "POST", body: {texto: "x" + i}}), env, ctx)).status, 200);
  assert.equal((await worker.fetch(conCodigo("/v1/reporte", "codigo-beto1", {method: "POST", body: {texto: "otro"}}), env, ctx)).status, 429);
  assert.equal((await worker.fetch(conCodigo("/v1/reporte", "codigo-admin1", {method: "POST", body: {texto: "de otro"}}), env, ctx)).status, 200);  // el límite es por usuario
  for (let i = 0; i < 5; i++) await worker.fetch(conCodigo("/v1/ping", "codigo-beto1", {method: "POST", body: {version: "0.9.0", region: "la1"}}), env, ctx);
  const met = await (await worker.fetch(conCodigo("/v1/admin/metricas", "codigo-admin1"), env, ctx)).json();
  assert.equal(met[0].usos, 3);  // los pings de más se ignoran sin error
  for (const email of ["a@b", "sin-arroba", "x@y.c"]) assert.equal((await worker.fetch(conCodigo("/v1/admin/invitados", "codigo-admin1", {method: "POST", body: {nombre: "z" + email.length, email}}), env, ctx)).status, 400);
});

test("tabla del grupo: solo quien la activó, con su récord de 7 días y de sus últimas 20", async () => {
  const {env, ctx} = entorno(); env.ACCESOS = "beto:codigo-beto1";
  const {token} = await (await worker.fetch(req("/v1/login", {method: "POST", body: LOGIN}), env, ctx)).json();
  await worker.fetch(req("/v1/yo/riot", {method: "PUT", body: {riot_id: "Ana#LAN", region: "la1"}, token}), env, ctx);
  const ahora = Date.now(), viejo = ahora - 10 * 864e5;
  await worker.fetch(req("/v1/yo/resumenes", {method: "PUT", body: [{match_id: "LA1_1", ts: ahora, resumen: {win: true, score: 60}}, {match_id: "LA1_2", ts: viejo, resumen: {win: false, score: 40}}], token}), env, ctx);
  assert.deepEqual(await (await worker.fetch(conCodigo("/v1/grupo", "codigo-beto1"), env, ctx)).json(), []);  // aún no la activa
  await worker.fetch(req("/v1/yo/ajustes", {method: "PUT", body: {grupo: true}, token}), env, ctx);
  const g = await (await worker.fetch(conCodigo("/v1/grupo", "codigo-beto1"), env, ctx)).json();
  assert.deepEqual(g, [{riot_id: "Ana#LAN", yo: false, semana: [1, 1], ultimas: [1, 2], score: 50}]);
  assert.equal((await (await worker.fetch(req("/v1/grupo", {token}), env, ctx)).json())[0].yo, true);
  assert.ok(!JSON.stringify(g).includes("gmail"));  // nunca el correo
  assert.equal((await worker.fetch(req("/v1/grupo"), env, ctx)).status, 401);
});
