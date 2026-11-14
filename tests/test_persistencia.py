"""Prueba obligatoria: ejecutar → guardar → cerrar/reiniciar → recuperar → repetir → coincidir."""
import numpy as np
import pytest
from app import create_app, comparar
from simtele import db, servicio, modelos as M


@pytest.mark.parametrize("tipo", M.ESC_TIPOS)
def test_guardar_cerrar_recuperar_repetir(tmp_path, tipo):
    ruta = str(tmp_path / "t.db")
    p = {k: v for k, v in M.PARAMETROS["deterioro"][tipo].items() if k != "nota"}
    res = servicio.ejecutar("deterioro", tipo, p, {"tol": 1e-10, "max_iter": 3000})
    con = db.conectar(ruta)
    sid = db.guardar(con, "deterioro", tipo, res)
    con.close()                                              # "cerrar la aplicación"

    con2 = db.conectar(ruta)                                 # "reiniciar"
    sim = db.abrir(con2, sid)
    assert sim["tipo"] == tipo and sim["params"]["D0"] == p["D0"]
    assert len(sim["ejecuciones"]) == len(res["ejecuciones"])
    jac_orig = next(e for e in res["ejecuciones"] if e["metodo"] == "Jacobi")
    jac_rec = next(e for e in sim["ejecuciones"] if e["metodo"] == "Jacobi")
    assert len(jac_rec["iteraciones"]) == len(jac_orig["iteraciones"])   # iteraciones recuperadas

    s = sim["params"].pop("sistema"); sim["params"].pop("diagnostico")
    res2 = servicio.ejecutar("deterioro", tipo, sim["params"],
                             {"tol": s["tol"], "max_iter": s["max_iter"], "n": len(s["b"])})
    sid2 = db.guardar(con2, "deterioro", tipo, res2)
    assert all(c["ok"] for c in comparar(db.abrir(con2, sid), db.abrir(con2, sid2)))


def test_app_flujo_web(tmp_path):
    app = create_app(str(tmp_path / "w.db")); c = app.test_client()
    for clave in M.CASOS:
        assert c.get(f"/modulo/{clave}").status_code == 200
        form = {k: v for k, v in M.PARAMETROS[clave]["NORMAL"].items() if k != "nota"}
        form["tipo"] = "NORMAL"
        r = c.post(f"/modulo/{clave}/ejecutar", data=form)
        assert r.status_code == 302
        assert c.get(r.headers["Location"]).status_code == 200
    assert b"NORMAL" in c.get("/historial?q=Deterioro").data
    sid = 2
    assert c.get(f"/grafico/{sid}/curva.png").mimetype == "image/png"
    assert c.get(f"/grafico/{sid}/convergencia.png").mimetype == "image/png"
    r = c.post(f"/simulacion/{sid}/relanzar")
    assert r.status_code == 302 and "vs=2" in r.headers["Location"]
    assert "Sí".encode() in c.get(r.headers["Location"]).data


def test_validacion_rechaza_parametros_invalidos(tmp_path):
    c = create_app(str(tmp_path / "v.db")).test_client()
    form = {k: v for k, v in M.PARAMETROS["oscilaciones"]["NORMAL"].items() if k != "nota"}
    form.update(tipo="NORMAL", zeta=1.5)
    assert c.post("/modulo/oscilaciones/ejecutar", data=form).status_code == 400
