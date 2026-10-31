# VisionBites · De Fotografía a Recetas Inteligentes & Macronutrientes Exactos

> Aplicación inteligente y accesible que permite al usuario tomar una foto de sus ingredientes (nevera, despensa o alacena) o de su comida, escanearlos mediante visión artificial multimodal, y obtener al instante recetas saludables con sus **macronutrientes exactos calculados científicamente** y optimización de porciones.
> **Stack**: Python 3.11 · Streamlit · Gemini / Gemma Vision API · PuLP · Pandas

---

## 1. Guía Rápida de Instalación y Ejecución (Windows PowerShell)

### Requisitos Previos
- Python 3.11 o 3.12 instalado.
- Conexión a internet (para llamadas de visión multimodal y generación de recetas con Gemini/Gemma).

### Pasos de Arranque

```powershell
# 1. Posicionarse en la carpeta del proyecto
cd c:\Users\edgar\Desktop\MLH

# 2. Crear el entorno virtual (si no existe)
py -3.11 -m venv .venv

# 3. Instalar dependencias fijas
.\.venv\Scripts\pip.exe install -r requirements.txt

# 4. Configurar variable de entorno (opcional para IA en vivo)
Copy-Item .env.example .env
# (Si no configuras clave o no hay internet, VisionBites conmuta automáticamente al catálogo de contingencia y presets pre-auditados)

# 5. Ejecutar la aplicación Streamlit
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La aplicación abrirá automáticamente en tu navegador local en `http://localhost:8501`.

### Interfaz de cocina

El rediseño se aplica a la aplicación funcional de Streamlit (`app.py`). La carpeta `frontend/` contiene una demostración React independiente y no sirve esta interfaz.

- Navegación numerada entre ingredientes, despensa y recetas, con avance automático al guardar o generar.
- Paleta crema, salvia y melocotón; ilustración SVG y fuentes del sistema, sin descargas externas.
- Diseño para móvil: una columna, navegación visible, controles táctiles y edición de cada ingrediente sin depender de una tabla ancha.
- Ejemplos locales, carga de fotos, cámara opcional, simulador de porciones y descarga del plan de cocina.
- Los estilos están separados en `assets/theme.css`, `assets/components.css` y `assets/responsive.css`.

Pruebas de lógica y del recorrido de interfaz, sin modelos externos:

```powershell
$env:GEMINI_API_KEY = ''
.\.venv\Scripts\python.exe -m pytest -q test_suite.py test_ui.py
```

---

## 2. Batería de Pruebas Automatizadas (T01 a T16)

Para verificar todas las garantías contractuales, matemáticas, de resiliencia y de visión:

```powershell
.\.venv\Scripts\pytest.exe -v test_suite.py
```

### Resumen de Casos de Prueba Verificados
- **T01**: Ingesta de 20 alimentos y generación completa de plan.
- **T02**: Rechazo estricto ante cantidades negativas (-10g) o IDs duplicados.
- **T03**: Exclusión de productos marcados con `apto=false` o fecha vencida.
- **T04**: Descarte inmediato de recetas con ingredientes inventados por la IA.
- **T05**: Asignación de 0 porciones ante stock insuficiente (sin sobreasignación).
- **T06**: Cálculo exacto de macronutrientes por porción con fórmula por 100g.
- **T07**: Conservación rigurosa de masa: $\text{inicial} = \text{usado} + \text{restante}$ con tolerancia $< 0.01\,\text{g}$.
- **T08**: Reoptimización instantánea en memoria sin re-invocar la IA.
- **T09**: Activación automática y visible del catálogo de contingencia offline ante fallos de red.
- **T10**: Rechazo de estimaciones arbitrarias cuando un alimento no figure en la base nutricional.
- **T11**: Escaneo visual con presets de demostración y validación de inventario.
- **T12**: Manejo seguro y conmutación de contingencia ante ausencia de imagen o desconexión.
- **T13**: Validación Zero-Trust con Pydantic (rechazo estricto de NaN/Inf y normalización de tildes en grupos).
- **T14**: Inmunidad del solver PuLP ante caracteres especiales en IDs de recetas y protección contra recetas con ingredientes faltantes.
- **T15**: Cobertura offline completa: todas las muestras guiadas (nevera, alacena, sancocho) generan recetas compatibles en contingencia local.
- **T16**: Normalización determinista de sinónimos visuales hacia el catálogo oficial USDA/INCAP.

---

## 3. Radiografía Técnica de Arquitectura (Skill: codigo-intencional-explicable)

1. **Flujo de Datos**:
   - `Foto (Cámara / Archivo / Preset)` $\rightarrow$ `vision_scanner.py`: Detección visual multimodal con Gemini/Gemma $\rightarrow$ `validator.py`: Sanitización y validación zero-trust $\rightarrow$ `ai_engine.py`: Generación de recetas adaptadas exclusivamente a los ingredientes reales $\rightarrow$ `nutrition.py`: Cruce con catálogo USDA/INCAP y cálculo exacto de macros por 100 g $\rightarrow$ `optimizer.py`: Programación lineal entera en PuLP $\rightarrow$ `ui_components/`: Interfaz interactiva ergonómica en Streamlit (`ui-anti-ia`).

2. **Por Qué Así**:
   - Se desacoplaron las vistas en componentes modulares independientes (`scanner_view`, `detected_items_view`, `recipes_macro_view`, `nutrition_summary_view`) manteniendo cada archivo estrictamente bajo las 200 líneas (`arquitectura-organizacion-limpia`).
   - El escaneo multimodal admite presets instantáneos para que la aplicación sea 100% interactiva incluso en entornos de demostración sin cámara o sin conexión a internet.
   - El solver PuLP resuelve la asignación entera en menos de 50 ms en local, permitiendo alternar instantáneamente entre *Modo Balance* y *Modo Aprovechamiento* sin latencia.

3. **Puntos de Fallo Controlados**:
   - **Alucinación de IA**: Bloqueada mediante lista blanca en `validator.py` (cualquier ingrediente inventado descarta la receta).
   - **Fallas de Visión / Red**: Si el servicio multimodal falla o no hay conexión, `vision_scanner.py` conmuta a un preset pre-auditado de nevera o alacena con indicador visible de estado.
   - **Sobreconsumo de Alimentos**: Las restricciones duras en PuLP ($\sum_r \text{g}_{i,r} x_r \le \text{cantidad}_i$) hacen matemáticamente imposible consumir más de lo detectado en la foto.
