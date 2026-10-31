---
name: ui-anti-ia
description: Directrices de diseño de interfaz con identidad humana. Elimina clichés visuales de IA (gradientes morados, sombras difusas, tarjetas excesivas) y asegura estados completos.
---

# Skill: ui-anti-ia (Diseño de Interfaz con Identidad Humana)

## Propósito
Eliminar los patrones visuales y clichés repetitivos que delatan inmediatamente a una interfaz generada por IA, construyendo experiencias web y de producto con intención, sobriedad y calidad artesanal profesional.

---

## Directivas Obligatorias

### 1. Prohibición de Clichés Visuales de IA
- **Sin gradientes genéricos**: Prohibido usar gradientes morados/azules/neón por defecto (ej. `from-indigo-500 to-purple-600` o fondos oscuros saturados de brillos púrpura).
- **Sin abuso de sombras ni redondeos desmedidos**: Prohibido abusar de tarjetas con sombras difusas (`shadow-xl`, `shadow-2xl`) y bordes exageradamente redondeados (`rounded-3xl`) en todos los contenedores.
- **Sin iconitis decorativa**: Prohibido colocar iconos decorativos superfluos al lado de cada título, botón, etiqueta o métrica sin una función clara de navegación o significado.

### 2. Sistema de Color e Intención
- **Paleta Neutra con Matiz Real**: Utiliza escalas sobrias con matices cálidos o fríos reales (tipo Zinc, Slate, Stone o Neutral).
- **Evitar extremos puros sin contraste de superficie**: Evitar `#000000` o `#FFFFFF` planos sin jerarquía ni contraste entre planos/superficies.
- **Acento único y reservado**: Emplea un único color de acento primario estrictamente reservado para acciones principales y estados clave (evitar mezclar múltiples colores primarios en una sola vista).

### 3. Jerarquía por Tipografía y Espacio (No por Cajas)
- No encierres cada elemento dentro de un recuadro o tarjeta ("card soup").
- Separa secciones y niveles de lectura mediante:
  - Espaciado asimétrico y calibrado (macro y micro espacios deliberados).
  - Peso tipográfico contrastado (`font-medium`, `font-semibold`, `font-bold`).
  - Tracking ajustado en títulos (`letter-spacing: -0.02em` a `-0.03em`).
  - Divisores sutiles de 1px con opacidad baja en lugar de bordes pesados.

### 4. Layouts con Propósito Real
- Evita la clásica cuadrícula simétrica de 3 tarjetas idénticas centradas.
- Diseña pensando en la ergonomía y el flujo de trabajo real:
  - Barras laterales compactas y contextuales.
  - Tablas densas con números alineados a la derecha (`font-variant-numeric: tabular-nums` / `tabular-nums`).
  - Vistas maestro-detalle eficientes.
  - Densidad de información cómoda y productiva según el caso de uso.

### 5. Estados Completos Obligatorios
Ninguna pantalla o componente se considera terminado si solo cubre el "camino feliz":
- **Estado de Carga (Loading)**: Usa skeletons que repliquen la geometría y forma real del contenido final, no spinners genéricos centrados en un contenedor vacío.
- **Estado Vacío (Empty State)**: Mensaje contextual claro acompañado de una acción directa para resolverlo (ej. botón "Crear primer registro").
- **Estado de Error**: Manejo de errores visual en línea (inline error), recuperable y con explicación clara de qué falló y cómo solucionarlo.
