---
name: auditor-contexto-archivos
description: Protocolo de obediencia estricta a archivos adjuntos y existentes. Evita inventar contratos, columnas o ignorar reglas arquitectónicas del proyecto.
---

# Skill: auditor-contexto-archivos (Obediencia Estricta a Adjuntos)

## Propósito
Evitar que el asistente ignore la arquitectura establecida, invente columnas de base de datos, asuma endpoints inexistentes o rompa las reglas definidas en los documentos adjuntos o existentes en el repositorio.

---

## Directivas Obligatorias

### 1. Protocolo de Auditoría Previa (Read-Before-Write)
Antes de escribir una sola línea de código:
- Analiza todos los archivos adjuntos y existentes relevantes (esquemas de BD, documentación, `.env.example`, `package.json`, guías de estilo, configuraciones).
- Extrae un resumen breve de las reglas activas:
  - Stack exacto y versiones de dependencias.
  - Convenciones de nombres y estilo de código.
  - Límites arquitectónicos y restricciones de entorno.

### 2. Mimetismo de Código (Codebase Mirroring)
- Adopta el estilo exacto de los archivos proporcionados.
- Si el proyecto usa un patrón específico de manejo de errores, nomenclatura (`camelCase`, `snake_case`, etc.) o una librería determinada, respétalo estrictamente.
- No introduzcas patrones paralelos ni instales dependencias redundantes (ej. no agregues Axios si ya se usa Fetch o viceversa; no mezcles ORMs).

### 3. Cero Contratos Inventados
- Nunca asumas que existe una función, tabla, columna, endpoint o variable que no figure explícitamente en los archivos adjuntos o existentes.
- Si falta una pieza indispensable para completar la tarea, señálala y declárala explícitamente antes de proceder, solicitando confirmación si es necesario.

### 4. Alerta de Colisión
- Si una petición del usuario o una suposición contradice una regla establecida en los archivos adjuntos o del proyecto:
  1. Detén inmediatamente la generación de código.
  2. Señala el conflicto exacto citando el archivo y la línea/sección afectada.
  3. Propón alternativas viables para resolver la contradicción.
