-- v0.13: una sola vez sobre la D1 que ya existe (schema.sql ya las trae para bases nuevas)
ALTER TABLE metricas ADD COLUMN sirvio_si INTEGER DEFAULT 0;
ALTER TABLE metricas ADD COLUMN sirvio_no INTEGER DEFAULT 0;
ALTER TABLE metricas ADD COLUMN sirvio_no_vi INTEGER DEFAULT 0;
