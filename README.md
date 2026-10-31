# VisionBites

### Turning food inventory into smarter decisions with open-source AI.

**Hacktoberfest Hack Day Panama City 2026 | Open-Source AI Track**

**AI Model:** `gemma-4-26b-a4b-it` via Google Gemini API

---

## The Problem

Every day, small restaurants, cafeterias, and local food businesses must decide how to use their available ingredients efficiently.

In Panama, traditional food businesses such as *fondas* often work with changing inventory quantities, different ingredient priorities, and limited resources for planning food production.

At the same time, understanding the nutritional characteristics of prepared meals can be challenging without specialized tools.

**What if AI could help transform existing food inventory into practical, measurable cooking decisions?**

## Our Solution

**VisionBites** is an open-source AI-powered food production planning prototype designed to help small food businesses make better use of their available ingredients.

By combining generative AI, multimodal computer vision, nutritional reference data (INCAP & USDA), and mathematical optimization (PuLP), VisionBites transforms an ingredient inventory into a feasible meal production plan with exact macronutrients.

### Key Capabilities

- **Multimodal Visual Scanning:** Scan inventory or ingredients directly from photos or camera with fallback presets.
- **Smart Inventory:** Manage food inventory with quantities, expiration dates, and priority levels.
- **AI Recipe Generation:** Propose structured recipe candidates using Gemma 4 via Gemini API.
- **Nutritional Analysis:** Compute scientific macronutrients (calories, protein, carbohydrates, fats) using INCAP & USDA reference data.
- **Resource Optimization:** Calculate integer feasible serving quantities using mathematical linear programming without exceeding ingredient availability.
- **Two Planning Modes:**
  - **Rescue Mode (Aprovechamiento):** Prioritizes planned consumption of higher priority / at-risk ingredients.
  - **Balance Mode (Balance Nutricional):** Combines inventory priority with transparent food diversity.
- **Inventory Insights:** Visualize estimated ingredient consumption, remaining quantities, and mass conservation.

---

## 🚀 Getting Started & Execution Guide (Windows PowerShell)

### Prerequisites
- Python 3.11 or 3.12 installed.
- Internet connection (optional: fallback offline presets included if no key or offline).

### Quick Setup Steps

```powershell
# 1. Posicionarse en la carpeta del proyecto
cd c:\Users\edgar\Desktop\MLH

# 2. Crear entorno virtual (si no existe)
py -3.11 -m venv .venv

# 3. Instalar dependencias
.\.venv\Scripts\pip.exe install -r requirements.txt

# 4. Configurar variable de entorno (opcional para IA en vivo)
Copy-Item .env.example .env

# 5. Ejecutar la aplicación Streamlit
.\.venv\Scripts\python.exe -m streamlit run app.py
```

La aplicación abrirá automáticamente en tu navegador local en `http://localhost:8501`.

---

## 🧪 Automated Test Suite (T01 to T16)

Para verificar todas las garantías contractuales, matemáticas, de resiliencia y de visión:

```powershell
.\.venv\Scripts\python.exe -m pytest -q test_suite.py test_ui.py
```

### Verified Test Cases
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
- **T13**: Validación Zero-Trust con Pydantic.
- **T14**: Inmunidad del solver PuLP ante caracteres especiales en IDs de recetas y protección contra recetas con ingredientes faltantes.
- **T15**: Cobertura offline completa: muestras guiadas (nevera, alacena, sancocho) generan recetas compatibles en contingencia local.
- **T16**: Normalización determinista de sinónimos visuales hacia el catálogo oficial USDA/INCAP.

---

## 🇵🇦 Built for Panama

VisionBites focuses on the challenges faced by small food businesses in Panama. Rather than providing a generic chatbot, the prototype combines AI-generated suggestions with explicit data validation and mathematical resource constraints.

## Limitations

VisionBites is a hackathon prototype, not a commercial food safety or clinical nutrition system.
- Demo inventories are fictional.
- Nutritional calculations are estimates based on reference databases.
- The tool does not verify food safety, storage conditions, or allergens.
- It does not prescribe diets or claim to treat obesity.
- Planned ingredient utilization is not equivalent to measured waste reduction.

## Team

Developed during **Hacktoberfest Hack Day Panama City — October 31, 2026**.

- Development & UI — Edgar Saldaña
- Data & Validation — Gabriel Medina
- Product, Documentation & Submission — Isaac Delgado

## License

This repository is licensed under the **MIT License**. See [LICENSE](LICENSE).

---

**VisionBites — Better planning. Smarter kitchens. Less avoidable waste.**
