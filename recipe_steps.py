"""
recipe_steps.py - Generador de recetas paso a paso con Gemma 4 para VisionBites.
Transforma los platos asignados en guías culinarias con mise en place, tiempos,
técnicas de fuego y consejos del chef adaptados estrictamente a las porciones e ingredientes.
"""

import os
from typing import Any
from dotenv import load_dotenv

load_dotenv()

PROMPT_PASO_A_PASO_GEMMA = """Eres el chef de cocina casera de VisionBites.
El usuario va a cocinar el siguiente plato confirmado de su despensa:
Plato: "{nombre_plato}"
Porciones a preparar: {porciones}
Tiempo estimado: {tiempo_min} minutos
Técnica culinaria base: {metodo_base}

Ingredientes EXACTOS calculados para estas {porciones} porciones:
{ingredientes_texto}

Instrucciones:
Escribe la RECETA PASO A PASO con esta estructura limpia y humana:
1. **Resumen y tiempos:** Breve descripción del plato y tiempo total estimado.
2. **Preparación previa (Mise en place):** Lista clara de los ingredientes con sus cortes (juliana, cubos, picado fino, etc.) usando EXACTAMENTE las cantidades en gramos indicadas.
3. **Paso a paso de cocción:** Pasos numerados claros (Paso 1, Paso 2, etc.) con tiempos aproximados en minutos, orden cronológico de incorporación de ingredientes, niveles de fuego (bajo, medio, alto) y señales visuales de cocción (ej. "hasta que dore", "traslúcido", "reduzca a la salsa").
4. **Consejo del chef:** Un truco práctico y directo para maximizar el sabor con estos ingredientes exactos, sin asumir que el usuario tiene ingredientes adicionales fuera de la lista.

Tono: Claro, cálido, profesional y sin florituras artificiales ni clichés."""


def _generar_paso_a_paso_offline(plato: dict, ingredientes_detalle: list[dict], porciones: int) -> str:
    """Genera una guía paso a paso coherente y estructurada para modo sin conexión."""
    nombre = plato.get("nombre", "Plato Casero")
    tiempo = plato.get("tiempo_min", 25)
    metodo = plato.get("metodo", "Cocinar integrando sabores a fuego medio.")
    
    lineas_mise = []
    for ing in ingredientes_detalle:
        nom = ing.get("nombre", ing.get("id", "Ingrediente"))
        g = ing.get("cantidad_g", 0)
        lineas_mise.append(f"- **{nom}**: {g:.0f} g (lavado y cortado en trozos parejos para cocción uniforme)")
    
    mise_str = "\n".join(lineas_mise) if lineas_mise else "- Ingredientes de la despensa medidos según porción."
    
    return f"""### 1. Resumen y tiempos
Una preparación reconfortante y equilibrada para **{porciones} {'porción' if porciones == 1 else 'porciones'}**.
- **Tiempo total estimado:** {tiempo} minutos.
- **Técnica base:** {metodo}

### 2. Preparación previa (Mise en place)
{mise_str}

### 3. Paso a paso de cocción
* **Paso 1 (5 a 7 min):** En una sartén u olla adecuada, añade la materia grasa o inicia a fuego medio-alto. Incorpora primero los ingredientes que requieren mayor dorado (proteínas o aromáticos) hasta sellar sus jugos y notar un aroma tostado ligero.
* **Paso 2 (6 a 8 min):** Reduce a fuego medio. Agrega los vegetales y tubérculos cortados. Remueve suavemente para que se impregnen de los jugos del fondo de cocción sin romper su estructura.
* **Paso 3 (8 a 12 min):** Ajusta a fuego medio-bajo, tapa parcialmente y permite que los ingredientes liberen su humedad natural creando una salsa jugosa y unificada. Comprueba que las texturas estén tiernas al tacto.

### 4. Consejo del chef
Controla el fuego y permite que los ingredientes doren antes de remover continuamente. Ese sellado inicial aportará toda la profundidad de sabor al plato sin necesidad de sazonadores artificiales."""


def generate_step_by_step_recipe(
    plato: dict,
    ingredientes_detalle: list[dict],
    porciones: int,
    model_name: str | None = None,
    offline: bool = False
) -> dict[str, Any]:
    """
    Invoca a Gemma 4 para redactar la receta detallada paso a paso.
    Si se fuerza offline o la API falla, conmuta al redactor seguro local.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    modelo = (
        model_name
        or os.getenv("GEMMA_MODEL_NAME")
        or os.getenv("GEMINI_MODEL_NAME")
        or "gemma-4-26b-a4b-it"
    )
    
    en_pytest = bool(os.getenv("PYTEST_CURRENT_TEST") and not os.getenv("LIVE_API"))
    sin_api_key = not api_key or api_key.strip() in ("", "tu_api_key_aqui")
    
    if offline or en_pytest or sin_api_key:
        contenido = _generar_paso_a_paso_offline(plato, ingredientes_detalle, porciones)
        return {
            "modelo": "Gemma 4 (Guía local auditada)",
            "usando_respaldo": True,
            "texto": contenido,
            "plato_id": plato.get("id", ""),
            "porciones": porciones
        }
    
    ingredientes_texto = "\n".join(
        f"- {i.get('nombre', i.get('id'))}: {float(i.get('cantidad_g', 0)):.0f} g"
        for i in ingredientes_detalle
    )
    
    prompt = PROMPT_PASO_A_PASO_GEMMA.format(
        nombre_plato=plato.get("nombre", "Plato"),
        porciones=porciones,
        tiempo_min=plato.get("tiempo_min", 25),
        metodo_base=plato.get("metodo", "Cocinar a fuego medio"),
        ingredientes_texto=ingredientes_texto
    )
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=modelo,
            contents=prompt,
        )
        
        if not response or not response.text:
            raise ValueError(f"Respuesta vacía de Gemma ({modelo}).")
            
        return {
            "modelo": f"Gemma 4 ({modelo})",
            "usando_respaldo": False,
            "texto": response.text.strip(),
            "plato_id": plato.get("id", ""),
            "porciones": porciones
        }
    except Exception as err:
        contenido = _generar_paso_a_paso_offline(plato, ingredientes_detalle, porciones)
        return {
            "modelo": f"Gemma 4 (Local por {type(err).__name__})",
            "usando_respaldo": True,
            "texto": contenido,
            "plato_id": plato.get("id", ""),
            "porciones": porciones
        }
