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
  PRIMARY KEY (google_sub, match_id)
);
