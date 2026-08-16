# MPR State Contract Test Suite

## Resumen

Este PR transforma la validación de anotaciones del visor MPR de una estrategia basada en la capa visual a una estrategia basada en el modelo matemático interno de CornerstoneTools.

El objetivo es validar el estado clínico real de las mediciones: UIDs, coordenadas world-space, dimensiones físicas, slices, planos MPR y ciclo de vida de las anotaciones.

## Motivación

La suite anterior inspeccionaba overlays SVG y texto renderizado para decidir si una medición existía. Esa aproximación tiene varios problemas:

- Acopla los tests a una implementación visual no contractual.
- Puede pasar aunque el modelo matemático esté corrupto.
- Puede fallar por cambios de renderizado, WebGL, zoom o estilos.
- No permite validar correctamente persistencia, mutaciones ni referencias espaciales.

Ahora las assertions consultan el estado de CornerstoneTools y reciben JSON plano, independiente de la presentación.

## Cambios principales

### Bridge de estado Cornerstone

El bridge de Cornerstone ahora vive en `handlers/`:

- `handlers/cornerstone_test_bridge.js`
- `handlers/cornerstone_test_bridge.py`

El bridge expone:

- Anotaciones registradas por viewport y herramienta.
- Anotaciones visibles en el slice actual.
- UID y búsqueda directa de anotaciones.
- `FrameOfReferenceUID`, `referencedImageId`, `volumeId` y `sliceIndex`.
- Puntos world-space `[x, y, z]`.
- Vectores de cámara y normales de plano.
- Medidas numéricas y unidades desde `cachedStats`.
- Proyección `worldToCanvas` para interacciones de edición y selección.
- Estado de herramientas activas y viewport actual.

Todas las respuestas del bridge son serializables como JSON.

### Acciones reutilizables

`utils/shared_actions.py` permanece como capa común para navegación, waits, clicks, teclado, drag, scroll, geometría, screenshots y eventos sobre canvas.

Los Page Objects componen estas acciones y los steps Behave permanecen delgados.

### Assertions matemáticas

La creación de una medición valida que:

- Existan exactamente dos puntos world-space.
- Los puntos sean vectores tridimensionales válidos.
- La unidad sea `mm`.
- La distancia calculada entre puntos coincida con el valor reportado dentro de una tolerancia de `0.01 mm`.

La persistencia valida UID y puntos espaciales antes y después de zoom, pan o navegación de slices.

### Edición y eliminación

Se añadieron acciones para:

- Proyectar puntos world-space a coordenadas de pantalla.
- Arrastrar un endpoint de una medición existente.
- Seleccionar una medición por su punto medio.
- Presionar `Delete` y verificar que el UID desaparece del State Manager.

### Ejecución de tests

Se eliminó el soporte de ejecuciones paralelas del runner:

- Se retiró `-p/--parallel` de `run_tests.py`.
- Se eliminó `ThreadPoolExecutor` y `run_parallel()`.
- Los equipos separados por coma se ejecutan secuencialmente.

## Cobertura

Se conservan los escenarios de carga y menú, y se añaden o reformulan 12 escenarios de contrato de estado.

| Categoría | Cobertura |
|---|---|
| Creación | Geometría física válida, unidades y valor positivo |
| Persistencia | UIDs únicos y conservación de puntos |
| Edge cases | Doble click sin distancia no crea anotaciones |
| Transformaciones | Zoom y pan no degradan el estado matemático |
| Slices | Visibilidad por slice y persistencia al regresar |
| MPR | Aislamiento axial, coronal y sagittal |
| Mutación | Edición de endpoint actualiza puntos y longitud |
| Eliminación | Delete limpia el UID del State Manager |
| Herramientas | Pan no crea anotaciones y el cambio de herramienta conserva el estado |
| Regresión | Carga del visor y cierre del menú circular |

Total: 14 escenarios.

## Criterios de arquitectura

- No se usan `g[data-annotation-uid]`, overlays SVG ni nodos de texto para assertions clínicas.
- No se usa OCR, comparación de píxeles ni screenshots como fuente de verdad.
- Los clicks de interacción usan Page Objects y `SharedActions`.
- La visibilidad por slice está separada de la persistencia del modelo.
- La selección de endpoints usa la transformación oficial de Cornerstone y el origen real del canvas.
- Los cambios no modifican el código del frontend de producción.

## Validación ejecutada

```text
python run_tests.py -t eden --headless
14 scenarios passed
91 steps passed
0 errors
```

También se verificó:

- `@measurement`
- `@spatial`
- `@crossplane`
- `@mutation`
- `@toolswitch`
- `@scroll`
- `@smoke`
- `@menu`
- Compilación Python.
- Sintaxis JavaScript del bridge.
- Ayuda de la CLI sin `--parallel`.
- Ausencia de referencias a selectores SVG de anotaciones.

## Fuera de alcance

- Cambios en la aplicación frontend de producción.
- Persistencia DICOM SR o backend.
- Validación clínica de valores esperados contra un estándar externo.
- Uso de OCR o inspección visual como mecanismo de assertion.
