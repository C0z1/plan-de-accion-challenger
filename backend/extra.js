// Racha · v0.8 (todo gratis, D1): builds compartidas, invitaciones, reportes privados y métricas anónimas.
// Admin = quien entra con un código cuyo nombre, o una sesión de Google cuyo correo, está en el secreto ADMINS.

import {usuarioDeSesion, sha256} from "./cuenta.js";

const json = (cuerpo, status = 200) => new Response(JSON.stringify(cuerpo), {status, headers: {"content-type": "application/json; charset=utf-8"}});
const ahora = () => Math.floor(Date.now() / 1000);
const lista = s => (s || "").split(",").map(x => x.trim().toLowerCase()).filter(Boolean);
const CLAVE = /^[A-Za-z' .&]{2,30}\|[A-Z]{3,7}$/;  // «Campeón|POSICIÓN»
const NOMBRE = /^[a-z0-9_-]{2,24}$/;
const EMAIL = /^[a-z0-9._%+-]{1,64}@[a-z0-9-]{1,63}(\.[a-z0-9-]{1,63})*\.[a-z]{2,24}$/;  // con dominio y TLD: «a@b» no pasa

export async function limite(env, clave, max, segundos) {
  // true si `clave` ya pasó de `max` usos en la ventana actual de `segundos`; cuenta este uso
  if (!env.DB) return false;
  const ventana = Math.floor(Date.now() / 1000 / segundos) * segundos;
  const f = await env.DB.prepare("INSERT INTO limites (clave, ventana, n) VALUES (?, ?, 1) ON CONFLICT(clave, ventana) DO UPDATE SET n = n + 1 RETURNING n")
    .bind(clave, ventana).first();
  if (Math.random() < .02) await env.DB.prepare("DELETE FROM limites WHERE ventana < ?").bind(ventana - 86400).run();  // limpieza ocasional
  return !!f && f.n > max;
}

export async function codigoInvitado(token, env) {
  // nombre del invitado (D1) dueño de este código, o null
  if (!token || !env.DB || !/^[A-Za-z0-9_-]{6,64}$/.test(token)) return null;
  const f = await env.DB.prepare("SELECT nombre FROM invitados WHERE codigo = ?").bind(token).first();
  return f ? f.nombre : null;
}

export async function correoInvitado(email, env) {
  if (!email || !env.DB) return false;
  return !!await env.DB.prepare("SELECT 1 AS si FROM invitados WHERE lower(email) = lower(?)").bind(email).first();
}

async function quien(request, env, quienEs) {
  // {id, admin} de quien llama (código de ACCESOS, código de D1 o sesión de Google), o null
  const admins = lista(env.ADMINS), tok = request.headers.get("x-racha-token");
  const nombre = quienEs(tok, env.ACCESOS);  // solo los códigos del secreto ACCESOS pueden ser admin
  if (nombre) return {id: "c:" + nombre, admin: admins.includes(nombre.toLowerCase())};
  const invitado = await codigoInvitado(tok, env);
  if (invitado) return {id: "i:" + invitado, admin: false};
  const sub = await usuarioDeSesion(request, env);
  if (!sub) return null;
  const u = await env.DB.prepare("SELECT email FROM usuarios WHERE google_sub = ?").bind(sub).first();
  return {id: "g:" + sub, admin: !!u && admins.includes(String(u.email).toLowerCase())};
}

function codigoNuevo() {
  const b = new Uint8Array(12); crypto.getRandomValues(b);
  return [...b].map(x => x.toString(16).padStart(2, "0")).join("");
}

async function cuerpo(request) { try { return await request.json(); } catch { return undefined; } }

export async function extra(request, env, url, quienEs) {
  // Rutas /v1/builds, /v1/reporte, /v1/ping y /v1/admin/…; null si no son de aquí
  const ruta = url.pathname, m = request.method, DB = env.DB;
  if (!/^\/v1\/(builds|reporte|ping|admin)(\/|$)/.test(ruta)) return null;
  const q = await quien(request, env, quienEs);
  if (!q) return json({error: "código de acceso inválido"}, 401);

  if (ruta === "/v1/builds" && m === "GET") {
    const {results} = await DB.prepare("SELECT clave, ts FROM builds ORDER BY clave").bind().all();
    return json(results || []);
  }
  if (ruta.startsWith("/v1/builds/") && m === "GET") {
    let clave; try { clave = decodeURIComponent(ruta.slice(11)); } catch { return json({error: "sin build todavía"}, 404); }
    const f = CLAVE.test(clave) && await DB.prepare("SELECT datos, ts FROM builds WHERE clave = ?").bind(clave).first();
    return f ? json({clave, ts: f.ts, datos: JSON.parse(f.datos)}) : json({error: "sin build todavía"}, 404);
  }
  const anon = (await sha256("racha:" + q.id)).slice(0, 16);  // para los límites: no se guarda quién es
  if (ruta === "/v1/reporte" && m === "POST" && await limite(env, "reporte:" + anon, 10, 86400)) return json({error: "ya mandaste muchos reportes hoy"}, 429);
  if (ruta === "/v1/ping" && m === "POST" && await limite(env, "ping:" + anon, 3, 3600)) return json({ok: true, ignorado: true});
  if (ruta === "/v1/reporte" && m === "POST") {  // privado: solo lo lee el admin; no guarda quién lo mandó
    const d = await cuerpo(request) || {};
    const s = v => String(v || "").slice(0, 40);
    const texto = String(d.texto || "").trim();
    if (!texto || texto.length > 4000) return json({error: "escribe qué pasó (máx. 4000 letras)"}, 400);
    const n = await DB.prepare("SELECT COUNT(*) AS n FROM reportes WHERE ts > ?").bind(ahora() - 86400).first();
    if (n && n.n >= 200) return json({error: "demasiados reportes hoy"}, 429);  // tope para no llenar el plan gratis
    await DB.prepare("INSERT INTO reportes (ts, version, vista, fase, texto) VALUES (?, ?, ?, ?, ?)").bind(ahora(), s(d.version), s(d.vista), s(d.fase), texto).run();
    return json({ok: true});
  }
  if (ruta === "/v1/ping" && m === "POST") {  // métricas opt-in: solo contadores por día/versión/región, sin identidad
    const d = await cuerpo(request) || {};
    const version = /^\d+\.\d+\.\d+$/.test(d.version || "") ? d.version : "?";
    const region = /^[a-z0-9]{2,5}$/.test(d.region || "") ? d.region : "?";
    const b = k => d[k] ? 1 : 0;
    await DB.prepare("INSERT INTO metricas (dia, version, region, usos, overlay, champ_select, revision) VALUES (?, ?, ?, 1, ?, ?, ?) " +
      "ON CONFLICT(dia, version, region) DO UPDATE SET usos = usos + 1, overlay = overlay + excluded.overlay, champ_select = champ_select + excluded.champ_select, revision = revision + excluded.revision")
      .bind(new Date().toISOString().slice(0, 10), version, region, b("overlay"), b("champ_select"), b("revision")).run();
    return json({ok: true});
  }

  if (!ruta.startsWith("/v1/admin/") && !(ruta === "/v1/builds" && m === "PUT")) return json({error: "no existe"}, 404);
  if (!q.admin) return json({error: "solo el admin"}, 403);
  if (ruta === "/v1/builds" && m === "PUT") {  // builds.py --subir: {«Campeón|POS»: datos, …}
    const d = await cuerpo(request);
    const pares = d && typeof d === "object" && !Array.isArray(d) ? Object.entries(d) : null;
    if (!pares || pares.length > 300 || !pares.every(([k, v]) => CLAVE.test(k) && JSON.stringify(v).length < 20000)) return json({error: "builds inválidas"}, 400);
    for (const [k, v] of pares) await DB.prepare("INSERT OR REPLACE INTO builds (clave, datos, ts) VALUES (?, ?, ?)").bind(k, JSON.stringify(v), ahora()).run();
    return json({ok: true, n: pares.length});
  }
  if (ruta === "/v1/admin/invitados" && m === "GET") {
    const {results} = await DB.prepare("SELECT nombre, email, creado FROM invitados ORDER BY creado").bind().all();
    return json(results || []);  // los códigos no se vuelven a mostrar
  }
  if (ruta === "/v1/admin/invitados" && m === "POST") {
    const d = await cuerpo(request) || {};
    const nombre = String(d.nombre || "").trim().toLowerCase(), email = d.email ? String(d.email).trim().toLowerCase() : null;
    if (!NOMBRE.test(nombre) || (email && !EMAIL.test(email))) return json({error: "nombre (2–24 letras, números, - o _) o correo inválidos"}, 400);
    if (await DB.prepare("SELECT 1 AS si FROM invitados WHERE nombre = ?").bind(nombre).first()) return json({error: "ya existe ese nombre"}, 409);
    const codigo = codigoNuevo();
    await DB.prepare("INSERT INTO invitados (nombre, codigo, email, creado) VALUES (?, ?, ?, ?)").bind(nombre, codigo, email, ahora()).run();
    return json({nombre, email, codigo});
  }
  if (ruta.startsWith("/v1/admin/invitados/") && m === "DELETE") {
    let nombre; try { nombre = decodeURIComponent(ruta.slice(20)); } catch { return json({error: "no existe"}, 404); }
    await DB.prepare("DELETE FROM invitados WHERE nombre = ?").bind(nombre).run();
    return json({ok: true});
  }
  if (ruta === "/v1/admin/reportes" && m === "GET") {
    const {results} = await DB.prepare("SELECT id, ts, version, vista, fase, texto FROM reportes ORDER BY id DESC LIMIT 200").bind().all();
    return json(results || []);
  }
  if (ruta.startsWith("/v1/admin/reportes/") && m === "DELETE") {
    await DB.prepare("DELETE FROM reportes WHERE id = ?").bind(Number(ruta.slice(19)) || 0).run();
    return json({ok: true});
  }
  if (ruta === "/v1/admin/metricas" && m === "GET") {
    const {results} = await DB.prepare("SELECT * FROM metricas WHERE dia >= ? ORDER BY dia DESC").bind(new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10)).all();
    return json(results || []);
  }
  return json({error: "no existe"}, 404);
}
