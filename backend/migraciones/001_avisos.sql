-- v0.11 (F5): una sola vez sobre la D1 que ya existe (schema.sql ya las trae para bases nuevas)
ALTER TABLE metricas ADD COLUMN avisos INTEGER DEFAULT 0;
ALTER TABLE metricas ADD COLUMN partidas_con_aviso INTEGER DEFAULT 0;
