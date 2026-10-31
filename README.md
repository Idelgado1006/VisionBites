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

By combining generative AI, nutritional reference data, and mathematical optimization, VisionBites aims to turn an ingredient inventory into a feasible meal production plan.

### Planned Capabilities

- **Smart Inventory:** Import food inventory with quantities and priority levels.
- **AI Recipe Generation:** Generate candidate recipes using Gemma 4.
- **Nutritional Analysis:** Estimate calories, protein, carbohydrates, and fats using reference data.
- **Resource Optimization:** Calculate feasible serving quantities without exceeding ingredient availability.
- **Two Planning Modes:** Compare inventory rescue with nutritional diversity considerations.
- **Inventory Insights:** Visualize estimated ingredient consumption, remaining quantities, and planned utilization.

*Final implemented features will be confirmed after testing.*

##  How Gemma 4 Powers VisionBites

VisionBites uses the open-weight Gemma 4 model through Google's Gemini API.

The system separates creative generation from numerical decision-making:

1. **Input:** A food business provides an inventory of available ingredients.
2. **AI Generation:** Gemma 4 proposes structured recipe candidates using the provided ingredients.
3. **Validation:** The application checks recipe ingredients and quantities.
4. **Nutrition:** An independent nutritional catalog provides nutrient values.
5. **Optimization:** A mathematical algorithm determines feasible serving quantities.
6. **Results:** The interface presents a production plan and estimated inventory utilization.

### AI Model

- **Model:** `gemma-4-26b-a4b-it`
- **Provider:** Google Gemini API
- **Integration:** Google GenAI Python SDK
- **API/SDK versions:** To be documented after integration testing.

Gemma 4 does not supply the nutritional reference values or independently determine inventory consumption.

##  Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Gemma 4 | Candidate recipe generation |
| Gemini API | Hosted model inference |
| Streamlit | Web application |
| Pandas | Data processing |
| PuLP | Mathematical optimization |
| CSV | Demo inventory and nutritional reference data |

## Getting Started

Installation and execution commands will be finalized after the application is integrated and tested.

A Gemini API key is required for live Gemma 4 generation.

[Create a Gemini API key](https://aistudio.google.com/apikey)

API credentials must be stored locally and must never be committed to this repository.

## Expected Demonstration

The prototype is intended to demonstrate a workflow in which an inventory of 20 fictional food products is converted into recipe candidates, feasible servings, estimated nutrient values, and remaining inventory quantities.

The demonstration will compare two optimization modes:

**Rescue Mode:** Prioritizes the planned consumption of ingredients marked as higher priority.

**Balance Mode:** Combines inventory priority with a transparent food-diversity score.

## 🇵🇦 Built for Panama

VisionBites focuses on the challenges faced by small food businesses in Panama.

Rather than providing a generic chatbot, the prototype is designed to combine AI-generated suggestions with explicit data validation and mathematical resource constraints.

## Limitations

VisionBites is a hackathon prototype, not a commercial food safety or clinical nutrition system.

- Demo inventories are fictional.
- Nutritional calculations are estimates based on reference databases.
- The tool does not verify food safety, storage conditions, or allergens.
- It does not prescribe diets or claim to treat obesity.
- Planned ingredient utilization is not equivalent to measured waste reduction.

## Team

Developed during **Hacktoberfest Hack Day Panama City — October 31, 2026**.

- Development & UI — [Contributor]
- Data & Validation — [Contributor]
- Product, Documentation & Submission — [Contributor]

## AI-Assisted Development

This project may use AI-assisted development tools. All submitted code, documentation, calculations, and results are the responsibility of the project contributors and must be reviewed before submission.

## License

This repository is licensed under the **MIT License**. See [LICENSE](LICENSE).

---

**VisionBites — Better planning. Smarter kitchens. Less avoidable waste.**
