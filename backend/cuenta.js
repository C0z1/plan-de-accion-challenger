// Racha · cuenta en la nube: login con Google y datos de cada usuario en D1 (plan gratis).
// Flujo (plan de DeepSeek): la app abre Google con PKCE y redirect a su servidor local (127.0.0.1); recibe el `code`
// y lo manda aquí con el `verifier`. El Worker lo cambia por el id_token directo con Google (el secreto del cliente
// vive solo aquí) y, si el correo está en GOOGLE_EMAILS, emite una sesión propia de 90 días.

import {correoInvitado, limite} from "./extra.js";

const DIAS90 = 90 * 86400;
const json = (cuerpo, status = 200) => new Response(JSON.stringify(cuerpo), {status, headers: {"content-type": "application/json; charset=utf-8"}});
const ahora = () => Math.floor(Date.now() / 1000);

export async function sha256(texto) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(texto));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}

function tokenNuevo() {
  const b = new Uint8Array(32); crypto.getRandomValues(b);
  return [...b].map(x => x.toString(16).padStart(2, "0")).join("");
}

export function payloadJWT(idToken) {
  // Llegó directo de Google por HTTPS en nuestro propio intercambio: basta revisar aud, iss, exp y el correo.
  const p = String(idToken || "").split(".")[1];
  if (!p) return null;
  try { return JSON.parse(atob(p.replace(/-/g, "+").replace(/_/g, "/"))); } catch { return null; }
}

export function permitido(email, lista) {
  return !!email && (lista || "").split(",").map(x => x.trim().toLowerCase()).filter(Boolean).includes(email.toLowerCase());
}

export async function usuarioDeSesion(request, env) {
  // google_sub de la sesión «Authorization: Bearer <token>» vigente, o null
  const m = (request.headers.get("authorization") || "").match(/^Bearer ([0-9a-f]{64})$/);
  if (!m || !env.DB) return null;
  const fila = await env.DB.prepare("SELECT google_sub, exp FROM sesiones WHERE token_hash = ?").bind(await sha256(m[1])).first();
  return fila && fila.exp > ahora() ? fila.google_sub : null;
}

async function login(request, env) {
  let d; try { d = await request.json(); } catch { return json({error: "cuerpo inválido"}, 400); }
  const {code, verifier, redirect_uri} = d || {};
  if (![code, verifier, redirect_uri].every(x => typeof x === "string" && x.length < 2048)) return json({error: "faltan datos"}, 400);
  if (!/^http:\/\/(127\.0\.0\.1|localhost):\d{2,5}\/oauth$/.test(redirect_uri)) return json({error: "redirect no permitido"}, 400);
  const r = await fetch("https://oauth2.googleapis.com/token", {method: "POST", headers: {"content-type": "application/x-www-form-urlencoded"},
    body: new URLSearchParams({code, code_verifier: verifier, redirect_uri, client_id: env.GOOGLE_CLIENT_ID, client_secret: env.GOOGLE_CLIENT_SECRET, grant_type: "authorization_code"})});
  if (!r.ok) return json({error: "Google no aceptó el inicio de sesión"}, 401);
  const p = payloadJWT((await r.json()).id_token);
  if (!p || p.aud !== env.GOOGLE_CLIENT_ID || !["accounts.google.com", "https://accounts.google.com"].includes(p.iss) || p.exp < ahora() || !p.email_verified)
    return json({error: "identidad de Google inválida"}, 401);
  if (!permitido(p.email, env.GOOGLE_EMAILS) && !await correoInvitado(p.email, env)) return json({error: "Tu correo no está invitado a Racha. Pídele acceso a quien te invitó."}, 403);
  const t = ahora(), token = tokenNuevo();
  await env.DB.prepare("INSERT INTO usuarios (google_sub, email, nombre, creado, ultima) VALUES (?, ?, ?, ?, ?) ON CONFLICT(google_sub) DO UPDATE SET email = excluded.email, nombre = excluded.nombre, ultima = excluded.ultima")
    .bind(p.sub, p.email, p.name || "", t, t).run();
  await env.DB.prepare("INSERT INTO sesiones (token_hash, google_sub, exp) VALUES (?, ?, ?)").bind(await sha256(token), p.sub, t + DIAS90).run();
  return json({token, email: p.email, nombre: p.name || ""});
}

const RIOT_ID = /^[^#]{1,32}#[^#]{1,8}$/;

export async function cuenta(request, env, url) {
  // Rutas /v1/login y /v1/yo…; null si la ruta no es de cuenta (sigue el proxy de Riot)
  const ruta = url.pathname, m = request.method;
  if (ruta === "/v1/login" && m === "POST") {
    if (await limite(env, "login:" + (request.headers.get("cf-connecting-ip") || "?"), 10, 600)) return json({error: "Demasiados intentos: espera unos minutos."}, 429);
    return login(request, env);
  }
  if (ruta === "/v1/config" && m === "GET") return json({google_client_id: env.GOOGLE_CLIENT_ID || null});  // público, como en cualquier app
  if (!ruta.startsWith("/v1/yo")) return null;
  const sub = await usuarioDeSesion(request, env);
  if (!sub) return json({error: "inicia sesión"}, 401);
  const DB = env.DB;
  if (ruta === "/v1/yo" && m === "GET") {
    const u = await DB.prepare("SELECT email, nombre, ajustes, riot_id, region, ultima FROM usuarios WHERE google_sub = ?").bind(sub).first();
    const n = await DB.prepare("SELECT COUNT(*) AS n FROM resumenes WHERE google_sub = ?").bind(sub).first();
    const {results: cs} = await DB.prepare("SELECT riot_id, region FROM cuentas_riot WHERE google_sub = ? ORDER BY creado, rowid").bind(sub).all();
    return json({...u, ajustes: u && u.ajustes ? JSON.parse(u.ajustes) : null, partidas: n ? n.n : 0, cuentas: cs || []});
  }
  let d = null;
  if (m === "PUT" || m === "POST") { try { d = await request.json(); } catch { return json({error: "cuerpo inválido"}, 400); } }
  if (ruta === "/v1/yo/ajustes" && m === "PUT") {
    const s = JSON.stringify(d || {}); if (s.length > 4000) return json({error: "demasiado grande"}, 413);
    await DB.prepare("UPDATE usuarios SET ajustes = ?, ultima = ? WHERE google_sub = ?").bind(s, ahora(), sub).run();
    return json({ok: true});
  }
  if (ruta === "/v1/yo/riot" && m === "PUT") {
    const {riot_id, region} = d || {};
    if (!RIOT_ID.test(riot_id || "") || !/^[a-z0-9]{2,5}$/.test(region || "")) return json({error: "Riot ID o región inválidos"}, 400);
    await DB.prepare("UPDATE usuarios SET riot_id = ?, region = ?, ultima = ? WHERE google_sub = ?").bind(riot_id, region, ahora(), sub).run();
    return json({ok: true});
  }
  if (ruta === "/v1/yo/cuentas" && m === "PUT") {  // vincular la cuenta con sesión en tu cliente de LoL (hasta 5)
    const {riot_id, region} = d || {};
    if (!RIOT_ID.test(riot_id || "") || !/^[a-z0-9]{2,5}$/.test(region || "")) return json({error: "Riot ID o región inválidos"}, 400);
    const ya = await DB.prepare("SELECT COUNT(*) AS n FROM cuentas_riot WHERE google_sub = ? AND riot_id != ?").bind(sub, riot_id).first();
    if (ya && ya.n >= 5) return json({error: "ya tienes 5 cuentas vinculadas"}, 409);
    await DB.prepare("INSERT INTO cuentas_riot (google_sub, riot_id, region, creado, ultima) VALUES (?, ?, ?, ?, ?) ON CONFLICT(google_sub, riot_id) DO UPDATE SET region = excluded.region, ultima = excluded.ultima")
      .bind(sub, riot_id, region, ahora(), ahora()).run();
    const {results} = await DB.prepare("SELECT riot_id, region FROM cuentas_riot WHERE google_sub = ? ORDER BY creado, rowid").bind(sub).all();
    return json({ok: true, cuentas: results || []});
  }
  if (ruta === "/v1/yo/resumenes" && m === "PUT") {
    const fs = Array.isArray(d) ? d.slice(0, 50) : null;
    if (!fs || !fs.every(f => /^[A-Z0-9]{2,5}_\d{1,15}$/.test(f.match_id || "") && JSON.stringify(f.resumen || {}).length < 2000
                         && (f.cuenta == null || RIOT_ID.test(f.cuenta)))) return json({error: "resúmenes inválidos"}, 400);
    await DB.batch(fs.map(f => DB.prepare("INSERT OR REPLACE INTO resumenes (google_sub, match_id, ts, resumen, cuenta) VALUES (?, ?, ?, ?, ?)")
      .bind(sub, f.match_id, f.ts || 0, JSON.stringify(f.resumen), f.cuenta || null)));
    return json({ok: true, n: fs.length});
  }
  if (ruta === "/v1/yo/resumenes" && m === "GET") {
    const {results} = await DB.prepare("SELECT match_id, ts, resumen, cuenta FROM resumenes WHERE google_sub = ? ORDER BY ts DESC LIMIT 500").bind(sub).all();
    return json((results || []).map(r => ({match_id: r.match_id, ts: r.ts, cuenta: r.cuenta, resumen: JSON.parse(r.resumen)})));
  }
  if (ruta === "/v1/yo/salir" && m === "POST") {
    await DB.prepare("DELETE FROM sesiones WHERE token_hash = ?").bind(await sha256(request.headers.get("authorization").slice(7))).run();
    return json({ok: true});
  }
  if (ruta === "/v1/yo" && m === "DELETE") {  // borrar mis datos: usuario, sesiones y resúmenes
    for (const t of ["resumenes", "cuentas_riot", "sesiones", "usuarios"]) await DB.prepare(`DELETE FROM ${t} WHERE google_sub = ?`).bind(sub).run();
    return json({ok: true});
  }
  return json({error: "no existe"}, 404);
}
