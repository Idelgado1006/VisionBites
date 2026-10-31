---
name: arquitectura-organizacion-limpia
description: Estructura modular orientada a dominios (feature-based). Límites de líneas, responsabilidad única, nombres autoexplicativos y puntos únicos de verdad.
---

# Skill: arquitectura-organizacion-limpia (Estructura Modular)

## Propósito
Mantener proyectos ordenados, navegables y mantenibles a largo plazo, evitando archivos monstruosos donde se mezcla la interfaz con la lógica de negocio y la base de datos.

---

## Directivas Obligatorias

### 1. Estructura Orientada a Dominios (Feature-Based)
- Organiza el código por módulos o capacidades de negocio (ej. `features/usuarios`, `features/facturacion`, `features/inventario`).
- Cada módulo encapsula sus propios:
  - Componentes de interfaz de usuario.
  - Servicios y clientes de API.
  - Tipos e interfaces TypeScript / esquemas.
  - Validaciones y utilidades de dominio.
- Las carpetas globales (`shared/`, `core/`, `components/ui/`) se reservan estrictamente para utilidades e infraestructura verdaderamente transversales.

### 2. Límite de Tamaño y Responsabilidad Única
- **Límite**: Ningún archivo individual debe superar las 200 a 250 líneas de código.
- Si un archivo crece más allá de este umbral, divide sus responsabilidades:
  - **Vista**: UI pura y renderizado declarativo.
  - **Estado e interacción**: Hooks personalizados, controladores o máquinas de estado.
  - **Lógica de datos**: Servicios, transformadores y repositorios.

### 3. Nomenclatura Autoexplicativa
- **Prohibición de "Cajones de Sastre"**: Prohibido crear archivos genéricos como `utils.ts`, `helpers.js`, `common.ts` o `misc.py`.
- Cada archivo y función debe describir con precisión exacta su responsabilidad única:
  - Ejemplos correctos: `calcularImpuestosFactura.ts`, `validadorSesionActiva.ts`, `formatearMonedaLocal.ts`.
  - Si una utilidad hace varias cosas distintas, debe descomponerse en funciones enfocadas.

### 4. Punto Único de Verdad (Single Source of Truth)
- Las constantes de negocio, tipos de datos, esquemas de validación y variables de entorno se definen exactamente en un solo lugar y se exportan/importan.
- Cero cadenas mágicas (*magic strings*) o números fijos (*magic numbers*) dispersos en el código.
- Los esquemas de validación deben ser la fuente de derivación de los tipos (ej. `z.infer<typeof Schema>` en Zod o modelos Pydantic).
