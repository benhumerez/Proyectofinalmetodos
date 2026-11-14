# SIMTELE-RISK

Desafío Integrador Final de **Métodos Numéricos** (UMSA · Informática). Aplicación web con **cuatro casos de estudio**
inspirados en un sistema de transporte por cable (tipo Mi Teleférico, La Paz), cada uno con tres escenarios:
**NORMAL**, **ESTRÉS** y **MAL CONDICIONADO**.

> Proyecto estrictamente educativo. Los datos son **sintéticos** y los parámetros **supuestos**; no describen fallas
> verificadas de ninguna empresa ni se conectan con equipos de control reales.

## Estado: entrega Semana 1

| Área | Estado |
|---|---|
| Teoría de errores transversal (`simtele/errores.py`) | ✔ implementada y probada |
| Sistemas lineales: Jacobi, Gauss-Seidel, LU, Gradiente Conjugado, directa (`simtele/lineales.py`) | ✔ |
| Módulo 2 con los 3 escenarios (NORMAL, ESTRÉS, MAL COND.) | ✔ |
| Módulos 1, 3, 4: modelo, escenarios definidos, referencia analítica y sensibilidad | ✔ (métodos numéricos en Semana 2) |
| Aplicación web con 4 módulos, historial, guardar/recuperar/relanzar | ✔ prototipo |
| DER, modelo relacional y script SQL | ✔ (`docs/DER.*`, `db/`) |
| Interpolación, raíces, integración, EDO (RK2/RK4) | ⏳ Semana 2 |

El informe de avance está en `docs/Semana1_Avance_SIMTELE-RISK.pdf`.

## Instalación y ejecución

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py                                           # http://127.0.0.1:5000
```

La base de datos SQLite se crea sola en `data/simtele.db` (otra ruta: variable `SIMTELE_DB`).

## Pruebas

```bash
python -m pytest -q
```

Incluyen: convergencia y precisión de los métodos en los tres escenarios, distinción entre mal condicionamiento y no
convergencia, rechazo de matrices no SPD en CG, y la **prueba de persistencia**:
ejecutar → guardar → cerrar → recuperar → repetir el cálculo → coincidencia dentro de la tolerancia.

## Estructura

```
app.py              Aplicación Flask (inicio, módulo, resultados, historial, relanzar)
simtele/            errores.py · lineales.py · modelos.py · servicio.py · db.py · graficos.py
templates/          Plantillas HTML
db/                 schema_sqlite.sql (usado por la app) · schema_postgres.sql (equivalente, sin probar en servidor)
docs/               DER (DER.dot / DER.png / DER.puml), informe PDF y generar_informe.py
tests/              pytest
data/ejemplos/      Entradas de ejemplo (12 JSON: 4 casos × 3 escenarios)
```

## Modelo de datos

`caso_estudio 1─N escenario 1─N simulacion 1─N ejecucion_metodo 1─N iteracion_resultado`, y
`ejecucion_metodo 1─1 resultado_resumen`. Ver `docs/DER.png`; el código PlantUML está en `docs/DER.puml`
(se puede pegar en planttext.com).

## Cómo usar la aplicación

1. **Inicio**: elegir una de las cuatro tarjetas.
2. **Módulo**: elegir escenario, ajustar parámetros (con validación) y pulsar *Ejecutar y guardar*.
3. **Resultados**: tabla por método, gráficos regenerados desde la BD, conclusión matemática y del caso.
4. **Historial**: buscar, abrir y *Relanzar* una simulación guardada; la pantalla compara el nuevo resultado con el original.

## Regenerar el informe

```bash
python docs/generar_informe.py
```

## Integrantes

- Benjamin Isaac Humerez Surco
- [completar integrantes y mención]
