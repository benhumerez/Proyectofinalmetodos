"""Orquesta la ejecución de cada módulo (validación → cálculo → estructura guardable).

Semana 1: Módulo 2 ejecuta sistemas lineales (Jacobi, Gauss-Seidel, LU, CG, directa)
y la raíz analítica del umbral. Módulos 1, 3 y 4 ejecutan su REFERENCIA ANALÍTICA y
la sensibilidad; sus métodos numéricos (RK, integración, interpolación, raíces) se
agregan en la semana 2 sobre esta misma estructura."""
import math
import numpy as np
from . import errores as E, lineales as L, modelos as M


def _f(v):
    """float JSON-seguro (nan/inf -> None)."""
    v = float(v)
    return v if math.isfinite(v) else None


# ---------------------------- validaciones --------------------------------
def validar(caso, p):
    err = []
    pos = lambda k: p.get(k) is not None and p[k] > 0 or err.append(f"{k} debe ser > 0")
    if caso == "detencion":
        if "v0" in p:
            pos("v0"); pos("a")
            if p.get("t_reac", 0) < 0:
                err.append("t_reac debe ser ≥ 0")
    elif caso == "deterioro":
        pos("D_umbral")
        if p["D_umbral"] <= p["D0"]:
            err.append("D_umbral debe ser > D0")
        if not (0 <= p["D0"] < 1):
            err.append("D0 debe estar en [0,1)")
    elif caso == "oscilaciones":
        pos("m"); pos("k")
        if not (0 <= p["zeta"] < 1):
            err.append("ζ debe estar en [0,1) (régimen subamortiguado, referencia analítica)")
        if p.get("F0", 0) < 0 or p.get("r", 0) < 0:
            err.append("F0 y r deben ser ≥ 0")
    elif caso == "sensores":
        if not (3 <= int(p["n_nodos"]) <= 40):
            err.append("n_nodos debe estar entre 3 y 40")
        if p["b"] <= p["a"]:
            err.append("b debe ser > a")
        if p.get("ruido", 0) < 0:
            err.append("ruido debe ser ≥ 0")
    return err


def _ejec(metodo, x_hist, conv, tol=None, paso=None, max_iter=None, ms=0.0, resumen=None):
    return {"metodo": metodo, "iteraciones": x_hist, "convergio": bool(conv),
            "tolerancia": tol, "paso": paso, "max_iter": max_iter, "tiempo_ms": ms,
            "resumen": resumen or {}}


def _hist_de(salida):
    return [{"numero": h["numero"], "aproximacion": [_f(v) for v in h["aproximacion"]],
             "residual": _f(h["residual"]), "error_abs": _f(h["error_abs"]),
             "error_rel": None if h["error_rel"] is None else _f(h["error_rel"])}
            for h in salida["historial"]]


# ------------------------------- módulos ----------------------------------
def ejecutar(caso, tipo, params, config=None):
    """Devuelve {"params": <reproducible>, "ejecuciones": [...]}"""
    config = config or {}
    fn = {"detencion": _m1, "deterioro": _m2, "oscilaciones": _m3, "sensores": _m4}[caso]
    return fn(tipo, dict(params), config)


def _m1(tipo, p, cfg):
    if tipo == "MAL_CONDICIONADO":
        T, v0, eps = p["T"], p["v0"], p["eps"]
        t0, t1 = T, T * (1 - (eps / v0) ** (1 / 3))
        res = {"referencia": "raíz triple t=T de v(t)=v0(1-t/T)^3",
               "valor": {"T": T, "t_raiz_perturbada": _f(t1)},
               "metricas": {"desplazamiento_raiz": _f(abs(t1 - t0)), "amplificacion_abs": _f(abs(t1 - t0) / eps)},
               "interpretacion": "Subexperimento numérico: una perturbación de 1e-9 m/s en v(t) mueve la "
                                 "raíz ≈1e-3 s (amplificación ~1e6). No es un peligro físico: es sensibilidad "
                                 "matemática de una raíz múltiple (Newton pierde orden cuadrático)."}
        return {"params": p, "ejecuciones": [_ejec("Referencia analítica", [], True, resumen=res)]}
    v0, a, tr = p["v0"], p["a"], p.get("t_reac", 0.0)
    t_det, d_fren = v0 / a, v0 ** 2 / (2 * a)
    res = {"referencia": "v(t)=v0-a t ; t_det=v0/a ; d=v0²/(2a)",
           "valor": {"t_det_s": t_det, "d_frenado_m": d_fren, "d_total_m": d_fren + v0 * tr},
           "metricas": {"elasticidad_d_total_v0": E.elasticidad(lambda v: M.d_total(v, a, tr), v0),
                        "elasticidad_d_total_a": E.elasticidad(lambda x: M.d_total(v0, x, tr), a)},
           "interpretacion": f"Con v0={v0} m/s y a={a} m/s² la cabina se detiene en {t_det:.2f} s y "
                             f"recorre {d_fren + v0 * tr:.2f} m incluyendo la reacción. Resultado de "
                             f"referencia: aún sin RK/integración (semana 2)."}
    return {"params": p, "ejecuciones": [_ejec("Referencia analítica", [], True, resumen=res)]}


def _m2(tipo, p, cfg):
    tol = float(cfg.get("tol", 1e-10))
    max_iter = int(cfg.get("max_iter", 5000))
    n = cfg.get("n")
    A, b, xs, desc = M.sistema_lineal(tipo, n)
    p["sistema"] = {"descripcion": desc, "A": A.tolist(), "b": b.tolist(), "x_ref": xs.tolist(),
                    "tol": tol, "max_iter": max_iter}
    ejs = []
    t_root = M.raiz_umbral(p["D0"], p["alfa"], p["beta"], p["D_umbral"])
    ejs.append(_ejec("Raíz analítica (cuadrática)", [], math.isfinite(t_root), resumen={
        "referencia": "menor raíz positiva de D0+αt+βt²=D_umbral",
        "valor": {"t_umbral_meses": _f(t_root)},
        "metricas": {}, "interpretacion": "Tiempo hipotético al umbral (datos sintéticos); "
                                          "bisección/Newton/secante se comparan en la semana 2."}))
    diag = L.diagnostico(A)
    xr = L.referencia_directa(A, b)
    res = L.ejecutar_todos(A, b, xs, tol=tol, max_iter=max_iter)
    ejs.append(_ejec("Directa (referencia)", [{"numero": 1, "aproximacion": [_f(v) for v in xr],
                                                "residual": _f(E.residual(A, xr, b)),
                                                "error_abs": _f(E.error_abs(xr, xs)),
                                                "error_rel": _f(E.error_rel(xr, xs))}], True,
                     resumen={"referencia": "numpy.linalg.solve (LAPACK)",
                              "valor": {"x": [_f(v) for v in xr]},
                              "metricas": {"kappa2": _f(diag["kappa2"])},
                              "interpretacion": "Solución directa usada como referencia numérica."}))
    for nombre in ("Jacobi", "Gauss-Seidel", "LU", "Gradiente conjugado"):
        s = res[nombre]
        h = s["historial"][-1]
        if nombre == "Jacobi":
            txt = (f"ρ(T_J)={diag['rho_jacobi']:.4g}: " +
                   ("converge (ρ<1)." if diag["rho_jacobi"] < 1 else "NO converge (ρ≥1)."))
        elif nombre == "Gauss-Seidel":
            txt = (f"ρ(T_GS)={diag['rho_gs']:.6g}; A SPD ⇒ converge en teoría" +
                   ("" if s["convergio"] else ", pero no alcanzó la tolerancia en max_iter (convergencia lenta)") + ".")
        elif nombre == "LU":
            txt = f"Método directo; κ₂(A)={diag['kappa2']:.3g} limita la precisión alcanzable."
        else:
            txt = "A SPD ⇒ CG aplicable; con κ grande la pérdida de ortogonalidad degrada el error."
        ejs.append(_ejec(nombre, _hist_de(s), s["convergio"], tol=s["tol"], max_iter=s["max_iter"],
                         ms=s["tiempo_ms"], resumen={
            "referencia": "x* conocido (b=A x*)",
            "valor": {"x": [_f(v) for v in s["x"]]},
            "metricas": {"error_rel_final": h["error_rel"], "residual_final": h["residual"],
                         "iteraciones": s["iteraciones"],
                         "cota_kappa_residual": E.cota_error_por_residual(A, s["x"], b)
                         if np.all(np.isfinite(s["x"])) else None},
            "interpretacion": txt}))
    p["diagnostico"] = {k: (_f(v) if isinstance(v, float) else v) for k, v in diag.items()}
    return {"params": p, "ejecuciones": ejs}


def _m3(tipo, p, cfg):
    m, k, z = p["m"], p["k"], p["zeta"]
    w0 = math.sqrt(k / m)
    wd = w0 * math.sqrt(1 - z ** 2)
    c = 2 * z * math.sqrt(k * m)
    val = {"omega0_rad_s": w0, "omega_d_rad_s": wd, "c_Ns_m": c, "T_d_s": 2 * math.pi / wd}
    met = {}
    if p.get("F0", 0) > 0:
        X = M.amplitud_estacionaria(p["F0"], k, z, p["r"])
        val["amplitud_estacionaria_m"] = X
        met["elasticidad_X_r"] = E.elasticidad(
            lambda r: M.amplitud_estacionaria(p["F0"], k, z, r), p["r"]) if p["r"] > 0 else None
    if "x0" in p:
        x0, v0 = p["x0"], p["v0"]
        val["C1_m"], val["C2_m"] = x0, (v0 + z * w0 * x0) / wd
        met["elasticidad_C2_zeta"] = E.elasticidad(lambda zz: M.coef_C2(zz, w0, x0, v0), z, 1e-8)
    res = {"referencia": "vibración libre subamortiguada / amplitud estacionaria",
           "valor": {kk: _f(v) for kk, v in val.items()},
           "metricas": {kk: None if v is None else _f(v) for kk, v in met.items()},
           "interpretacion": f"ω0={w0:.3f} rad/s, ζ={z}, ωd={wd:.3f} rad/s. Referencia analítica; "
                             f"RK2/RK4 e integración de x(t)² se añaden en la semana 2."}
    return {"params": p, "ejecuciones": [_ejec("Referencia analítica", [], True, resumen=res)]}


def _m4(tipo, p, cfg):
    n = int(p["n_nodos"])
    a, b = p["a"], p["b"]
    out = []
    for nodos in ("equiespaciados", "Chebyshev"):
        if nodos == "equiespaciados":
            t = np.linspace(a, b, n)
        else:
            kk = np.arange(n)
            t = 0.5 * (a + b) + 0.5 * (b - a) * np.cos((2 * kk + 1) * math.pi / (2 * n))
        V = np.vander(t, increasing=True)
        out.append({"nodos": nodos, "kappa_V": _f(np.linalg.cond(V))})
    res = {"referencia": "y(t)=sin t en los nodos",
           "valor": {"n": n, "intervalo": [a, b]},
           "metricas": {"kappa_V_equiespaciados": out[0]["kappa_V"], "kappa_V_Chebyshev": out[1]["kappa_V"]},
           "interpretacion": "Condicionamiento de la base monomial para los nodos elegidos. Lagrange, Newton "
                             "y spline se implementan en la semana 2."}
    return {"params": p, "ejecuciones": [_ejec("Referencia analítica", [], True, resumen=res)]}
