---
name: codigo-intencional-explicable
description: Cero código basura, apego estricto a YAGNI, comentarios de por qué (no de qué) y radiografía técnica explicativa de arquitectura en cada entrega.
---

# Skill: codigo-intencional-explicable (Cero Código Basura)

## Propósito
Frenar la tendencia de la IA a sobreingenierizar, introducir abstracciones prematuras o escribir código que el desarrollador no pueda defender, explicar ni mantener con confianza.

---

## Directivas Obligatorias

### 1. Regla YAGNI (You Aren't Gonna Need It)
- Escribe código estrictamente necesario para resolver el requerimiento actual.
- **Prohibido**:
  - Crear factories innecesarias, wrappers genéricos o clases abstractas "por si en el futuro se necesita".
  - Introducir capas de configuración complejas para casos hipotéticos.
  - Optimización prematura sin métricas o necesidad demostrada.

### 2. Prueba de Defensibilidad
- Cada bloque de código, función, parámetro o dependencia debe tener un propósito directo y justificado.
- Si una línea no aporta directamente al requerimiento ni corrige un caso borde real, debe eliminarse.
- Menos código que funcione supera a más código ornamental.

### 3. Comentarios de "Por Qué", Nunca de "Qué"
- **Prohibido comentar lo obvio**:
  - Evitar comentarios redundantes como `// recorre el array de usuarios`, `// define la variable id` o `// retorna el resultado`.
- El código debe ser autoexplicativo gracias a nombres precisos de variables, funciones y tipos.
- Usa comentarios únicamente para:
  - Explicar reglas de negocio complejas o no evidentes.
  - Justificar una decisión técnica específica o una solución a un caso borde no trivial.
  - Advertir sobre efectos colaterales o limitaciones técnicas deliberadas.

### 4. Entrega con Radiografía Técnica
Siempre que generes o modifiques un módulo o bloque de código significativo, acompaña la entrega con una **Radiografía Técnica** concisa que responda a 3 puntos en lenguaje claro:

1. **Flujo**: Cómo viajan y se transforman los datos de principio a fin a través de este fragmento.
2. **Por qué así**: Justificación de por qué se eligió esta solución directa frente a alternativas más complejas o sobrecargadas.
3. **Puntos de fallo controlados**: Qué errores, excepciones o casos borde específicos está previniendo activamente este código.
