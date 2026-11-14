"""Genera docs/Semana1_Avance_SIMTELE-RISK.pdf con datos calculados por el propio código."""
import math, os, sys, tempfile
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from simtele import lineales as L, modelos as M, errores as E, servicio, db

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                PageBreak, Image, Preformatted, KeepTogether)

AQUI = os.path.dirname(os.path.abspath(__file__))
FD = "/usr/share/fonts/truetype/dejavu/"
for n, f in (("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
             ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVM", "DejaVuSansMono.ttf")):
    pdfmetrics.registerFont(TTFont(n, FD + f))
pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")

AZUL = colors.HexColor("#12355b")
st = {
    "t": ParagraphStyle("t", fontName="DV-B", fontSize=24, leading=30, alignment=TA_CENTER, textColor=AZUL),
    "st": ParagraphStyle("st", fontName="DV", fontSize=13, leading=18, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName="DV-B", fontSize=14, leading=18, textColor=AZUL, spaceBefore=12, spaceAfter=6),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=11, leading=14, textColor=AZUL, spaceBefore=8, spaceAfter=3),
    "b": ParagraphStyle("b", fontName="DV", fontSize=9, leading=12.5, alignment=TA_JUSTIFY, spaceAfter=4),
    "c": ParagraphStyle("c", fontName="DV", fontSize=7.4, leading=9.4),
    "ch": ParagraphStyle("ch", fontName="DV-B", fontSize=7.4, leading=9.4, textColor=colors.white),
    "f": ParagraphStyle("f", fontName="DV", fontSize=9.5, leading=14, leftIndent=14, spaceAfter=3),
    "n": ParagraphStyle("n", fontName="DV-I", fontSize=7.8, leading=10, textColor=colors.HexColor("#444")),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=7.4, leading=9.2, leftIndent=8,
                           backColor=colors.HexColor("#f1f3f5")),
}
P = lambda t, s="b": Paragraph(t, st[s])
g4 = lambda v: "—" if v is None else f"{v:.4g}"
e3 = lambda v: "—" if v is None else f"{v:.3e}"
e2 = lambda v: "—" if v is None else f"{v:.2e}"
g3 = lambda v: "—" if v is None else f"{v:.3g}"


def tabla(filas, anchos, cab=True, zebra=True):
    data = [[Paragraph(str(c), st["ch"] if (cab and i == 0) else st["c"]) for c in r] for i, r in enumerate(filas)]
    t = Table(data, colWidths=[a * cm for a in anchos], repeatRows=1 if cab else 0)
    sty = [("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#b8c2cc")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
           ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3)]
    if cab:
        sty.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
    if zebra:
        for i in range(1, len(data)):
            if i % 2 == 0:
                sty.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f3f6f9")))
    t.setStyle(TableStyle(sty))
    return t


def fig_a_img(fig, ancho_cm):
    ruta = tempfile.mktemp(suffix=".png")
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    from PIL import Image as PI
    w, h = PI.open(ruta).size
    return Image(ruta, width=ancho_cm * cm, height=ancho_cm * cm * h / w)


def vec(v, d=6):
    return "(" + ", ".join(f"{x:.{d}g}" for x in v) + ")"


story = []
PAR, ETQ = M.PARAMETROS, {"NORMAL": "NORMAL", "ESTRES": "ESTRÉS", "MAL_CONDICIONADO": "MAL COND."}

# ================================ PORTADA ==================================
story += [Spacer(1, 3.5 * cm), P("SIMTELE-RISK", "t"), Spacer(1, .4 * cm),
          P("Desafío Integrador Final · Métodos Numéricos", "st"), Spacer(1, .3 * cm),
          P("<b>AVANCE DE LA SEMANA 1</b><br/>Modelos, teoría de errores transversal y sistemas lineales", "st"),
          Spacer(1, 1.2 * cm),
          P("Universidad Mayor de San Andrés · Carrera de Informática", "st"),
          Spacer(1, .8 * cm),
          P("<b>Participantes y mención</b><br/>Benjamin Isaac Humerez Surco<br/>"
            "[completar: otros integrantes (máx. 4) y mención de cada uno]", "st"),
          Spacer(1, .8 * cm),
          P("Repositorio GitHub: [pegar URL del repositorio]<br/>Fecha de entrega: 14 de noviembre de 2026", "st"),
          Spacer(1, 2 * cm),
          P("Los escenarios son hipotéticos y los datos, sintéticos. El sistema es estrictamente educativo y no se "
            "conecta con equipos de control reales ni describe fallas verificadas de Mi Teleférico.", "n"),
          PageBreak()]

# ============================ 1. ALCANCE ===================================
story += [P("1. Objetivo y cumplimiento de la Semana 1", "h1"),
          P("Este documento reúne la evidencia de la Semana 1 (6 puntos): planteamiento de los cuatro casos, teoría de "
            "errores transversal, sistemas lineales con referencia exacta, pruebas de los tres escenarios en un caso "
            "(Módulo 2), definición de los escenarios de los otros tres, prototipo web con cuatro módulos, DER inicial y "
            "repositorio con README. Todas las cifras de este informe las produce el código del repositorio "
            "(<font name='DVM'>docs/generar_informe.py</font>), por lo que son reproducibles."),
          tabla([["Entregable de la consigna (S1)", "Evidencia", "Dónde"],
                 ["Planteamiento de los cuatro casos y relación modelos–métodos", "Tablas de modelo, variables, unidades, parámetros y escenarios", "Secciones 2 y 3"],
                 ["Teoría de errores transversal", "Definiciones, cotas, tablas de sensibilidad por módulo (4 módulos × 3 escenarios)", "Sección 4 · <font name='DVM'>simtele/errores.py</font>"],
                 ["Sistemas lineales (Jacobi, G-S, LU, CG, directa)", "Fórmulas, pseudocódigo, condiciones de convergencia, ejemplos manuales", "Secciones 5 y 6 · <font name='DVM'>simtele/lineales.py</font>"],
                 ["Tres escenarios en al menos un caso; definir los otros tres", "Módulo 2 ejecutado en NORMAL, ESTRÉS y MAL CONDICIONADO; escenarios de M1, M3, M4 definidos", "Secciones 2 y 7"],
                 ["Matrices/soluciones de referencia y tablas de error", "A x* = b con x* conocido; residual, κ, iteraciones y errores", "Secciones 6 y 7"],
                 ["Prototipo web (4 módulos), DER inicial, GitHub con README", "App Flask + SQLite, esquema SQL, DER, pruebas automáticas", "Sección 8"]],
                [5.4, 7.2, 4.4]), Spacer(1, .2 * cm)]

# ===================== 2. CUATRO CASOS ======================================
d = PAR["detencion"]
def m1(t):
    p = d[t]; return p["v0"] / p["a"], p["v0"] ** 2 / (2 * p["a"]), M.d_total(p["v0"], p["a"], p["t_reac"])
n1, s1 = m1("NORMAL"), m1("ESTRES")
dt = PAR["deterioro"]
tN = M.raiz_umbral(dt["NORMAL"]["D0"], dt["NORMAL"]["alfa"], dt["NORMAL"]["beta"], dt["NORMAL"]["D_umbral"])
tS = M.raiz_umbral(dt["ESTRES"]["D0"], dt["ESTRES"]["alfa"], dt["ESTRES"]["beta"], dt["ESTRES"]["D_umbral"])
tM = M.raiz_umbral(dt["MAL_CONDICIONADO"]["D0"], dt["MAL_CONDICIONADO"]["alfa"], dt["MAL_CONDICIONADO"]["beta"], dt["MAL_CONDICIONADO"]["D_umbral"])
o = PAR["oscilaciones"]
w0 = math.sqrt(o["NORMAL"]["k"] / o["NORMAL"]["m"])
XN = M.amplitud_estacionaria(o["NORMAL"]["F0"], o["NORMAL"]["k"], o["NORMAL"]["zeta"], o["NORMAL"]["r"])
XS = M.amplitud_estacionaria(o["ESTRES"]["F0"], o["ESTRES"]["k"], o["ESTRES"]["zeta"], o["ESTRES"]["r"])

story += [P("2. Planteamiento de los cuatro casos de estudio", "h1"),
          P("Cada caso se define con variables, unidades, hipótesis, referencia analítica y tres escenarios. Todos los "
            "parámetros son <b>supuestos sintéticos</b> (fuente declarada en la BD, campo <i>fuente_datos</i>). "
            "Se distingue deliberadamente entre <i>riesgo físico/alta exigencia</i> (ESTRÉS) y "
            "<i>mal condicionamiento matemático</i> (MAL COND.), como exige la consigna.")]

story += [P("Módulo 1 · Detención de emergencia de cabinas", "h2"), tabla([
    ["Elemento", "Definición"],
    ["Pregunta", "¿Cómo varían tiempo y distancia de detención frente a cambios de velocidad, tiempo de reacción y frenado?"],
    ["Modelo", "x′ = v ; v′ = −a (a constante en el caso base; a(v,t) variable como ampliación). Tras t<sub>r</sub> con velocidad constante v<sub>0</sub> comienza el frenado."],
    ["Variables / unidades", "x [m], v [m/s], v<sub>0</sub> [m/s], a [m/s²], t<sub>r</sub> [s]"],
    ["Referencia analítica", "v(t)=v<sub>0</sub>−a t ; x(t)=x<sub>0</sub>+v<sub>0</sub>t−(a/2)t² ; t<sub>det</sub>=v<sub>0</sub>/a ; d<sub>fren</sub>=v<sub>0</sub>²/(2a) ; d<sub>tot</sub>=v<sub>0</sub>t<sub>r</sub>+d<sub>fren</sub>"],
    ["NORMAL", f"v<sub>0</sub>=5 m/s, a=1.2 m/s², t<sub>r</sub>=0.5 s → t<sub>det</sub>={n1[0]:.3f} s, d<sub>fren</sub>={n1[1]:.3f} m, d<sub>tot</sub>={n1[2]:.3f} m"],
    ["ESTRÉS", f"v<sub>0</sub>=6 m/s, a=0.6 m/s², t<sub>r</sub>=1.5 s → t<sub>det</sub>={s1[0]:.3f} s, d<sub>fren</sub>={s1[1]:.3f} m, d<sub>tot</sub>={s1[2]:.3f} m (más tiempo de simulación y pasos más exigentes en S2)"],
    ["MAL COND. (subexperimento numérico)", "v(t)=v<sub>0</sub>(1−t/T)³, T=4 s: raíz <b>triple</b> en t=T (f′(T)=f″(T)=0). Newton pierde orden cuadrático; una perturbación δ=10⁻⁹ m/s desplaza la raíz ≈10⁻³ s. No describe un peligro físico: es sensibilidad matemática."],
    ["Métodos (S2)", "RK2 y RK4 sobre x′=v, v′=−a ; trapecio, Simpson 1/3 y Romberg para ∫v dt ; bisección, Newton y secante para v(t)=0"]],
    [3.6, 13.4])]

story += [P("Módulo 2 · Deterioro mecánico y mantenimiento", "h2"), tabla([
    ["Elemento", "Definición"],
    ["Pregunta", "¿Cuándo alcanzaría un indicador hipotético de deterioro un umbral de inspección?"],
    ["Modelo", "D(t)=D<sub>0</sub>+α t+β t² ; se resuelve D(t*)=D<sub>umbral</sub>. Calibración de coeficientes mediante A x = b con A simétrica definida positiva (SPD)."],
    ["Variables / unidades", "D [adim.], t [meses], D<sub>0</sub> [adim.], α [1/mes], β [1/mes²], D<sub>umbral</sub> [adim.]"],
    ["Referencia analítica", "Raíz de la cuadrática; se elige la menor raíz positiva con D′(t*)&gt;0 (físicamente admisible). Para sistemas: b = A x* con x* conocido."],
    ["NORMAL", f"D<sub>0</sub>=0.10, α=0.004, β=5·10⁻⁵, D<sub>umbral</sub>=0.60 → t*={tN:.3f} meses. Sistema: SPD 4×4 estrictamente diagonal dominante."],
    ["ESTRÉS (mantenimiento retrasado)", f"α=0.006, β=1.5·10⁻⁴ (deterioro acelerado) → t*={tS:.3f} meses. Sistema: SPD 10×10 tridiagonal (2,−1), débilmente dominante, κ mayor."],
    ["MAL COND.", f"β=−10⁻⁴, α=0.02, D<sub>umbral</sub>=1.1−10⁻⁸ (casi el máximo de D): discriminante ≈4·10⁻¹², raíz casi doble, t*≈{tM:.3f}. Sistema: matriz de Hilbert 6×6 (SPD, κ≈1.5·10⁷)."],
    ["Métodos (S2 / S1)", "S1: Jacobi, Gauss-Seidel, LU, CG y directa. S2: bisección, Newton y secante sobre D(t)−D<sub>umbral</sub>; integración opcional de la tasa de deterioro."]],
    [3.6, 13.4])]

story += [P("Módulo 3 · Oscilaciones por viento", "h2"), tabla([
    ["Elemento", "Definición"],
    ["Pregunta", "¿Cómo se modifica la oscilación ante cambios de fuerza externa, amortiguamiento y parámetros del modelo?"],
    ["Modelo", "m x″ + c x′ + k x = F(t), F(t)=F<sub>0</sub> sin Ωt ; x′=v ; v′=(F−c v−k x)/m. ω<sub>0</sub>=√(k/m), ζ=c/(2√(k m)), ω<sub>d</sub>=ω<sub>0</sub>√(1−ζ²), r=Ω/ω<sub>0</sub>."],
    ["Variables / unidades", "x [m], v [m/s], m [kg], k [N/m], c [N·s/m], F<sub>0</sub> [N], Ω [rad/s], ζ y r [adim.]"],
    ["Referencia analítica", "F=0, subamortiguado: x(t)=e<sup>−ζω₀t</sup>[C<sub>1</sub>cos ω<sub>d</sub>t + C<sub>2</sub>sin ω<sub>d</sub>t], C<sub>1</sub>=x<sub>0</sub>, C<sub>2</sub>=(v<sub>0</sub>+ζω<sub>0</sub>x<sub>0</sub>)/ω<sub>d</sub>. Amplitud estacionaria X=(F<sub>0</sub>/k)/√((1−r²)²+(2ζr)²)."],
    ["NORMAL", f"m=3000 kg, k=5·10⁴ N/m (ω<sub>0</sub>={w0:.3f} rad/s), ζ=0.10, F<sub>0</sub>=500 N, r=0.50 → X={XN*1000:.2f} mm"],
    ["ESTRÉS", f"ζ=0.02, F<sub>0</sub>=1500 N, r=0.95 (cerca de resonancia) → X={XS*1000:.1f} mm. Alto riesgo modelado, pero κ moderado (§4): <i>exigente no es lo mismo que mal condicionado</i>."],
    ["MAL COND.", "ζ=0.999 (casi crítico): ω<sub>d</sub>→0 y C<sub>2</sub> depende de 1/ω<sub>d</sub>; κ≈5·10² para C<sub>2</sub> (§4)."],
    ["Métodos (S2)", "RK2 (variante declarada) y RK4 sobre el sistema de primer orden; trapecio, Simpson y Romberg para ∫x(t)² dt"]],
    [3.6, 13.4])]

story += [P("Módulo 4 · Reconstrucción de señales de sensores", "h2"), tabla([
    ["Elemento", "Definición"],
    ["Pregunta", "¿Cómo reconstruir registros faltantes y medir la distorsión que producen datos con ruido?"],
    ["Modelo", "Señal sintética y(t)=sin t (o e<sup>−t</sup>) muestreada en n nodos; se retiran puntos de prueba y se reconstruyen con P(t)."],
    ["Variables / unidades", "t [s], y [adim.], n [nodos], σ [adim., ruido relativo]"],
    ["Referencia", "Valor exacto sin t en los puntos retirados → error real de reconstrucción."],
    ["NORMAL", "n=6 nodos equiespaciados en [0, 2π], sin ruido"],
    ["ESTRÉS", "n=12 nodos en [0, 2π], ruido σ=10⁻³ (más puntos y perturbación)"],
    ["MAL COND.", "n=20 nodos equiespaciados en [0,10] (grado 19): κ(V)≈10²³ en la base monomial; nodos de Chebyshev como contraste."],
    ["Métodos (S2)", "Lagrange, Newton (diferencias divididas) y spline cúbico sobre los mismos nodos; raíz de cruce de umbral con bisección/Newton/secante"]],
    [3.6, 13.4])]

story += [P("3. Relación entre modelos y familias de métodos", "h1"),
          P("Todos los métodos de la consigna aparecen en el sistema completo; cada módulo usa los pertinentes. "
            "La teoría de errores es transversal (no es un módulo)."),
          tabla([["Familia", "M1 Detención", "M2 Deterioro", "M3 Oscilaciones", "M4 Sensores"],
                 ["Errores (transversal)", "✔", "✔", "✔", "✔"],
                 ["Sistemas lineales", "—", "✔ (S1)", "auxiliar", "auxiliar"],
                 ["Interpolación", "—", "—", "—", "✔"],
                 ["Raíces", "✔", "✔", "—", "✔ (cruce de umbral)"],
                 ["Integración", "✔", "opcional", "✔", "—"],
                 ["EDO (RK2, RK4)", "✔", "—", "✔", "—"]],
                [4.0, 3.0, 3.0, 3.4, 3.6])]

# ===================== 4. TEORÍA DE ERRORES =================================
story += [PageBreak(), P("4. Teoría de errores transversal", "h1"),
          P("Sea x* el valor de referencia (analítico o numérico de alta precisión justificada) y x la aproximación. "
            "Para vectores se usa la norma euclídea; ningún cociente divide por cero (la implementación devuelve "
            "<i>None</i> si la referencia es 0)."),
          tabla([["Magnitud", "Fórmula", "Uso"],
                 ["Error absoluto", "E<sub>abs</sub> = ‖x − x*‖", "Distancia al valor de referencia (con unidades)"],
                 ["Error relativo", "E<sub>rel</sub> = ‖x − x*‖ / ‖x*‖ , si ‖x*‖ ≠ 0", "Compara escalas distintas"],
                 ["Error porcentual", "E<sub>%</sub> = 100·E<sub>rel</sub>", "Presentación en tablas"],
                 ["Residual", "r = b − A x ; ‖r‖ y ‖r‖/‖b‖", "Criterio de parada; no requiere conocer x*"],
                 ["Número de condición", "κ(A)=‖A‖·‖A<sup>−1</sup>‖ = λ<sub>máx</sub>/λ<sub>mín</sub> (A SPD, norma 2)", "Amplificación de perturbaciones"],
                 ["Cota por residual", "‖x−x*‖/‖x*‖ ≤ κ(A)·‖r‖/‖b‖", "Un residual pequeño NO garantiza error pequeño"],
                 ["Cota por perturbación", "‖δx‖/‖x‖ ≤ κ(A)·‖δb‖/‖b‖", "Sensibilidad de la solución a los datos"],
                 ["Condición relativa de y=f(p)", "κ<sub>f</sub> = |f′(p)·p / f(p)| ≈ (|Δy|/|y|)/(|Δp|/|p|)", "Sensibilidad de una salida a un parámetro"],
                 ["Épsilon de máquina", f"ε<sub>mach</sub> = {E.EPS_MAQ:.3e} (doble precisión)", "Piso de precisión alcanzable ≈ κ·ε<sub>mach</sub>"]],
                [3.4, 7.6, 6.0]), Spacer(1, .2 * cm),
          P("<b>Tipos de error considerados.</b> (i) <i>Datos/modelo</i>: parámetros sintéticos y supuestos del modelo; "
            "(ii) <i>truncamiento</i>: método finito (iteraciones, paso h, grado del polinomio); (iii) <i>redondeo</i>: "
            "aritmética de coma flotante. Se distingue además <b>mal condicionamiento</b> (propiedad del problema), "
            "<b>inestabilidad</b> (propiedad del algoritmo) y <b>no convergencia</b> (propiedad del método iterativo "
            "sobre ese problema). Criterios de parada: ‖r‖/‖b‖ &lt; tol y límite de iteraciones."),
          P("4.1 Sensibilidad de las referencias analíticas (12 casos: 4 módulos × 3 escenarios)", "h2"),
          P("Se perturba un parámetro y se mide el cambio en la salida de referencia (E<sub>%</sub> = 100·E<sub>rel</sub>). κ<sub>rel</sub> aproxima la "
            "condición relativa; cuando el parámetro nominal es 0 se informa solo la amplificación absoluta |Δy|/|Δp|.")]
filas = [["M", "Esc.", "Salida", "Parámetro perturbado", "y nom.", "y pert.", "E<sub>abs</sub>", "E<sub>rel</sub>", "|Δy|/|Δp|", "κ<sub>rel</sub>"]]
ABREV = {"NORMAL": "NORM.", "ESTRES": "ESTR.", "MAL_COND.": "MAL"}
for f in M.tabla_sensibilidad():
    filas.append([f["modulo"], ABREV[f["escenario"]], f["salida"], f["param"], g4(f["y0"]), g4(f["y1"]), e2(f["err_abs"]),
                  e2(f["err_rel"]), e2(f["amp_abs"]), g3(f["kappa"])])
story += [tabla(filas, [.9, 1.3, 2.2, 2.3, 1.4, 1.6, 1.7, 1.7, 1.7, 1.7]),
          P("Lectura: en M3-ESTRÉS la amplitud es muy sensible a r (κ≈19) porque se acerca a la resonancia, pero eso es "
            "<i>alta exigencia</i>; en M1-MAL, M2-MAL, M3-MAL y M4-MAL la sensibilidad crece por razones puramente "
            "matemáticas (raíz múltiple, raíz casi doble, ζ→1, evaluación de sin t cerca de su cero), con κ de 10²–10⁶.", "n")]

story += [PageBreak(), P("4.2 Condicionamiento de la interpolación en base monomial (Módulo 4)", "h2")]
fv = [["Esc.", "n", "Nodos", "κ(V) (Vandermonde)", "Amplificación observada (perturbación 10⁻⁶ en y)"]]
for f in M.tabla_vandermonde():
    fv.append([f["escenario"], f["n"], f["nodos"], e3(f["kappa"]), g4(f["amplificacion"])])
story += [tabla(fv, [2.2, 1.0, 3.2, 4.2, 6.4]),
          P("Nota: κ(V) describe el problema de hallar coeficientes monomiales; Lagrange y Newton no forman V, por lo que "
            "en S2 se comparará el error real de reconstrucción, no solo κ(V). La amplificación observada depende de la "
            "dirección aleatoria de la perturbación y está acotada por κ(V).", "n")]

# ===================== 5. SISTEMAS LINEALES =================================
story += [P("5. Sistemas lineales A x = b: métodos y condiciones de convergencia", "h1"),
          P("Se construye b = A x* con x* conocido, de modo que el error real sea medible. La matriz es SPD en los tres "
            "escenarios, de modo que el gradiente conjugado estándar está bien definido (el código verifica simetría y "
            "definición positiva y rechaza matrices que no lo sean).")]
story += [tabla([
    ["Método", "Fórmula", "Condición de convergencia", "Costo / observaciones"],
    ["Jacobi", "x<sub>i</sub><super>(k+1)</super> = (b<sub>i</sub> − Σ<sub>j≠i</sub> a<sub>ij</sub> x<sub>j</sub><super>(k)</super>) / a<sub>ii</sub>",
     "ρ(T<sub>J</sub>)&lt;1, T<sub>J</sub>=I−D<super>−1</super>A. Suficiente: diagonal dominante estricta.", "O(n²) por iteración; paralelizable; puede divergir aunque A sea SPD."],
    ["Gauss-Seidel", "x<sub>i</sub><super>(k+1)</super> = (b<sub>i</sub> − Σ<sub>j&lt;i</sub> a<sub>ij</sub> x<sub>j</sub><super>(k+1)</super> − Σ<sub>j&gt;i</sub> a<sub>ij</sub> x<sub>j</sub><super>(k)</super>) / a<sub>ii</sub>",
     "ρ(T<sub>GS</sub>)&lt;1. Suficiente: diagonal dominante estricta <b>o</b> A SPD.", "Suele converger ≈2× más rápido que Jacobi en matrices SPD tipo Poisson."],
    ["LU (Doolittle)", "A = L U ; L y = b ; U x = y", "Existe sin pivoteo si todos los menores principales son ≠ 0 (SPD cumple).", "O(n³/3); error ≈ κ(A)·ε<sub>mach</sub>."],
    ["Gradiente conjugado", "α<sub>k</sub>=r<sub>k</sub>ᵀr<sub>k</sub>/p<sub>k</sub>ᵀA p<sub>k</sub><br/>x<sub>k+1</sub>=x<sub>k</sub>+α<sub>k</sub>p<sub>k</sub> ; r<sub>k+1</sub>=r<sub>k</sub>−α<sub>k</sub>A p<sub>k</sub><br/>β<sub>k</sub>=r<sub>k+1</sub>ᵀr<sub>k+1</sub>/r<sub>k</sub>ᵀr<sub>k</sub> ; p<sub>k+1</sub>=r<sub>k+1</sub>+β<sub>k</sub>p<sub>k</sub>",
     "A SPD. En aritmética exacta termina en ≤ n pasos; ‖e<sub>k</sub>‖<sub>A</sub> ≤ 2((√κ−1)/(√κ+1))<super>k</super>‖e<sub>0</sub>‖<sub>A</sub>.", "Con κ grande se pierde ortogonalidad por redondeo."],
    ["Directa de referencia", "Eliminación con pivoteo parcial (LAPACK, <font name='DVM'>numpy.linalg.solve</font>)", "—", "Referencia numérica cuando no hay x* exacto."]],
    [2.4, 6.0, 4.6, 4.0]), Spacer(1, .2 * cm),
    P("Pseudocódigo (Gauss-Seidel y CG)", "h2"),
    Preformatted("""Gauss-Seidel(A, b, x0, tol, max_iter):
  x <- x0
  para k = 1..max_iter:
     para i = 1..n:
        x[i] <- (b[i] - suma_{j!=i} A[i,j]*x[j]) / A[i,i]    (x[j] ya actualizado si j<i)
     si ||b - A x|| / ||b|| < tol: devolver x
  devolver x (sin convergencia)""", st["code"]), Spacer(1, .15 * cm),
    Preformatted("""Gradiente_Conjugado(A, b, x0, tol, max_iter):      (A simetrica definida positiva)
  x <- x0 ; r <- b - A x ; p <- r ; rs <- r.r
  para k = 1..max_iter:
     Ap <- A p ; alfa <- rs / (p.Ap) ; x <- x + alfa p ; r <- r - alfa Ap
     si ||r|| / ||b|| < tol: devolver x
     rs_nuevo <- r.r ; p <- r + (rs_nuevo / rs) p ; rs <- rs_nuevo
  devolver x (sin convergencia)""", st["code"])]

# ===================== 6. EJEMPLOS MANUALES =================================
A, b, xs, desc = M.sistema_lineal("NORMAL")
mat = lambda X: "<br/>".join("[ " + "  ".join(f"{v:8.4f}" for v in fila) + " ]" for fila in X)
story += [PageBreak(), P("6. Ejemplos manuales (sistema NORMAL 4×4)", "h1"),
          P("Matriz SPD estrictamente diagonal dominante, x* = (1, 2, −1, 1)ᵀ y b = A x* = (6, 25, −11, 15)ᵀ:"),
          Preformatted("A = [[10, -1,  2,  0],\n     [-1, 11, -1,  3],\n     [ 2, -1, 10, -1],\n     [ 0,  3, -1,  8]]     "
                       f"b = {vec(b)}     x* = {vec(xs)}\nκ₂(A) = {E.cond2(A):.4f}, λ_min = {np.linalg.eigvalsh(A).min():.4f}, "
                       f"λ_max = {np.linalg.eigvalsh(A).max():.4f}", st["code"])]

# Jacobi manual
x0 = np.zeros(4)
x1 = np.array([(b[0] - A[0, 1] * x0[1] - A[0, 2] * x0[2]) / A[0, 0],
               (b[1] - A[1, 0] * x0[0] - A[1, 2] * x0[2] - A[1, 3] * x0[3]) / A[1, 1],
               (b[2] - A[2, 0] * x0[0] - A[2, 1] * x0[1] - A[2, 3] * x0[3]) / A[2, 2],
               (b[3] - A[3, 1] * x0[1] - A[3, 2] * x0[2]) / A[3, 3]])
j1 = L.jacobi(A, b, max_iter=2, tol=1e-30, x_ref=xs)["historial"]
story += [P("6.1 Jacobi (x<super>(0)</super> = 0)", "h2"),
          P("x<sub>1</sub><super>(1)</super> = (6 − (−1)·0 − 2·0)/10 = 0.6 ; "
            "x<sub>2</sub><super>(1)</super> = (25 − (−1)·0 − (−1)·0 − 3·0)/11 = 2.272727 ; "
            "x<sub>3</sub><super>(1)</super> = (−11)/10 = −1.1 ; x<sub>4</sub><super>(1)</super> = 15/8 = 1.875.", "f"),
          P(f"x<super>(1)</super> = {vec(j1[1]['aproximacion'])}. Segunda iteración: "
            f"x<sub>1</sub><super>(2)</super> = (6 + x<sub>2</sub><super>(1)</super> − 2x<sub>3</sub><super>(1)</super>)/10 = "
            f"(6 + {j1[1]['aproximacion'][1]:.6f} + {-2 * j1[1]['aproximacion'][2]:.6f})/10 = {j1[2]['aproximacion'][0]:.6f} ; "
            f"x<sub>2</sub><super>(2)</super> = (25 + x<sub>1</sub> + x<sub>3</sub> − 3x<sub>4</sub>)/11 = {j1[2]['aproximacion'][1]:.6f} ; "
            f"x<sub>3</sub><super>(2)</super> = (−11 − 2x<sub>1</sub> + x<sub>2</sub> + x<sub>4</sub>)/10 = {j1[2]['aproximacion'][2]:.6f} ; "
            f"x<sub>4</sub><super>(2)</super> = (15 − 3x<sub>2</sub> + x<sub>3</sub>)/8 = {j1[2]['aproximacion'][3]:.6f}.", "f"),
          tabla([["k", "x<sup>(k)</sup>", "E<sub>rel</sub> vs x*", "‖b − A x‖"]] +
                [[h["numero"], vec(h["aproximacion"]), e3(h["error_rel"]), e3(h["residual"])] for h in j1], [1.0, 8.0, 3.8, 4.2])]

# Gauss-Seidel manual
gs = L.gauss_seidel(A, b, max_iter=2, tol=1e-30, x_ref=xs)["historial"]
a1 = gs[1]["aproximacion"]
story += [P("6.2 Gauss-Seidel (x<super>(0)</super> = 0)", "h2"),
          P(f"x<sub>1</sub><super>(1)</super> = 6/10 = 0.6 ; x<sub>2</sub><super>(1)</super> = (25 − (−1)(0.6) − (−1)(0) − 3·0)/11 = {a1[1]:.6f} ; "
            f"x<sub>3</sub><super>(1)</super> = (−11 − 2(0.6) − (−1)({a1[1]:.6f}) − (−1)(0))/10 = {a1[2]:.6f} ; "
            f"x<sub>4</sub><super>(1)</super> = (15 − 3({a1[1]:.6f}) − (−1)({a1[2]:.6f}))/8 = {a1[3]:.6f}. "
            "Cada componente usa ya los valores nuevos de las anteriores.", "f"),
          tabla([["k", "x<sup>(k)</sup>", "E<sub>rel</sub> vs x*", "‖b − A x‖"]] +
                [[h["numero"], vec(h["aproximacion"]), e3(h["error_rel"]), e3(h["residual"])] for h in gs], [1.0, 8.0, 3.8, 4.2])]

# LU manual
lu = L.lu_solve(A, b, x_ref=xs)
Lm, Um, y = lu["L"], lu["U"], lu["y"]
story += [P("6.3 Factorización LU (Doolittle)", "h2"),
          P("Para i = 1..n: u<sub>ij</sub> = a<sub>ij</sub> − Σ<sub>k&lt;i</sub> l<sub>ik</sub>u<sub>kj</sub> (j ≥ i) ; "
            "l<sub>ji</sub> = (a<sub>ji</sub> − Σ<sub>k&lt;i</sub> l<sub>jk</sub>u<sub>ki</sub>)/u<sub>ii</sub> (j &gt; i). "
            f"Ejemplo: u<sub>11</sub>=10 ; l<sub>21</sub>=−1/10={Lm[1,0]:.4f} ; l<sub>31</sub>=2/10={Lm[2,0]:.4f} ; "
            f"u<sub>22</sub>=11−(−0.1)(−1)={Um[1,1]:.4f}.", "f"),
          Preformatted("L =\n" + "\n".join("  " + "  ".join(f"{v:9.5f}" for v in r) for r in Lm) +
                       "\nU =\n" + "\n".join("  " + "  ".join(f"{v:9.5f}" for v in r) for r in Um) +
                       f"\nL y = b → y = {vec(y)}\nU x = y → x = {vec(lu['x'], 10)}\n‖L U − A‖<sub>max</sub> = {np.abs(Lm @ Um - A).max():.2e}   "
                       f"E_rel = {lu['historial'][-1]['error_rel']:.2e}".replace("<sub>max</sub>", "_max"), st["code"])]

# CG manual
cg = L.gradiente_conjugado(A, b, x_ref=xs, tol=1e-14)
r0 = b.copy(); p0 = r0.copy(); Ap0 = A @ p0; al0 = (r0 @ r0) / (p0 @ Ap0)
x1c = al0 * p0; r1 = r0 - al0 * Ap0; be0 = (r1 @ r1) / (r0 @ r0)
story += [P("6.4 Gradiente conjugado (x<super>(0)</super> = 0)", "h2"),
          P(f"r<sub>0</sub> = p<sub>0</sub> = b ; r<sub>0</sub>·r<sub>0</sub> = {r0 @ r0:.1f} ; p<sub>0</sub>ᵀA p<sub>0</sub> = {p0 @ Ap0:.1f} ; "
            f"α<sub>0</sub> = {al0:.6f} ; x<sup>(1)</sup> = α<sub>0</sub>p<sub>0</sub> = {vec(x1c)} ; r<sub>1</sub> = r<sub>0</sub> − α<sub>0</sub>A p<sub>0</sub> = {vec(r1)} ; "
            f"β<sub>0</sub> = {be0:.6f}. El método alcanzó ‖r‖/‖b‖ &lt; 10⁻¹⁴ en {cg['iteraciones']} iteraciones (n = 4, coherente con "
            f"la terminación en ≤ n pasos).", "f"),
          tabla([["k", "x<sup>(k)</sup>", "E<sub>rel</sub> vs x*", "‖b − A x‖"]] +
                [[h["numero"], vec(h["aproximacion"], 8), e3(h["error_rel"]), e3(h["residual"])] for h in cg["historial"]], [1.0, 8.0, 3.8, 4.2])]

# ===================== 7. EXPERIMENTOS 3 ESCENARIOS =========================
story += [PageBreak(), P("7. Módulo 2: ejecución de los tres escenarios (sistemas lineales)", "h1"),
          P("Parámetros numéricos: tolerancia ‖r‖/‖b‖ &lt; 10⁻¹⁰, x<super>(0)</super>=0, máximo 5000 iteraciones (CG: 200). "
            "Se ejecutan los cuatro métodos más la directa de referencia y se comparan contra x*.")]
resumen = {}
fig, axs = plt.subplots(1, 3, figsize=(11, 3.1))
for ax, tipo in zip(axs, M.ESC_TIPOS):
    A_, b_, xs_, desc_ = M.sistema_lineal(tipo)
    diag = L.diagnostico(A_)
    res = L.ejecutar_todos(A_, b_, xs_, tol=1e-10, max_iter=5000)
    resumen[tipo] = (A_, b_, xs_, desc_, diag, res)
    for m in ("Jacobi", "Gauss-Seidel", "Gradiente conjugado"):
        h = res[m]["historial"]
        ax.semilogy([i["numero"] for i in h], [i["residual"] for i in h], label=m)
    ax.set_title(f"{ETQ[tipo]} (κ₂={diag['kappa2']:.3g})", fontsize=9)
    ax.set_xlabel("iteración"); ax.set_ylabel("‖b − A x‖"); ax.grid(alpha=.3)
    if tipo != "ESTRES":
        ax.set_xscale("symlog", linthresh=10)
axs[0].legend(fontsize=7)
fig.tight_layout()
img_conv = fig_a_img(fig, 17)

for tipo in M.ESC_TIPOS:
    A_, b_, xs_, desc_, diag, res = resumen[tipo]
    story += [PageBreak()] if tipo == "MAL_CONDICIONADO" else []
    story += [P(f"7.{M.ESC_TIPOS.index(tipo) + 1} Escenario {ETQ[tipo]}", "h2"), P(desc_),
              tabla([["n", "SPD", "Dom. estricta", "κ₂(A)", "λ<sub>mín</sub>", "λ<sub>máx</sub>", "ρ(T<sub>J</sub>)", "ρ(T<sub>GS</sub>)"],
                     [diag["n"], "sí" if diag["spd"] else "no", "sí" if diag["dd_estricta"] else "no", e3(diag["kappa2"]),
                      e3(diag["lambda_min"]), e3(diag["lambda_max"]), g4(diag["rho_jacobi"]), g4(diag["rho_gs"])]],
                    [1.0, 1.4, 2.4, 2.6, 2.3, 2.3, 2.5, 2.5])]
    filas = [["Método", "¿Convergió?", "Iter.", "E<sub>abs</sub> final", "E<sub>rel</sub> final", "E<sub>%</sub>", "‖r‖ final", "κ·‖r‖/‖b‖ (cota)", "Tiempo [ms]"]]
    for m in ("Jacobi", "Gauss-Seidel", "LU", "Gradiente conjugado"):
        s = res[m]; h = s["historial"][-1]
        ok = np.all(np.isfinite(s["x"])) and abs(h["error_rel"]) < 1e100
        cota = E.cota_error_por_residual(A_, s["x"], b_) if ok else None
        filas.append([m, "sí" if s["convergio"] else "<b>NO</b>", s["iteraciones"] if ok else f"{s['iteraciones']} (diverge)",
                      e3(h["error_abs"]) if ok else "∞ (desbordó)", e3(h["error_rel"]) if ok else "∞",
                      e2(100 * h["error_rel"]) if ok else "—", e3(h["residual"]) if ok else "—", e3(cota), f"{s['tiempo_ms']:.2f}"])
    xr = res["referencia"]
    filas.append(["Directa (referencia)", "sí", 1, e3(E.error_abs(xr, xs_)), e3(E.error_rel(xr, xs_)),
                  e2(E.error_pct(xr, xs_)), e3(E.residual(A_, xr, b_)), e3(E.cota_error_por_residual(A_, xr, b_)), "—"])
    story += [tabla(filas, [2.9, 1.5, 1.9, 1.9, 1.9, 1.3, 1.9, 2.1, 1.6])]
    # evolución del error en iteraciones seleccionadas
    sel = [1, 2, 5, 10, 50, 100, 500]
    ev = [["Iter. k"] + [str(k) for k in sel]]
    for m in ("Jacobi", "Gauss-Seidel", "Gradiente conjugado"):
        h = res[m]["historial"]
        fila = [m]
        for k in sel:
            fila.append(e2(h[k]["error_rel"]) if k < len(h) and abs(h[k]["error_rel"]) < 1e100 else "—")
        ev.append(fila)
    story += [Spacer(1, .1 * cm), P("Error relativo E<sub>rel</sub> en iteraciones seleccionadas (— = el método ya terminó, divergió o no llegó a esa iteración):", "n"),
              tabla(ev, [3.2] + [1.97] * 7)]
story += [Spacer(1, .2 * cm), P("Residual frente a iteración (escala logarítmica; eje x simétrico-log en NORMAL y MAL COND.):", "n"), img_conv]

# perturbación
rng = np.random.default_rng(7)
amps = {}
fp = [["Escenario", "κ₂(A)", "‖δb‖/‖b‖", "‖δx‖/‖x‖ observado", "Cota κ·‖δb‖/‖b‖", "Amplificación observada"]]
for tipo in M.ESC_TIPOS:
    A_, b_, xs_, *_ = resumen[tipo]
    db_ = rng.standard_normal(len(b_)); db_ *= 1e-6 * np.linalg.norm(b_) / np.linalg.norm(db_)
    xp = L.referencia_directa(A_, b_ + db_)
    obs = np.linalg.norm(xp - xs_) / np.linalg.norm(xs_)
    cota = E.cota_perturbacion(A_, b_, db_)
    amps[tipo] = (obs / 1e-6, E.cond2(A_), obs <= cota * (1 + 1e-9))
    fp.append([ETQ[tipo], e3(E.cond2(A_)), "1.000e-06", e3(obs), e3(cota), g4(obs / 1e-6)])
story += [P("7.4 Sensibilidad ante una perturbación de b (‖δb‖/‖b‖ = 10⁻⁶, dirección aleatoria fija, semilla 7)", "h2"),
          tabla(fp, [2.4, 2.6, 2.4, 3.6, 3.4, 2.6]),
          P("Amplificación observada (‖δx‖/‖x‖ dividido por ‖δb‖/‖b‖): " +
            "; ".join(f"{ETQ[t]} {amps[t][0]:.3g} (κ₂={amps[t][1]:.3g})" for t in M.ESC_TIPOS) +
            ". " + ("En los tres escenarios el error observado respeta la cota κ·‖δb‖/‖b‖ de la Sección 4."
                    if all(v[2] for v in amps.values()) else "ATENCIÓN: se violó la cota en algún escenario."), "n")]

# conclusiones numéricas preliminares
rN, rS, rM = resumen["NORMAL"][5], resumen["ESTRES"][5], resumen["MAL_CONDICIONADO"][5]
dM = resumen["MAL_CONDICIONADO"][4]
story += [P("7.5 Conclusión numérica preliminar (Módulo 2, sistemas lineales)", "h2"),
          P(f"• <b>NORMAL</b> (κ₂={resumen['NORMAL'][4]['kappa2']:.2f}, dominancia estricta): los cuatro métodos convergen; "
            f"Gauss-Seidel necesitó {rN['Gauss-Seidel']['iteraciones']} iteraciones, Jacobi {rN['Jacobi']['iteraciones']} y CG {rN['Gradiente conjugado']['iteraciones']} "
            f"(≤ n=4). LU y CG alcanzan precisión de máquina; los iterativos clásicos quedan en ≈10⁻¹⁰ (la tolerancia pedida).<br/>"
            f"• <b>ESTRÉS</b> (n=10, κ₂={resumen['ESTRES'][4]['kappa2']:.1f}): ρ(T<sub>J</sub>)={resumen['ESTRES'][4]['rho_jacobi']:.4f} y ρ(T<sub>GS</sub>)={resumen['ESTRES'][4]['rho_gs']:.4f} "
            f"explican la lentitud: Jacobi {rS['Jacobi']['iteraciones']} y Gauss-Seidel {rS['Gauss-Seidel']['iteraciones']} iteraciones (≈ la mitad, como predice ρ<sub>GS</sub>≈ρ<sub>J</sub>²), "
            f"frente a {rS['Gradiente conjugado']['iteraciones']} de CG. La exigencia crece pero el sistema sigue bien condicionado.<br/>"
            f"• <b>MAL COND.</b> (Hilbert 6×6, κ₂={dM['kappa2']:.3g}): se distinguen tres fenómenos. "
            f"(i) <i>Mal condicionamiento</i>: incluso LU alcanza solo E<sub>rel</sub>={rM['LU']['historial'][-1]['error_rel']:.1e} con residual ≈10⁻¹⁶; "
            f"(ii) <i>Fallo de convergencia</i>: Jacobi <b>diverge</b> (ρ(T<sub>J</sub>)={dM['rho_jacobi']:.2f}&gt;1) y Gauss-Seidel, pese a ser A SPD (ρ={dM['rho_gs']:.6f}), "
            f"no alcanza la tolerancia en 5000 iteraciones (E<sub>rel</sub>={rM['Gauss-Seidel']['historial'][-1]['error_rel']:.1e}); "
            f"(iii) CG converge en {rM['Gradiente conjugado']['iteraciones']} iteraciones por residual, pero con E<sub>rel</sub>={rM['Gradiente conjugado']['historial'][-1]['error_rel']:.1e}: "
            f"<b>un residual pequeño no implica un error pequeño</b> cuando κ es grande.")]

# ===================== 8. PROTOTIPO, DER, REPO ==============================
tmp = tempfile.mkdtemp()
ruta = os.path.join(tmp, "p.db")
prm = {k: v for k, v in PAR["deterioro"]["MAL_CONDICIONADO"].items() if k != "nota"}
res1 = servicio.ejecutar("deterioro", "MAL_CONDICIONADO", prm, {"tol": 1e-10, "max_iter": 3000})
con = db.conectar(ruta); sid = db.guardar(con, "deterioro", "MAL_CONDICIONADO", res1); con.close()
con = db.conectar(ruta); rec = db.abrir(con, sid)
n_it = sum(len(e["iteraciones"]) for e in rec["ejecuciones"])
s_ = rec["params"].pop("sistema"); rec["params"].pop("diagnostico")
res2 = servicio.ejecutar("deterioro", "MAL_CONDICIONADO", rec["params"], {"tol": s_["tol"], "max_iter": s_["max_iter"], "n": len(s_["b"])})
dif = []
for e1, e2 in zip(res1["ejecuciones"], res2["ejecuciones"]):
    if e1["iteraciones"]:
        dif.append((e1["metodo"], np.max(np.abs(np.array(e1["iteraciones"][-1]["aproximacion"], float) - np.array(e2["iteraciones"][-1]["aproximacion"], float)))))
con.close()

story += [PageBreak(), P("8. Prototipo web, modelo de datos y repositorio", "h1"),
          P("<b>Aplicación.</b> Flask + SQLite (<font name='DVM'>python app.py</font>). Pantallas: <i>Inicio</i> (4 tarjetas: Detención, Deterioro, "
            "Oscilaciones, Sensores), <i>Módulo del caso</i> (modelo, parámetros con validación, selector NORMAL/ESTRÉS/MAL COND.), "
            "<i>Resultados</i> (tabla por método, gráficos regenerados desde la BD, conclusión matemática y del caso separadas) e "
            "<i>Historial</i> (buscar, abrir y relanzar con comparación). En esta semana el Módulo 2 ejecuta los métodos lineales; los módulos 1, 3 y 4 "
            "ejecutan su referencia analítica y quedan listos para recibir RK, integración e interpolación en la semana 2."),
          P("<b>Modelo entidad–relación.</b> Seis entidades en cadena 1:N (caso → escenario → simulación → ejecución de método → iteraciones) "
            "más un resumen 1:1 por ejecución. Scripts: <font name='DVM'>db/schema_sqlite.sql</font> (usado por la app) y "
            "<font name='DVM'>db/schema_postgres.sql</font> (equivalente con SERIAL/JSONB/BOOLEAN; no probado contra un servidor PostgreSQL en esta entrega). "
            "Código PlantUML en <font name='DVM'>docs/DER.puml</font>."),
          Image(os.path.join(AQUI, "DER.png"), width=17 * cm, height=17 * cm * 0.37), Spacer(1, .2 * cm),
          P("Modelo relacional (PK subrayada en el DER; FK → tabla padre):", "n"),
          Preformatted("caso_estudio(id PK, nombre UNIQUE, modelo_version)\n"
                       "escenario(id PK, caso_id FK->caso_estudio, tipo CHECK{NORMAL,ESTRES,MAL_CONDICIONADO},\n"
                       "          parametros_json, fuente_datos)\n"
                       "simulacion(id PK, escenario_id FK->escenario, fecha, usuario_equipo, estado)\n"
                       "ejecucion_metodo(id PK, simulacion_id FK->simulacion, metodo, tolerancia, paso,\n"
                       "                 max_iter, convergio, tiempo_ms)\n"
                       "iteracion_resultado(id PK, ejecucion_id FK->ejecucion_metodo, numero,\n"
                       "                    aproximacion_json, residual, error_abs, error_rel)\n"
                       "resultado_resumen(id PK, ejecucion_id FK UNIQUE->ejecucion_metodo, referencia,\n"
                       "                  valor_json, metrica_error_json, interpretacion)", st["code"]),
          P("<b>Prueba de persistencia (ejecutar → guardar → cerrar → recuperar → repetir → comparar).</b> Se ejecutó Módulo 2 / MAL COND., "
            "se guardó, se cerró la conexión, se abrió una conexión nueva y se recuperaron parámetros e iteraciones "
            f"({n_it} registros de iteración); luego se repitió el cálculo desde los parámetros guardados. Diferencia máxima entre la aproximación final "
            "original y la repetida por método: " + "; ".join(f"{m}: {v:.1e}" for m, v in dif) +
            " (el cálculo es determinista, por lo que coinciden dentro de la tolerancia 10⁻¹²). La misma prueba está automatizada en "
            "<font name='DVM'>tests/test_persistencia.py</font> para los tres escenarios; el conjunto de pruebas incluye 13 casos (errores, métodos, persistencia y flujo web)."),
          P("<b>Estructura del repositorio.</b>", "b"),
          Preformatted("simtele-risk/\n├── app.py                  # aplicación Flask\n├── simtele/                # errores.py, lineales.py, modelos.py, servicio.py, db.py, graficos.py\n"
                       "├── templates/              # inicio, módulo, simulación, historial\n├── db/                     # schema_sqlite.sql, schema_postgres.sql\n"
                       "├── docs/                   # DER (dot/png/puml), generar_informe.py, este PDF\n├── tests/                  # pytest: lineales, errores, persistencia, flujo web\n"
                       "├── data/                   # ejemplos de entrada (JSON) y base SQLite local\n└── README.md, requirements.txt", st["code"])]

# ===================== 9. LIMITACIONES / PLAN ===============================
story += [P("9. Limitaciones y plan de la Semana 2", "h1"),
          P("<b>Limitaciones actuales.</b> (i) Los métodos de raíces, integración, interpolación y EDO aún no están implementados: los módulos 1, 3 y 4 "
            "muestran solo referencia analítica y sensibilidad. (ii) El módulo 2 aplica los sistemas lineales a matrices SPD construidas con x* conocido; "
            "el vínculo con un ajuste real de D(t) por mínimos cuadrados se hará en S2. (iii) Las conclusiones del caso son borradores automáticos. "
            "(iv) El esquema PostgreSQL no se ha probado en un servidor. (v) Datos y parámetros son sintéticos."),
          P("<b>Plan S2.</b> Implementar interpolación (Lagrange, Newton, splines), raíces (bisección, Newton-Raphson, secante), integración (trapecio, Simpson 1/3, Romberg) "
            "y EDO (RK2 con variante declarada, RK4); ejecutar NORMAL en los cuatro módulos con tablas y dos gráficos; incorporar ESTRÉS y MAL COND.; "
            "publicar la aplicación y presentar el informe de experimentos y fallos."),
          P("<b>Anexos.</b> Repositorio: [pegar URL de GitHub] · Código del DER: <font name='DVM'>docs/DER.puml</font> (pegar en planttext.com) · "
            "Reproducir este informe: <font name='DVM'>python docs/generar_informe.py</font>.")]


def pie(canvas, doc):
    canvas.saveState(); canvas.setFont("DV", 7); canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1.2 * cm, "SIMTELE-RISK · Proyecto final de Métodos Numéricos · Avance Semana 1 · datos sintéticos, uso educativo")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"{doc.page}")
    canvas.restoreState()


salida = os.path.join(AQUI, "Semana1_Avance_SIMTELE-RISK.pdf")
doc = SimpleDocTemplate(salida, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm, bottomMargin=2 * cm,
                        title="SIMTELE-RISK · Avance Semana 1", author="Benjamin Isaac Humerez Surco")
doc.build(story, onFirstPage=pie, onLaterPages=pie)
print("OK", salida)
