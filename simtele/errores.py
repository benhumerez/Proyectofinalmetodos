"""Teoría de errores transversal (usada por todos los módulos y métodos).

Convenciones
------------
- Error absoluto      E_abs = ||x - x_ref||
- Error relativo      E_rel = ||x - x_ref|| / ||x_ref||   (None si ||x_ref|| == 0)
- Error porcentual    E_%   = 100 * E_rel
- Residual            r = b - A x ,  ||r||
- Sensibilidad        elasticidad  e_p = (dy/dp) * p / y  (número de condición relativo)
"""
import numpy as np

EPS_MAQ = np.finfo(float).eps  # ~2.22e-16


def error_abs(x, x_ref):
    return float(np.linalg.norm(np.atleast_1d(x) - np.atleast_1d(x_ref)))


def error_rel(x, x_ref):
    """Error relativo; devuelve None (no divide por cero) si la referencia es 0."""
    n = float(np.linalg.norm(np.atleast_1d(x_ref)))
    if n == 0.0:
        return None
    return error_abs(x, x_ref) / n


def error_pct(x, x_ref):
    e = error_rel(x, x_ref)
    return None if e is None else 100.0 * e


def residual(A, x, b):
    """Norma 2 del residual b - A x."""
    return float(np.linalg.norm(b - A @ x))


def residual_rel(A, x, b):
    nb = float(np.linalg.norm(b))
    return None if nb == 0 else residual(A, x, b) / nb


def cond2(A):
    return float(np.linalg.cond(A, 2))


def cota_error_por_residual(A, x, b):
    """Cota  ||x - x*|| / ||x*||  <=  kappa(A) * ||r|| / ||b||  (sistemas lineales)."""
    rr = residual_rel(A, x, b)
    return None if rr is None else cond2(A) * rr


def cota_perturbacion(A, b, db):
    """Cota  ||dx||/||x|| <= kappa(A) * ||db||/||b||."""
    return cond2(A) * float(np.linalg.norm(db)) / float(np.linalg.norm(b))


def elasticidad(f, p, h_rel=1e-6):
    """Número de condición relativo de f respecto del parámetro p:
    kappa = |f'(p) * p / f(p)|  (derivada central)."""
    h = abs(p) * h_rel if p != 0 else h_rel
    d = (f(p + h) - f(p - h)) / (2 * h)
    fp = f(p)
    return None if fp == 0 else float(abs(d * p / fp))


def tabla_perturbacion(f, p, delta_rel=0.01):
    """Compara salida nominal y perturbada (p -> p(1+delta_rel))."""
    y0 = f(p)
    y1 = f(p * (1 + delta_rel))
    return {
        "y_nominal": y0, "y_perturbado": y1,
        "error_abs": abs(y1 - y0),
        "error_rel": None if y0 == 0 else abs(y1 - y0) / abs(y0),
        "error_pct": None if y0 == 0 else 100 * abs(y1 - y0) / abs(y0),
        "kappa_rel": elasticidad(f, p),
    }
