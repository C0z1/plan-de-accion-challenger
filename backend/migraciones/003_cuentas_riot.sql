-- v0.27: una sola vez sobre la D1 que ya existe y ANTES del deploy (schema.sql ya lo trae para bases nuevas).
-- Tu cuenta de Google vinculada a tus cuentas de LoL (solo las que tuvieron sesión en tu cliente), y de qué cuenta es cada resumen.
CREATE TABLE IF NOT EXISTS cuentas_riot (
  google_sub TEXT NOT NULL,
  riot_id    TEXT NOT NULL,      -- «Nombre#TAG» (el puuid cambia según la key de Riot: no sirve de clave)
  region     TEXT,
  creado     INTEGER,
  ultima     INTEGER,
  PRIMARY KEY (google_sub, riot_id)
);
ALTER TABLE resumenes ADD COLUMN cuenta TEXT;  -- riot_id de la partida; NULL = resúmenes de antes de 0.27 (de la cuenta principal)
