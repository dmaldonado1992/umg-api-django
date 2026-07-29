# Suite de pruebas automatizadas — API de Reserva de Laboratorios

Pruebas derivadas de las Historias de Usuario y sus Criterios de Aceptación en
formato Gherkin (Entregables 3 y 4).

## Cómo ejecutar

```bash
# 1. Instalar dependencias (una sola vez)
pip install -r requirements-dev.txt

# 2. Levantar la base de datos de pruebas (queda corriendo en segundo plano)
docker compose -f docker-compose.test.yml up -d

# 3. Ejecutar la suite
pytest
```

Filtros útiles:

```bash
pytest -m unit            # solo pruebas unitarias
pytest -m integration     # solo pruebas de integración
pytest -m hu001           # todo lo relacionado con HU-001
pytest --runxfail         # muestra los defectos conocidos como fallos reales
```

Para apagar la base de pruebas: `docker compose -f docker-compose.test.yml down -v`

## Estrategia de ambientes

| Nivel | Contra qué corre | Escribe datos | Cuándo |
|---|---|---|---|
| Unitarias | PostgreSQL 18 efímero (contenedor) | Sí, y revierte | Cada push y en local |
| Integración | PostgreSQL 18 efímero (contenedor) | Sí, y revierte | Cada push y en local |
| Smoke | API desplegada en Render | **No, solo lectura** | Manual / post-deploy |

La base productiva de Render **nunca** participa en las pruebas unitarias ni de integración. Se usa un PostgreSQL 18 desechable —el mismo motor que producción,
por lo que se conserva la fidelidad de comportamiento— y `pytest-django` envuelve cada prueba en una transacción que se revierte al terminar.

Los smoke tests sí golpean el despliegue real, pero se limitan a peticiones `GET`.
Se ejecutan aparte:

```bash
pytest -m smoke
```

La URL sale de `SMOKE_BASE_URL`, resuelta con `python-decouple` igual que las
credenciales de base de datos. Como decouple da prioridad a las variables de
entorno del sistema sobre el archivo `.env`, la misma línea de código sirve en
los dos ambientes:

| Ambiente | Dónde se define |
|---|---|
| Local | `.env` → `SMOKE_BASE_URL=https://umg-api-django.onrender.com` |
| GitHub Actions | *Settings → Secrets and variables → Actions → Variables* |

Si no está definida, las pruebas se omiten (`skip`) y la suite normal no se ve
afectada.

**Sobre el arranque en frío.** Render suspende los servicios del plan gratuito
tras un rato sin tráfico, y la primera petición dispara el arranque del
contenedor —que puede tardar más de un minuto—. Para que ninguna prueba falle por
una causa ajena a la API, la fixture `sesion` despierta el servicio antes de
empezar y reintenta hasta agotar un presupuesto de 4 minutos. Ese costo se paga
una sola vez por corrida: una vez despierto, la suite completa toma ~25 s.

## Estructura

```
tests/
├── conftest.py                          fixtures compartidas (usuarios, labs, payloads)
├── unit/
│   └── test_hu001_reglas.py             reglas de negocio aisladas
├── integration/
│   └── test_hu001_crear_reserva.py      6 escenarios Gherkin de HU-001
└── smoke/
    └── test_smoke_produccion.py         verificación de solo lectura sobre Render
```

Cada clase de `integration/` corresponde a un escenario del documento de criterios
y lleva el Gherkin completo en su docstring, de modo que la trazabilidad
criterio → prueba es directa.

## Estado actual

| Suite | Resultado | Duración |
|---|---|---|
| Unitarias + integración (HU-001) | `53 passed, 9 xfailed` | 2.2 s |
| Smoke (Render) | `7 passed` | 26 s |

### HU-001 — detalle por escenario

| # | Escenario | Regla | Resultado |
|---|---|---|---|
| 1 | Registro exitoso de una reserva | RF-001, RN-008, RN-010 | ✅ Cumple |
| 2 | Campos obligatorios incompletos | RF-001, RN-002, RN-005 | ⚠️ Parcial — DEF-001 |
| 3 | Correo electrónico con formato inválido | RN-009 | ✅ Cumple (adaptado, ver nota) |
| 4 | Fecha anterior a la fecha actual | RN-003 | ✅ Cumple |
| 5 | Duración mayor a la permitida | RN-011 | ❌ No implementada — DEF-002 |
| 6 | Horario fuera del rango de operación | RN-012 | ❌ No implementada — DEF-003 |

**Nota sobre el escenario 3.** El endpoint no recibe el correo del docente:
recibe `UMG_User_ID` y deriva el correo del usuario ya registrado, tal como
describe el comentario de la GUI ("se captura de manera automática el correo del
usuario que está logeado"). La validación de formato de correo pertenece por
tanto al alta de usuarios, no a este endpoint. La prueba verifica la regla
equivalente que sí aplica aquí: solo un docente existente y activo puede quedar
asociado a una reserva.

## Defectos detectados

Los tres están marcados con `@pytest.mark.xfail(strict=True)`, lo que mantiene la
suite en verde mientras documenta el defecto. `strict=True` significa que si
alguien corrige el código, la prueba fallará avisando que ya puede quitarse la
marca.

### DEF-001 — Omitir la hora devuelve HTTP 500 en lugar de 400

**Severidad:** Alta · **Escenario:** HU-001 #2 · **Ubicación:** `reservas/views.py:73`

```python
if hora_inicio >= hora_fin:
```

La comparación se ejecuta antes de comprobar que ambos campos vengan presentes.
Si el cliente omite `UMG_Hora_Inicio` o `UMG_Hora_Fin`, el valor es `None` y
Python lanza:

```
TypeError: '>=' not supported between instances of 'NoneType' and 'str'
```

El resultado es un HTTP 500 en vez del 400 que exige el criterio. Además de
incumplir el contrato, un 500 no le dice al cliente qué campo corrigió mal.

**Corrección sugerida:** validar la presencia de ambos campos antes de compararlos.

### DEF-002 — RN-011 no implementada (duración máxima de 4 horas)

**Severidad:** Media · **Escenario:** HU-001 #5 · **Ubicación:** `reservas/views.py`

No existe validación de duración del bloque. La API acepta con HTTP 201 reservas
de 6 h e incluso de 15 h continuas. Coincide con el hallazgo ya reportado en la
GUI ("si se exceden las 4 horas continuas el mismo día, se permite hacer la
reserva"), lo que confirma que la regla falta en toda la pila, no solo en el
frontend.

### DEF-003 — RN-012 no implementada (horario hábil 07:00–22:00)

**Severidad:** Media · **Escenario:** HU-001 #6 · **Ubicación:** `reservas/views.py`

No existe validación del horario de operación. La API acepta bloques de 05:00 a
06:00 o de 23:00 a 23:59. Concuerda con el comentario de la GUI, que ofrece un
rango de 06:00 a 23:30 en lugar del 07:00–22:00 especificado.

## Integración continua

`.github/workflows/pruebas.yml` avanza en tres etapas encadenadas. Cada una solo
arranca si la anterior terminó en verde:

```
1 - Unitarias  ──▶  2 - Integración  ──▶  3 - Smoke (manual)
   19 pruebas          34 + 9 xfail          7 pruebas
   ~0.9 s              ~3 s                  ~26 s
```

El orden va de lo más barato y específico a lo más caro y amplio: si una regla de
negocio está rota, no tiene sentido gastar tiempo levantando la API completa ni
mucho menos golpear el servicio desplegado.

Cada etapa publica sus propios artifacts:

| Etapa | Artifacts |
|---|---|
| Unitarias | `junit-unitarias.xml`, `reporte-unitarias.html` |
| Integración | `junit-integracion.xml`, `reporte-integracion.html`, `cobertura/` |
| Smoke | `junit-smoke.xml`, `reporte-smoke.html` |

La cobertura se mide en la etapa de integración, que es la que ejercita el código
de punta a punta.

La etapa de smoke se dispara a mano desde *Actions → Run workflow* marcando la
casilla. No corre en cada push porque un push no cambia el código desplegado, y
porque cada corrida implica el arranque en frío de Render. Para que corra
siempre, basta con borrar la condición `if` de ese job.

**La base de datos se levanta con el mismo `docker-compose.test.yml` que usás en
tu máquina**.

**Ejecuciones concurrentes.** El workflow declara `concurrency` con
`cancel-in-progress: true`, agrupado por rama. Si hacés dos pushes seguidos a la
misma rama, la corrida del commit anterior se cancela y solo sobrevive la del más
reciente. Ramas distintas nunca se cancelan entre sí.

Los smoke tests se disparan manualmente desde *Actions → Run workflow*, marcando
la casilla correspondiente. Requieren definir la variable `SMOKE_BASE_URL` en
*Settings → Secrets and variables → Actions → Variables*.

## Cómo agregar las siguientes historias

1. Crear `tests/integration/test_hu00X_<nombre>.py`.
2. Una clase por escenario, nombrada `TestEscenarioNDescripcion`.
3. Copiar el Gherkin del documento de criterios al docstring de la clase.
4. Marcar el módulo con `pytestmark = [pytest.mark.integration, pytest.mark.hu00X, pytest.mark.django_db]`.
5. Reutilizar las fixtures de `conftest.py`; agregar ahí las nuevas que sean
   compartidas por más de un archivo.

Las fixtures `crear_reserva`, `otro_docente`, `otro_lab` y `rol_admin` ya están
listas y aún no se usan en HU-001: están pensadas para HU-002 (conflictos de
disponibilidad), HU-007 (modificación) y HU-008 (cancelación).
