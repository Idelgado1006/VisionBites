---
name: backend-profesional
description: Ingeniería de servidor y seguridad. Separación estricta en 3 capas, validación zero-trust en la frontera, errores estandarizados y transacciones seguras.
---

# Skill: backend-profesional (Ingeniería de Servidor y Seguridad)

## Propósito
Garantizar que el backend sea seguro, predecible, fácil de depurar, mantenible y escalable bajo estándares de ingeniería de software robustos.

---

## Directivas Obligatorias

### 1. Separación Estricta en 3 Capas
El backend debe respetar una arquitectura desacoplada y unidireccional:
1. **Controlador / Ruta (Capa HTTP)**:
   - Solo extrae parámetros (`body`, `params`, `query`, `headers`).
   - Invoca la validación de entrada.
   - Llama al servicio correspondiente.
   - Devuelve la respuesta con el código HTTP apropiado.
   - **Prohibido**: Incluir lógica de negocio o consultas directas a la base de datos aquí.
2. **Servicio (Capa de Negocio)**:
   - Contiene las reglas del dominio, cálculos, flujos de trabajo y orquestación.
   - Totalmente agnóstico de la capa de transporte: **no debe conocer objetos `req` ni `res` HTTP**.
3. **Repositorio / Acceso a Datos**:
   - Único lugar autorizado para ejecutar consultas SQL, ORM o llamadas a APIs externas de almacenamiento.
   - Devuelve entidades o tipos de datos limpios al servicio.

### 2. Validación en la Frontera (Zero-Trust)
- Todo dato que ingrese al backend (`body`, `query`, `params`, `headers`) debe validarse y tiparse estrictamente en la puerta de entrada antes de ejecutar cualquier lógica de negocio.
- Emplea librerías declarativas con esquemas estrictos:
  - TypeScript/Node: Zod, Valibot, Typia.
  - Python: Pydantic.
  - Java/NestJS: Class-Validator con DTOs tipados.
- Rechaza campos no reconocidos o malformados inmediatamente (fail-fast).

### 3. Manejo de Errores Estandarizado
- **Prohibición de fugas de información**: Prohibido devolver al cliente errores crudos de la base de datos, trazas de pila (*stack traces*) o detalles de infraestructura interna.
- Implementa un manejador centralizado de errores (*error middleware* / *exception filter*).
- Respuestas de error siempre uniformes:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "La factura solicitada no existe.",
      "details": []
    }
  }
  ```
- Códigos HTTP semánticamente correctos:
  - `400 Bad Request`: Formato de petición inválido.
  - `401 Unauthorized`: Falta de autenticación o token inválido/expirado.
  - `403 Forbidden`: Autenticado pero sin permisos sobre el recurso.
  - `404 Not Found`: Recurso no encontrado.
  - `409 Conflict`: Conflicto de estado (ej. clave única duplicada).
  - `422 Unprocessable Entity`: Validación de negocio fallida sobre datos sintácticamente válidos.
  - `500 Internal Server Error`: Falla interna no controlada (con registro interno de logs).

### 4. Operaciones Críticas Seguras
- **Transacciones Atómicas**: Usa transacciones de base de datos cuando una operación afecte más de una tabla o documento (ej. crear pedido y descontar stock; crear usuario y registrar auditoría).
- **Paginación Obligatoria por Defecto**: Todo endpoint de listado debe tener paginación (offset o cursor-based) con límite máximo permitido para prevenir caídas por agotamiento de memoria.
- **Autorización a Nivel de Recurso (IDOR Prevention)**: Verifica que el usuario autenticado sea legítimamente propietario o tenga permisos explícitos sobre el recurso que intenta consultar, modificar o eliminar.
