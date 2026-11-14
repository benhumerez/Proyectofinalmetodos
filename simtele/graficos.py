"""Gráficos PNG generados SOLO a partir de lo recuperado de la BD (sin estado en memoria)."""
import io
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def convergencia(sim):
    """Residual y error relativo vs iteración para los métodos iterativos guardados."""
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.3))
    hay = False
    for ej in sim["ejecuciones"]:
        its = ej["iteraciones"]
        if len(its) < 3:
            continue
        k = [i["numero"] for i in its]
        res = [i["residual"] for i in its]
        err = [i["error_rel"] for i in its]
        ax[0].semilogy(k, res, label=ej["metodo"])
        ax[1].semilogy(k, [e if e and e > 0 else np.nan for e in err], label=ej["metodo"])
        hay = True
    for a, t in zip(ax, ("Residual ‖b − Ax‖", "Error relativo vs x*")):
        a.set_xlabel("iteración")
        a.set_title(t, fontsize=10)
        a.grid(alpha=.3)
    if hay:
        ax[0].legend(fontsize=7)
    else:
        ax[0].text(.5, .5, "Sin métodos iterativos", ha="center", transform=ax[0].transAxes)
    return _png(fig)


def curva(sim):
    p, caso, tipo = sim["params"], sim["caso_clave"], sim["tipo"]
    fig, ax = plt.subplots(figsize=(6, 3.3))
    if caso == "detencion":
        if tipo == "MAL_CONDICIONADO":
            t = np.linspace(0, p["T"], 200)
            ax.plot(t, p["v0"] * (1 - t / p["T"]) ** 3)
            ax.set(xlabel="t [s]", ylabel="v [m/s]", title="v(t) con raíz triple en t=T")
        else:
            td = p["v0"] / p["a"]
            t = np.linspace(0, td, 200)
            ax.plot(t, p["v0"] - p["a"] * t, label="v(t) [m/s]")
            ax.plot(t, p["v0"] * t - p["a"] * t ** 2 / 2, label="x(t) frenado [m]")
            ax.set(xlabel="t [s]", title="Detención con a constante (referencia analítica)")
            ax.legend()
    elif caso == "deterioro":
        from .modelos import raiz_umbral
        ts = raiz_umbral(p["D0"], p["alfa"], p["beta"], p["D_umbral"])
        t = np.linspace(0, 1.4 * ts, 300)
        ax.plot(t, p["D0"] + p["alfa"] * t + p["beta"] * t ** 2, label="D(t)")
        ax.axhline(p["D_umbral"], color="r", ls="--", label="umbral")
        ax.axvline(ts, color="g", ls=":", label=f"t*={ts:.2f} meses")
        ax.set(xlabel="t [meses]", ylabel="D (adim.)", title="Deterioro hipotético")
        ax.legend()
    elif caso == "oscilaciones":
        w0 = math.sqrt(p["k"] / p["m"])
        z = p["zeta"]
        wd = w0 * math.sqrt(1 - z ** 2)
        x0, v0 = p.get("x0", 0.1), p.get("v0", 0.0)
        t = np.linspace(0, 6 * math.pi / max(wd, 1e-9) if z < .99 else 30, 600)
        x = np.exp(-z * w0 * t) * (x0 * np.cos(wd * t) + (v0 + z * w0 * x0) / wd * np.sin(wd * t))
        ax.plot(t, x)
        ax.set(xlabel="t [s]", ylabel="x [m]", title="Vibración libre (referencia analítica)")
    else:
        n, a, b = int(p["n_nodos"]), p["a"], p["b"]
        tt = np.linspace(a, b, 400)
        ax.plot(tt, np.sin(tt), label="y=sin t")
        tn = np.linspace(a, b, n)
        ax.plot(tn, np.sin(tn), "o", label=f"{n} nodos")
        ax.set(xlabel="t [s]", title="Señal sintética y nodos")
        ax.legend()
    ax.grid(alpha=.3)
    return _png(fig)
