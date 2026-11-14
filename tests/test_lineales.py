import numpy as np
import pytest
from simtele import lineales as L, modelos as M, errores as E


@pytest.mark.parametrize("tipo", M.ESC_TIPOS)
def test_directo_y_lu_recuperan_x_ref(tipo):
    A, b, xs, _ = M.sistema_lineal(tipo)
    assert np.allclose(L.referencia_directa(A, b), xs, rtol=1e-6 if tipo == "MAL_CONDICIONADO" else 1e-12)
    out = L.lu_solve(A, b, x_ref=xs)
    assert np.allclose(out["L"] @ out["U"], A)
    assert E.error_rel(out["x"], xs) < (1e-7 if tipo == "MAL_CONDICIONADO" else 1e-12)


def test_normal_todos_convergen():
    A, b, xs, _ = M.sistema_lineal("NORMAL")
    r = L.ejecutar_todos(A, b, xs, tol=1e-10)
    for m in ("Jacobi", "Gauss-Seidel", "LU", "Gradiente conjugado"):
        assert r[m]["convergio"], m
        assert E.error_rel(r[m]["x"], xs) < 1e-9
    assert r["Gradiente conjugado"]["iteraciones"] <= 4        # n=4 → ≤ 4 pasos exactos


def test_cg_exacto_en_n_pasos_estres():
    A, b, xs, _ = M.sistema_lineal("ESTRES")
    out = L.gradiente_conjugado(A, b, x_ref=xs, tol=1e-12)
    assert out["convergio"] and out["iteraciones"] <= 10


def test_mal_condicionado_distingue_kappa_de_no_convergencia():
    A, b, xs, _ = M.sistema_lineal("MAL_CONDICIONADO")
    d = L.diagnostico(A)
    assert d["spd"] and d["kappa2"] > 1e7 and d["rho_jacobi"] > 1     # Jacobi diverge
    r = L.ejecutar_todos(A, b, xs, tol=1e-10, max_iter=2000)
    assert not r["Jacobi"]["convergio"]
    # residual pequeño NO implica error pequeño: error ≈ κ · residual relativo
    cg = r["Gradiente conjugado"]
    assert E.error_rel(cg["x"], xs) > 100 * E.residual_rel(A, cg["x"], b)
    assert E.error_rel(cg["x"], xs) <= E.cota_error_por_residual(A, cg["x"], b) * 1.0001


def test_cg_rechaza_matriz_no_spd():
    A = np.array([[1., 2.], [2., 1.]])      # simétrica, indefinida
    with pytest.raises(ValueError):
        L.gradiente_conjugado(A, np.ones(2))


def test_errores_sin_division_por_cero():
    assert E.error_rel(np.array([1.0]), np.array([0.0])) is None
    assert E.error_pct(np.array([1.0]), np.array([0.0])) is None
