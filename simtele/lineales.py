"""Sistemas lineales A x = b: Jacobi, Gauss-Seidel, LU, Gradiente Conjugado y
solución directa de referencia. Todos devuelven un dict homogéneo con el historial
de iteraciones (error vs x*, residual) para guardar en la BD."""
import time
import numpy as np
from . import errores as E


def _registro(k, x, A, b, x_ref, dx=None):
    return {
        "numero": k,
        "aproximacion": [float(v) for v in x],
        "residual": E.residual(A, x, b),
        "error_abs": E.error_abs(x, x_ref) if x_ref is not None else None,
        "error_rel": E.error_rel(x, x_ref) if x_ref is not None else None,
        "paso": dx,
    }


def referencia_directa(A, b):
    """Solución directa de referencia (LAPACK, pivoteo parcial)."""
    return np.linalg.solve(A, b)


def jacobi(A, b, x0=None, tol=1e-10, max_iter=5000, x_ref=None):
    t0 = time.perf_counter()
    n = len(b)
    x = np.zeros(n) if x0 is None else np.array(x0, float)
    D = np.diag(A)
    if np.any(D == 0):
        raise ValueError("Jacobi requiere diagonal no nula")
    R = A - np.diagflat(D)
    hist = [_registro(0, x, A, b, x_ref)]
    conv, nb = False, np.linalg.norm(b)
    for k in range(1, max_iter + 1):
        xn = (b - R @ x) / D
        dx = float(np.linalg.norm(xn - x, np.inf))
        x = xn
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e150:
            break
        hist.append(_registro(k, x, A, b, x_ref, dx))
        if hist[-1]["residual"] / nb < tol:
            conv = True
            break
    return _salida("Jacobi", x, hist, conv, tol, max_iter, t0)


def gauss_seidel(A, b, x0=None, tol=1e-10, max_iter=5000, x_ref=None):
    t0 = time.perf_counter()
    n = len(b)
    x = np.zeros(n) if x0 is None else np.array(x0, float)
    if np.any(np.diag(A) == 0):
        raise ValueError("Gauss-Seidel requiere diagonal no nula")
    hist = [_registro(0, x, A, b, x_ref)]
    conv, nb = False, np.linalg.norm(b)
    for k in range(1, max_iter + 1):
        xv = x.copy()
        for i in range(n):
            s1 = A[i, :i] @ x[:i]
            s2 = A[i, i + 1:] @ xv[i + 1:]
            x[i] = (b[i] - s1 - s2) / A[i, i]
        dx = float(np.linalg.norm(x - xv, np.inf))
        if not np.all(np.isfinite(x)) or np.max(np.abs(x)) > 1e150:
            break
        hist.append(_registro(k, x, A, b, x_ref, dx))
        if hist[-1]["residual"] / nb < tol:
            conv = True
            break
    return _salida("Gauss-Seidel", x, hist, conv, tol, max_iter, t0)


def lu_doolittle(A):
    """Factorización A = L U (Doolittle, SIN pivoteo; válida para SPD)."""
    n = A.shape[0]
    L, U = np.eye(n), np.zeros((n, n))
    for i in range(n):
        for j in range(i, n):
            U[i, j] = A[i, j] - L[i, :i] @ U[:i, j]
        if abs(U[i, i]) < 1e-300:
            raise ZeroDivisionError("pivote nulo: usar pivoteo parcial")
        for j in range(i + 1, n):
            L[j, i] = (A[j, i] - L[j, :i] @ U[:i, i]) / U[i, i]
    return L, U


def lu_solve(A, b, x_ref=None, **_):
    t0 = time.perf_counter()
    L, U = lu_doolittle(A)
    n = len(b)
    y = np.zeros(n)
    for i in range(n):                       # L y = b
        y[i] = b[i] - L[i, :i] @ y[:i]
    x = np.zeros(n)
    for i in range(n - 1, -1, -1):           # U x = y
        x[i] = (y[i] - U[i, i + 1:] @ x[i + 1:]) / U[i, i]
    hist = [_registro(1, x, A, b, x_ref)]
    out = _salida("LU", x, hist, True, None, None, t0)
    out["L"], out["U"], out["y"] = L, U, y
    return out


def gradiente_conjugado(A, b, x0=None, tol=1e-10, max_iter=None, x_ref=None):
    """CG estándar. Requiere A simétrica definida positiva (se verifica)."""
    t0 = time.perf_counter()
    if not np.allclose(A, A.T):
        raise ValueError("CG requiere A simétrica")
    if np.min(np.linalg.eigvalsh(A)) <= 0:
        raise ValueError("CG requiere A definida positiva")
    n = len(b)
    max_iter = max_iter or 10 * n
    x = np.zeros(n) if x0 is None else np.array(x0, float)
    r = b - A @ x
    p = r.copy()
    rs = r @ r
    nb = np.linalg.norm(b)
    hist = [_registro(0, x, A, b, x_ref)]
    conv = np.sqrt(rs) / nb < tol
    k = 0
    while not conv and k < max_iter:
        k += 1
        Ap = A @ p
        alfa = rs / (p @ Ap)
        x = x + alfa * p
        r = r - alfa * Ap
        rs_n = r @ r
        hist.append(_registro(k, x, A, b, x_ref, float(abs(alfa) * np.linalg.norm(p))))
        hist[-1]["alfa"] = float(alfa)
        if np.sqrt(rs_n) / nb < tol:
            conv = True
            break
        p = r + (rs_n / rs) * p
        rs = rs_n
    return _salida("Gradiente conjugado", x, hist, conv, tol, max_iter, t0)


def _salida(nombre, x, hist, conv, tol, max_iter, t0):
    return {
        "metodo": nombre, "x": x, "historial": hist, "convergio": bool(conv),
        "iteraciones": hist[-1]["numero"], "tol": tol, "max_iter": max_iter,
        "tiempo_ms": (time.perf_counter() - t0) * 1000.0,
    }


def diagnostico(A):
    """Propiedades teóricas que justifican (o no) la convergencia de cada método."""
    n = A.shape[0]
    D = np.diag(A)
    fuera = np.sum(np.abs(A), axis=1) - np.abs(D)
    dd_estricta = bool(np.all(np.abs(D) > fuera))
    sim = bool(np.allclose(A, A.T))
    ev = np.linalg.eigvalsh((A + A.T) / 2)
    spd = sim and bool(ev.min() > 0)
    Dm = np.diagflat(D)
    TJ = np.eye(n) - np.linalg.solve(Dm, A)                       # Jacobi
    TG = -np.linalg.solve(np.tril(A), np.triu(A, 1))              # Gauss-Seidel
    rho = lambda T: float(np.max(np.abs(np.linalg.eigvals(T))))
    return {
        "n": n, "simetrica": sim, "spd": spd, "dd_estricta": dd_estricta,
        "lambda_min": float(ev.min()), "lambda_max": float(ev.max()),
        "kappa2": E.cond2(A), "rho_jacobi": rho(TJ), "rho_gs": rho(TG),
    }


def ejecutar_todos(A, b, x_ref=None, tol=1e-10, max_iter=5000):
    """Corre los cuatro métodos + referencia y devuelve resultados comparables."""
    if x_ref is None:
        x_ref = referencia_directa(A, b)
    res = {"referencia": x_ref}
    res["Jacobi"] = jacobi(A, b, tol=tol, max_iter=max_iter, x_ref=x_ref)
    res["Gauss-Seidel"] = gauss_seidel(A, b, tol=tol, max_iter=max_iter, x_ref=x_ref)
    res["LU"] = lu_solve(A, b, x_ref=x_ref)
    res["Gradiente conjugado"] = gradiente_conjugado(
        A, b, tol=tol, max_iter=max(10 * len(b), 200), x_ref=x_ref)
    return res
