-- SIMTELE-RISK · esquema relacional (PostgreSQL)

CREATE TABLE IF NOT EXISTS caso_estudio (
    id             INTEGER PRIMARY KEY,
    nombre         TEXT NOT NULL UNIQUE,
    modelo_version TEXT NOT NULL DEFAULT 'v1'
);

CREATE TABLE IF NOT EXISTS escenario (
    id             SERIAL PRIMARY KEY,
    caso_id        INTEGER NOT NULL REFERENCES caso_estudio(id),
    tipo           TEXT NOT NULL CHECK (tipo IN ('NORMAL','ESTRES','MAL_CONDICIONADO')),
    parametros_json JSONB NOT NULL,
    fuente_datos   TEXT NOT NULL DEFAULT 'Datos sintéticos / parámetros supuestos'
);

CREATE TABLE IF NOT EXISTS simulacion (
    id             SERIAL PRIMARY KEY,
    escenario_id   INTEGER NOT NULL REFERENCES escenario(id),
    fecha          TIMESTAMP NOT NULL DEFAULT now(),
    usuario_equipo TEXT,
    estado         TEXT NOT NULL DEFAULT 'COMPLETADA'
                   CHECK (estado IN ('PENDIENTE','COMPLETADA','ERROR'))
);

CREATE TABLE IF NOT EXISTS ejecucion_metodo (
    id            SERIAL PRIMARY KEY,
    simulacion_id INTEGER NOT NULL REFERENCES simulacion(id) ON DELETE CASCADE,
    metodo        TEXT NOT NULL,
    tolerancia    REAL,
    paso          REAL,
    max_iter      INTEGER,
    convergio     BOOLEAN NOT NULL,
    tiempo_ms     REAL
);

CREATE TABLE IF NOT EXISTS iteracion_resultado (
    id               SERIAL PRIMARY KEY,
    ejecucion_id     INTEGER NOT NULL REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
    numero           INTEGER NOT NULL,
    aproximacion_json JSONB NOT NULL,
    residual         REAL,
    error_abs        REAL,
    error_rel        REAL
);

CREATE TABLE IF NOT EXISTS resultado_resumen (
    id               SERIAL PRIMARY KEY,
    ejecucion_id     INTEGER NOT NULL UNIQUE REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
    referencia       TEXT,
    valor_json       JSONB NOT NULL,
    metrica_error_json JSONB,
    interpretacion   TEXT
);

CREATE INDEX IF NOT EXISTS ix_esc_caso   ON escenario(caso_id);
CREATE INDEX IF NOT EXISTS ix_sim_esc    ON simulacion(escenario_id);
CREATE INDEX IF NOT EXISTS ix_ej_sim     ON ejecucion_metodo(simulacion_id);
CREATE INDEX IF NOT EXISTS ix_it_ej      ON iteracion_resultado(ejecucion_id, numero);
