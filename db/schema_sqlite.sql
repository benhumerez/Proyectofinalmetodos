-- SIMTELE-RISK · esquema relacional (SQLite; usado por la aplicación)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS caso_estudio (
    id             INTEGER PRIMARY KEY,
    nombre         TEXT NOT NULL UNIQUE,
    modelo_version TEXT NOT NULL DEFAULT 'v1'
);

CREATE TABLE IF NOT EXISTS escenario (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    caso_id        INTEGER NOT NULL REFERENCES caso_estudio(id),
    tipo           TEXT NOT NULL CHECK (tipo IN ('NORMAL','ESTRES','MAL_CONDICIONADO')),
    parametros_json TEXT NOT NULL,
    fuente_datos   TEXT NOT NULL DEFAULT 'Datos sintéticos / parámetros supuestos'
);

CREATE TABLE IF NOT EXISTS simulacion (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    escenario_id   INTEGER NOT NULL REFERENCES escenario(id),
    fecha          TEXT NOT NULL DEFAULT (datetime('now')),
    usuario_equipo TEXT,
    estado         TEXT NOT NULL DEFAULT 'COMPLETADA'
                   CHECK (estado IN ('PENDIENTE','COMPLETADA','ERROR'))
);

CREATE TABLE IF NOT EXISTS ejecucion_metodo (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    simulacion_id INTEGER NOT NULL REFERENCES simulacion(id) ON DELETE CASCADE,
    metodo        TEXT NOT NULL,
    tolerancia    REAL,
    paso          REAL,
    max_iter      INTEGER,
    convergio     INTEGER NOT NULL CHECK (convergio IN (0,1)),
    tiempo_ms     REAL
);

CREATE TABLE IF NOT EXISTS iteracion_resultado (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id     INTEGER NOT NULL REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
    numero           INTEGER NOT NULL,
    aproximacion_json TEXT NOT NULL,
    residual         REAL,
    error_abs        REAL,
    error_rel        REAL
);

CREATE TABLE IF NOT EXISTS resultado_resumen (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ejecucion_id     INTEGER NOT NULL UNIQUE REFERENCES ejecucion_metodo(id) ON DELETE CASCADE,
    referencia       TEXT,
    valor_json       TEXT NOT NULL,
    metrica_error_json TEXT,
    interpretacion   TEXT
);

CREATE INDEX IF NOT EXISTS ix_esc_caso   ON escenario(caso_id);
CREATE INDEX IF NOT EXISTS ix_sim_esc    ON simulacion(escenario_id);
CREATE INDEX IF NOT EXISTS ix_ej_sim     ON ejecucion_metodo(simulacion_id);
CREATE INDEX IF NOT EXISTS ix_it_ej      ON iteracion_resultado(ejecucion_id, numero);
