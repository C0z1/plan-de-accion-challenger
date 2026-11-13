-- Racha · cuenta en la nube (Cloudflare D1, plan gratis). Solo lo necesario; «borrar mis datos» quita todo de un usuario.
CREATE TABLE IF NOT EXISTS usuarios (
  google_sub TEXT PRIMARY KEY,   -- «sub» del id_token de Google
  email      TEXT NOT NULL,
  nombre     TEXT,
  ajustes    TEXT,               -- JSON de Ajustes (avisos, overlay…)
  riot_id    TEXT,
  region     TEXT,
  creado     INTEGER,
  ultima     INTEGER
);
CREATE TABLE IF NOT EXISTS sesiones (
  token_hash TEXT PRIMARY KEY,   -- sha256 del token: el token en claro nunca se guarda
  google_sub TEXT NOT NULL,
  exp        INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS resumenes (
  google_sub TEXT NOT NULL,
  match_id   TEXT NOT NULL,
  ts         INTEGER,
  resumen    TEXT NOT NULL,      -- JSON chico: campeón, resultado, KDA, score, reglas, error
  cuenta     TEXT,               -- riot_id de la partida (v0.27; NULL = de la cuenta principal, de antes)
  PRIMARY KEY (google_sub, match_id)
);
CREATE TABLE IF NOT EXISTS cuentas_riot (  -- v0.27: tu Google vinculado a tus cuentas de LoL (migraciones/003_cuentas_riot.sql)
  google_sub TEXT NOT NULL,
  riot_id    TEXT NOT NULL,
  region     TEXT,
  creado     INTEGER,
  ultima     INTEGER,
  PRIMARY KEY (google_sub, riot_id)
);
-- v0.8 (todo gratis): builds compartidas, invitaciones, reportes privados y métricas anónimas
CREATE TABLE IF NOT EXISTS builds (
  clave TEXT PRIMARY KEY,        -- «Campeón|POSICIÓN» (como builds.json)
  datos TEXT NOT NULL,           -- JSON del resumen de la build de los onetricks del top
  ts    INTEGER
);
CREATE TABLE IF NOT EXISTS invitados (
  nombre TEXT PRIMARY KEY,
  codigo TEXT NOT NULL UNIQUE,   -- código de acceso (también sirve sin Google)
  email  TEXT,                   -- correo de Google permitido (opcional)
  creado INTEGER
);
CREATE TABLE IF NOT EXISTS reportes (
  id      INTEGER PRIMARY KEY AUTOINCREMENT,
  ts      INTEGER,
  version TEXT, vista TEXT, fase TEXT,
  texto   TEXT                   -- lo que escribió el amigo + el error en pantalla; sin Riot ID ni correo
);
CREATE TABLE IF NOT EXISTS metricas (
  dia     TEXT NOT NULL,         -- AAAA-MM-DD
  version TEXT NOT NULL,
  region  TEXT NOT NULL,
  usos    INTEGER DEFAULT 0, overlay INTEGER DEFAULT 0, champ_select INTEGER DEFAULT 0, revision INTEGER DEFAULT 0,
  avisos  INTEGER DEFAULT 0, partidas_con_aviso INTEGER DEFAULT 0,
  sirvio_si INTEGER DEFAULT 0, sirvio_no INTEGER DEFAULT 0, sirvio_no_vi INTEGER DEFAULT 0,  -- v0.13: «¿te sirvieron los avisos?» (migraciones/002_sirvio.sql)  -- v0.11 (F5): avisos que salieron en la franja; en D1 ya creada: migraciones/001_avisos.sql
  PRIMARY KEY (dia, version, region)
);
-- v0.10: límites de uso (login por IP, ping y reportes por usuario) para no agotar el plan gratis
CREATE TABLE IF NOT EXISTS limites (
  clave   TEXT NOT NULL,         -- «login:<ip>», «ping:<hash>», «reporte:<hash>» (sin identidad en claro)
  ventana INTEGER NOT NULL,      -- inicio de la ventana en segundos
  n       INTEGER DEFAULT 0,
  PRIMARY KEY (clave, ventana)
);
