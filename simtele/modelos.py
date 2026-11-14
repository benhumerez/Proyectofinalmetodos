"""Modelos matemáticos de los cuatro casos de estudio y sus escenarios.

TODOS los parámetros son SINTÉTICOS / SUPUESTOS (uso educativo). No describen
fallas verificadas de Mi Teleférico ni se conectan con equipos reales.
"""
import math
import numpy as np
from . import errores as E

CASOS = {
    "detencion": {
        "id": 1, "nombre": "Detención de emergencia de cabinas",
        "pregunta": "¿Cómo varían tiempo y distancia de detención frente a cambios de "
                    "velocidad, tiempo de reacción y frenado?",
        "modelo": "x'(t)=v ; v'(t)=-a  (a constante) → v(t)=v0-a t ; t_det=v0/a ; "
                  "d_frenado=v0²/(2a) ; d_total=v0·t_r+v0²/(2a)",
        "metodos_sem2": "RK2, RK4, trapecio, Simpson, Romberg, bisección, Newton, secante",
        "icono": "🛑",
    },
    "deterioro": {
        "id": 2, "nombre": "Deterioro mecánico y mantenimiento",
        "pregunta": "¿Cuándo alcanzaría un indicador hipotético de deterioro un umbral de inspección?",
        "modelo": "D(t)=D0+α t+β t² ; resolver D(t*)=D_umbral (raíz admisible) ; "
                  "calibración: A x = b con A SPD",
        "metodos_sem2": "bisección, Newton, secante + Jacobi, Gauss-Seidel, LU, CG",
        "icono": "🔧",
    },
    "oscilaciones": {
        "id": 3, "nombre": "Oscilaciones por viento",
        "pregunta": "¿Cómo se modifica la oscilación ante cambios de fuerza externa, "
                    "amortiguamiento y parámetros del modelo?",
        "modelo": "m x'' + c x' + k x = F(t) ; ω0=√(k/m) ; ζ=c/(2√(k m)) ; "
                  "x(t)=e^(-ζω0 t)[C1 cos ωd t + C2 sin ωd t] (F=0)",
        "metodos_sem2": "RK2, RK4, trapecio, Simpson, Romberg",
        "icono": "🌬️",
    },
    "sensores": {
        "id": 4, "nombre": "Reconstrucción de señales de sensores",
        "pregunta": "¿Cómo reconstruir registros faltantes y medir la distorsión que "
                    "producen datos con ruido?",
        "modelo": "y(t)=sin t (o e^-t) muestreada en nodos; puntos retirados; "
                  "interpolantes P(t) de Lagrange, Newton y spline cúbico",
        "metodos_sem2": "Lagrange, Newton (dif. divididas), splines, raíces de cruce de umbral",
        "icono": "📡",
    },
}

ESC_TIPOS = ["NORMAL", "ESTRES", "MAL_CONDICIONADO"]

# ---------------------------------------------------------------------------
# Parámetros por caso y escenario (variables, unidades y fuente declaradas)
# ---------------------------------------------------------------------------
PARAMETROS = {
    "detencion": {
        "unidades": {"v0": "m/s", "a": "m/s²", "t_reac": "s"},
        "NORMAL": {"v0": 5.0, "a": 1.2, "t_reac": 0.5},
        "ESTRES": {"v0": 6.0, "a": 0.6, "t_reac": 1.5},
        "MAL_CONDICIONADO": {"v0": 5.0, "T": 4.0, "eps": 1e-9,
                             "nota": "v(t)=v0(1-t/T)^3: raíz triple en t=T"},
    },
    "deterioro": {
        "unidades": {"D0": "adim.", "alfa": "1/mes", "beta": "1/mes²", "D_umbral": "adim."},
        "NORMAL": {"D0": 0.10, "alfa": 0.004, "beta": 5e-5, "D_umbral": 0.60},
        "ESTRES": {"D0": 0.10, "alfa": 0.006, "beta": 1.5e-4, "D_umbral": 0.60},
        "MAL_CONDICIONADO": {"D0": 0.10, "alfa": 0.02, "beta": -1e-4,
                             "D_umbral": 1.1 - 1e-8,
                             "nota": "umbral casi igual al máximo de D(t): raíz casi doble"},
    },
    "oscilaciones": {
        "unidades": {"m": "kg", "k": "N/m", "zeta": "adim.", "F0": "N", "r": "Ω/ω0 (adim.)"},
        "NORMAL": {"m": 3000.0, "k": 5e4, "zeta": 0.10, "F0": 500.0, "r": 0.50},
        "ESTRES": {"m": 3000.0, "k": 5e4, "zeta": 0.02, "F0": 1500.0, "r": 0.95},
        "MAL_CONDICIONADO": {"m": 3000.0, "k": 5e4, "zeta": 0.999, "F0": 0.0, "r": 0.0,
                             "x0": 0.10, "v0": 0.05,
                             "nota": "ζ→1: ωd→0 y C2=(v0+ζω0x0)/ωd se vuelve sensible"},
    },
    "sensores": {
        "unidades": {"n_nodos": "puntos", "intervalo": "s", "ruido": "adim."},
        "NORMAL": {"n_nodos": 6, "a": 0.0, "b": 2 * math.pi, "ruido": 0.0},
        "ESTRES": {"n_nodos": 12, "a": 0.0, "b": 2 * math.pi, "ruido": 1e-3},
        "MAL_CONDICIONADO": {"n_nodos": 20, "a": 0.0, "b": 10.0, "ruido": 0.0,
                             "nota": "nodos equiespaciados, grado alto"},
    },
}

FUENTE = "Datos sintéticos / parámetros supuestos (uso educativo)"


# ---------------------------------------------------------------------------
# Sistemas lineales del escenario (Módulo 2: calibración SPD) -- semana 1
# ---------------------------------------------------------------------------
def hilbert(n):
    i = np.arange(n)
    return 1.0 / (i[:, None] + i[None, :] + 1.0)


def sistema_lineal(tipo, n=None):
    """Devuelve (A, b, x*, descripcion). b = A x* para conocer la solución exacta."""
    if tipo == "NORMAL":
        A = np.array([[10, -1, 2, 0], [-1, 11, -1, 3],
                      [2, -1, 10, -1], [0, 3, -1, 8]], float)
        xs = np.array([1.0, 2.0, -1.0, 1.0])
        desc = "SPD 4x4 estrictamente diagonal dominante (calibración, 4 coeficientes)"
    elif tipo == "ESTRES":
        n = n or 10
        A = 2 * np.eye(n) - np.eye(n, k=1) - np.eye(n, k=-1)
        xs = np.arange(1, n + 1) / n
        desc = f"SPD {n}x{n} tridiagonal (2,-1): débilmente dominante, κ mayor"
    elif tipo == "MAL_CONDICIONADO":
        n = n or 6
        A = hilbert(n)
        xs = np.ones(n)
        desc = f"Matriz de Hilbert {n}x{n} (SPD, κ≈10^7): normal eq. del ajuste polinomial en [0,1]"
    else:
        raise ValueError(tipo)
    return A, A @ xs, xs, desc


# ---------------------------------------------------------------------------
# Teoría de errores transversal: sensibilidad de las referencias analíticas
# ---------------------------------------------------------------------------
def d_total(v0, a, tr):
    return v0 * tr + v0 ** 2 / (2 * a)


def raiz_umbral(D0, alfa, beta, Du):
    """Menor raíz real positiva de D0+alfa t+beta t^2 = Du (físicamente admisible)."""
    c = D0 - Du
    disc = alfa ** 2 - 4 * beta * c
    if disc < 0:
        return float("nan")
    s = math.sqrt(disc)
    cand = [(-alfa + s) / (2 * beta), (-alfa - s) / (2 * beta)]
    cand = [t for t in cand if t > 0]
    return min(cand) if cand else float("nan")


def amplitud_estacionaria(F0, k, zeta, r):
    return (F0 / k) / math.sqrt((1 - r ** 2) ** 2 + (2 * zeta * r) ** 2)


def coef_C2(zeta, w0, x0, v0):
    wd = w0 * math.sqrt(1 - zeta ** 2)
    return (v0 + zeta * w0 * x0) / wd


def fila(modulo, esc, salida, param, p0, p1, y0, y1):
    de = abs(y1 - y0)
    dp = abs(p1 - p0)
    return {
        "modulo": modulo, "escenario": esc, "salida": salida, "param": param,
        "p0": p0, "p1": p1, "y0": y0, "y1": y1,
        "err_abs": de,
        "err_rel": None if y0 == 0 else de / abs(y0),
        "err_pct": None if y0 == 0 else 100 * de / abs(y0),
        "amp_abs": de / dp if dp else None,
        "kappa": (de / abs(y0)) / (dp / abs(p0)) if (y0 != 0 and p0 != 0 and dp != 0) else None,
    }


def tabla_sensibilidad():
    P = PARAMETROS
    filas = []
    # --- Módulo 1 ---
    p = P["detencion"]["NORMAL"]
    filas.append(fila("1", "NORMAL", "d_total [m]", "v0 (+1 %)", p["v0"], p["v0"] * 1.01,
                      d_total(p["v0"], p["a"], p["t_reac"]),
                      d_total(p["v0"] * 1.01, p["a"], p["t_reac"])))
    p = P["detencion"]["ESTRES"]
    filas.append(fila("1", "ESTRES", "d_total [m]", "a (+1 %)", p["a"], p["a"] * 1.01,
                      d_total(p["v0"], p["a"], p["t_reac"]),
                      d_total(p["v0"], p["a"] * 1.01, p["t_reac"])))
    p = P["detencion"]["MAL_CONDICIONADO"]
    # raíz triple de g(t)=v0(1-t/T)^3 - delta = 0  →  t*(delta)=T(1-(delta/v0)^(1/3))
    d0, d1 = 0.0, p["eps"]
    t0 = p["T"] * (1 - (d0 / p["v0"]) ** (1 / 3))
    t1 = p["T"] * (1 - (d1 / p["v0"]) ** (1 / 3))
    filas.append(fila("1", "MAL_COND.", "t* raíz triple [s]", "δ en v(t) [m/s]", d0, d1, t0, t1))
    # --- Módulo 2 ---
    p = P["deterioro"]["NORMAL"]
    f = lambda al: raiz_umbral(p["D0"], al, p["beta"], p["D_umbral"])
    filas.append(fila("2", "NORMAL", "t* umbral [meses]", "α (+1 %)", p["alfa"], p["alfa"] * 1.01,
                      f(p["alfa"]), f(p["alfa"] * 1.01)))
    p = P["deterioro"]["ESTRES"]
    f = lambda be: raiz_umbral(p["D0"], p["alfa"], be, p["D_umbral"])
    filas.append(fila("2", "ESTRES", "t* umbral [meses]", "β (+1 %)", p["beta"], p["beta"] * 1.01,
                      f(p["beta"]), f(p["beta"] * 1.01)))
    p = P["deterioro"]["MAL_CONDICIONADO"]
    f = lambda du: raiz_umbral(p["D0"], p["alfa"], p["beta"], du)
    du0, du1 = p["D_umbral"], p["D_umbral"] * (1 + 1e-10)
    filas.append(fila("2", "MAL_COND.", "t* umbral [meses]", "D_umbral (+1e-8 %)", du0, du1,
                      f(du0), f(du1)))
    # --- Módulo 3 ---
    p = P["oscilaciones"]["NORMAL"]
    f = lambda r: amplitud_estacionaria(p["F0"], p["k"], p["zeta"], r)
    filas.append(fila("3", "NORMAL", "amplitud X [m]", "r=Ω/ω0 (+1 %)", p["r"], p["r"] * 1.01,
                      f(p["r"]), f(p["r"] * 1.01)))
    p = P["oscilaciones"]["ESTRES"]
    f = lambda r: amplitud_estacionaria(p["F0"], p["k"], p["zeta"], r)
    filas.append(fila("3", "ESTRES", "amplitud X [m]", "r=Ω/ω0 (+1 %)", p["r"], p["r"] * 1.01,
                      f(p["r"]), f(p["r"] * 1.01)))
    p = P["oscilaciones"]["MAL_CONDICIONADO"]
    w0 = math.sqrt(p["k"] / p["m"])
    f = lambda z: coef_C2(z, w0, p["x0"], p["v0"])
    filas.append(fila("3", "MAL_COND.", "C2 libre [m]", "ζ (+0.01 %)", p["zeta"], p["zeta"] * 1.0001,
                      f(p["zeta"]), f(p["zeta"] * 1.0001)))
    # --- Módulo 4 (evaluación de sin t) ---
    for esc, t in (("NORMAL", 1.0), ("ESTRES", 2.5), ("MAL_COND.", math.pi - 1e-6)):
        d = 1e-8 if esc == "MAL_COND." else 1e-2
        filas.append(fila("4", esc, "y=sin t", f"t (+{d*100:g} %)", t, t * (1 + d),
                          math.sin(t), math.sin(t * (1 + d))))
    return filas


def tabla_vandermonde():
    """Mód. 4: condicionamiento de V (matriz del interpolante en la base monomial)
    para nodos equiespaciados y de Chebyshev; amplificación de una perturbación en y."""
    filas = []
    rng = np.random.default_rng(2026)
    for esc, n, a, b in (("NORMAL", 6, 0, 2 * math.pi), ("ESTRES", 12, 0, 2 * math.pi),
                         ("MAL_COND.", 20, 0, 10.0)):
        for tipo in ("equiespaciados", "Chebyshev"):
            if tipo == "equiespaciados":
                t = np.linspace(a, b, n)
            else:
                k = np.arange(n)
                t = 0.5 * (a + b) + 0.5 * (b - a) * np.cos((2 * k + 1) * math.pi / (2 * n))
            V = np.vander(t, increasing=True)
            y = np.sin(t)
            c0 = np.linalg.solve(V, y)
            dy = 1e-6 * rng.standard_normal(n)
            c1 = np.linalg.solve(V, y + dy)
            amp = (np.linalg.norm(c1 - c0) / np.linalg.norm(c0)) / (np.linalg.norm(dy) / np.linalg.norm(y))
            filas.append({"escenario": esc, "n": n, "nodos": tipo,
                          "kappa": float(np.linalg.cond(V)), "amplificacion": float(amp)})
    return filas
