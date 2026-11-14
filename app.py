"""SIMTELE-RISK · prototipo semana 1 (Flask + SQLite).  Ejecutar:  python app.py"""
import json
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, abort, Response
from simtele import db, graficos, modelos as M, servicio

ETQ = {"NORMAL": "NORMAL", "ESTRES": "ESTRÉS", "MAL_CONDICIONADO": "MAL CONDICIONADO"}


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def comparar(sim_a, sim_b, tol=1e-12):
    """Compara la aproximación final de cada método entre dos simulaciones."""
    out = []
    mb = {e["metodo"]: e for e in sim_b["ejecuciones"]}
    for e in sim_a["ejecuciones"]:
        o = mb.get(e["metodo"])
        if not e["iteraciones"] or not o or not o["iteraciones"]:
            continue
        xa = np.array(e["iteraciones"][-1]["aproximacion"], float)
        xb = np.array(o["iteraciones"][-1]["aproximacion"], float)
        d = float(np.max(np.abs(xa - xb))) if xa.shape == xb.shape else float("inf")
        out.append({"metodo": e["metodo"], "dif": d, "ok": d <= tol,
                    "it_a": e["iteraciones"][-1]["numero"], "it_b": o["iteraciones"][-1]["numero"]})
    return out


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path
    app.jinja_env.filters["g"] = lambda v: "—" if v is None else (f"{v:.4g}" if isinstance(v, float) else v)
    app.jinja_env.filters["e"] = lambda v: "—" if v is None else f"{v:.3e}"

    def con():
        return db.conectar(app.config["DB_PATH"])

    @app.route("/")
    def inicio():
        return render_template("index.html", casos=M.CASOS)

    @app.route("/modulo/<clave>")
    def modulo(clave):
        if clave not in M.CASOS:
            abort(404)
        tipo = request.args.get("esc", "NORMAL")
        if tipo not in M.ESC_TIPOS:
            abort(400)
        P = M.PARAMETROS[clave]
        valores = {k: v for k, v in P[tipo].items() if k != "nota"}
        return render_template("modulo.html", clave=clave, caso=M.CASOS[clave], tipo=tipo, etq=ETQ,
                               valores=valores, unidades=P["unidades"], nota=P[tipo].get("nota"),
                               tipos=M.ESC_TIPOS, errores=[])

    @app.route("/modulo/<clave>/ejecutar", methods=["POST"])
    def ejecutar(clave):
        if clave not in M.CASOS:
            abort(404)
        tipo = request.form.get("tipo", "NORMAL")
        if tipo not in M.ESC_TIPOS:
            abort(400)
        base = M.PARAMETROS[clave][tipo]
        params, errs = {}, []
        for k, v0 in base.items():
            if k == "nota":
                continue
            v = _num(request.form.get(k))
            if v is None:
                errs.append(f"{k}: valor numérico requerido")
            else:
                params[k] = v
        if "nota" in base:
            params["nota"] = base["nota"]
        if not errs:
            if clave == "sensores":
                params["n_nodos"] = int(params["n_nodos"])
            errs = servicio.validar(clave, params)
        cfg = {}
        if clave == "deterioro":
            cfg = {"tol": _num(request.form.get("tol")) or 1e-10,
                   "max_iter": int(_num(request.form.get("max_iter")) or 5000),
                   "n": int(_num(request.form.get("n"))) if _num(request.form.get("n")) else None}
            if not (0 < cfg["tol"] < 1):
                errs.append("tol debe estar en (0,1)")
            if cfg["n"] is not None and not (4 <= cfg["n"] <= 50):
                errs.append("n debe estar entre 4 y 50")
        if errs:
            P = M.PARAMETROS[clave]
            return render_template("modulo.html", clave=clave, caso=M.CASOS[clave], tipo=tipo, etq=ETQ,
                                   valores={k: request.form.get(k, "") for k in params or base if k != "nota"},
                                   unidades=P["unidades"], nota=base.get("nota"), tipos=M.ESC_TIPOS,
                                   errores=errs), 400
        res = servicio.ejecutar(clave, tipo, params, cfg)
        c = con()
        sim_id = db.guardar(c, clave, tipo, res, request.form.get("equipo") or None)
        return redirect(url_for("simulacion", sim_id=sim_id))

    @app.route("/simulacion/<int:sim_id>")
    def simulacion(sim_id):
        c = con()
        sim = db.abrir(c, sim_id)
        if sim is None:
            abort(404)
        vs = request.args.get("vs", type=int)
        cmp_ = comparar(db.abrir(c, vs), sim) if vs and db.abrir(c, vs) else None
        return render_template("simulacion.html", sim=sim, etq=ETQ, caso=M.CASOS[sim["caso_clave"]],
                               comparacion=cmp_, vs=vs, json=json)

    @app.route("/simulacion/<int:sim_id>/relanzar", methods=["POST"])
    def relanzar(sim_id):
        c = con()
        sim = db.abrir(c, sim_id)
        if sim is None:
            abort(404)
        p = dict(sim["params"])
        cfg = {}
        if sim["caso_clave"] == "deterioro":
            s = p.pop("sistema")
            p.pop("diagnostico", None)
            cfg = {"tol": s["tol"], "max_iter": s["max_iter"], "n": len(s["b"])}
        res = servicio.ejecutar(sim["caso_clave"], sim["tipo"], p, cfg)
        nuevo = db.guardar(c, sim["caso_clave"], sim["tipo"], res, sim["usuario_equipo"])
        return redirect(url_for("simulacion", sim_id=nuevo, vs=sim_id))

    @app.route("/historial")
    def historial():
        q = request.args.get("q", "").strip() or None
        return render_template("historial.html", filas=db.listar(con(), q), q=q or "", etq=ETQ)

    @app.route("/grafico/<int:sim_id>/<tipo>.png")
    def grafico(sim_id, tipo):
        sim = db.abrir(con(), sim_id)
        if sim is None or tipo not in ("convergencia", "curva"):
            abort(404)
        data = graficos.convergencia(sim) if tipo == "convergencia" else graficos.curva(sim)
        return Response(data, mimetype="image/png")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
