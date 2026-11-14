"""Persistencia: guarda y recupera ejecuciones completas (no depende de memoria)."""
import json
import os
import sqlite3
from . import modelos as M

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_DEFECTO = os.path.join(RAIZ, "data", "simtele.db")
ESQUEMA = os.path.join(RAIZ, "db", "schema_sqlite.sql")


def conectar(ruta=None):
    ruta = ruta or os.environ.get("SIMTELE_DB", RUTA_DEFECTO)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    with open(ESQUEMA, encoding="utf-8") as f:
        con.executescript(f.read())
    for clave, c in M.CASOS.items():
        con.execute("INSERT OR IGNORE INTO caso_estudio(id, nombre) VALUES (?,?)", (c["id"], c["nombre"]))
    con.commit()
    return con


def guardar(con, caso, tipo, resultado, usuario=None):
    """Guarda escenario + simulación + ejecuciones + iteraciones + resumen. Devuelve id."""
    caso_id = M.CASOS[caso]["id"]
    cur = con.execute(
        "INSERT INTO escenario(caso_id, tipo, parametros_json, fuente_datos) VALUES (?,?,?,?)",
        (caso_id, tipo, json.dumps(resultado["params"]), M.FUENTE))
    esc_id = cur.lastrowid
    cur = con.execute("INSERT INTO simulacion(escenario_id, usuario_equipo) VALUES (?,?)", (esc_id, usuario))
    sim_id = cur.lastrowid
    for ej in resultado["ejecuciones"]:
        c = con.execute(
            "INSERT INTO ejecucion_metodo(simulacion_id, metodo, tolerancia, paso, max_iter, convergio, tiempo_ms)"
            " VALUES (?,?,?,?,?,?,?)",
            (sim_id, ej["metodo"], ej["tolerancia"], ej["paso"], ej["max_iter"],
             int(ej["convergio"]), ej["tiempo_ms"]))
        ej_id = c.lastrowid
        con.executemany(
            "INSERT INTO iteracion_resultado(ejecucion_id, numero, aproximacion_json, residual, error_abs, error_rel)"
            " VALUES (?,?,?,?,?,?)",
            [(ej_id, h["numero"], json.dumps(h["aproximacion"]), h["residual"], h["error_abs"], h["error_rel"])
             for h in ej["iteraciones"]])
        r = ej["resumen"]
        con.execute(
            "INSERT INTO resultado_resumen(ejecucion_id, referencia, valor_json, metrica_error_json, interpretacion)"
            " VALUES (?,?,?,?,?)",
            (ej_id, r.get("referencia"), json.dumps(r.get("valor", {})),
             json.dumps(r.get("metricas", {})), r.get("interpretacion")))
    con.commit()
    return sim_id


def listar(con, q=None):
    sql = ("SELECT s.id, s.fecha, s.estado, s.usuario_equipo, e.tipo, c.nombre AS caso, c.id AS caso_id,"
           " (SELECT COUNT(*) FROM ejecucion_metodo m WHERE m.simulacion_id=s.id) AS n_metodos"
           " FROM simulacion s JOIN escenario e ON e.id=s.escenario_id JOIN caso_estudio c ON c.id=e.caso_id")
    args = []
    if q:
        sql += (" WHERE c.nombre LIKE ? OR e.tipo LIKE ? OR CAST(s.id AS TEXT)=? OR s.usuario_equipo LIKE ?")
        like = f"%{q}%"
        args = [like, like, q.strip(), like]
    sql += " ORDER BY s.id DESC"
    return [dict(r) for r in con.execute(sql, args)]


def abrir(con, sim_id):
    s = con.execute(
        "SELECT s.id, s.fecha, s.estado, s.usuario_equipo, e.tipo, e.parametros_json, e.fuente_datos,"
        " c.id AS caso_id, c.nombre AS caso FROM simulacion s JOIN escenario e ON e.id=s.escenario_id"
        " JOIN caso_estudio c ON c.id=e.caso_id WHERE s.id=?", (sim_id,)).fetchone()
    if s is None:
        return None
    sim = dict(s)
    sim["params"] = json.loads(sim.pop("parametros_json"))
    sim["caso_clave"] = next(k for k, c in M.CASOS.items() if c["id"] == sim["caso_id"])
    sim["ejecuciones"] = []
    for m in con.execute("SELECT * FROM ejecucion_metodo WHERE simulacion_id=? ORDER BY id", (sim_id,)):
        ej = dict(m)
        ej["convergio"] = bool(ej["convergio"])
        its = con.execute("SELECT numero, aproximacion_json, residual, error_abs, error_rel"
                          " FROM iteracion_resultado WHERE ejecucion_id=? ORDER BY numero", (m["id"],)).fetchall()
        ej["iteraciones"] = [{"numero": i["numero"], "aproximacion": json.loads(i["aproximacion_json"]),
                              "residual": i["residual"], "error_abs": i["error_abs"],
                              "error_rel": i["error_rel"]} for i in its]
        r = con.execute("SELECT * FROM resultado_resumen WHERE ejecucion_id=?", (m["id"],)).fetchone()
        ej["resumen"] = ({"referencia": r["referencia"], "valor": json.loads(r["valor_json"]),
                          "metricas": json.loads(r["metrica_error_json"] or "{}"),
                          "interpretacion": r["interpretacion"]} if r else {})
        sim["ejecuciones"].append(ej)
    return sim
