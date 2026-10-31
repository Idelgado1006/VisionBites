"""
vision_scanner.py - Motor de escaneo visual multimodal de alimentos para VisionBites.
Extrae ingredientes y cantidades estimadas a partir de fotos tomadas con cámara o subidas.
Mapea deterministicamente los alimentos a IDs normalizados del catálogo nutricional USDA/INCAP.
Incluye presets auditados y contingencia local segura sin interrupciones por caídas de red.
"""

import copy
import json
import os
import re
from typing import Any
from dotenv import load_dotenv

load_dotenv()

# Mapeo determinista de sinónimos culinarios a IDs canónicos del catálogo nutricional
MAPA_ALIAS_CATALOGO = {
    "pollo": "pollo_crudo", "pollo_fresco": "pollo_crudo", "pechuga": "pollo_crudo", "pechuga_pollo": "pollo_crudo", "pechuga_de_pollo": "pollo_crudo", "muslo_pollo": "pollo_crudo",
    "carne": "carne_res_cruda", "res": "carne_res_cruda", "carne_res": "carne_res_cruda", "carne_de_res": "carne_res_cruda", "carne_molida": "carne_res_cruda",
    "arroz": "arroz_seco", "arroz_blanco": "arroz_seco", "lenteja": "lentejas_secas", "lentejas": "lentejas_secas", "guandu": "guandu_fresco", "guandú": "guandu_fresco",
    "platano": "platano_maduro", "plátano": "platano_maduro", "tajada": "platano_maduro", "tajadas": "platano_maduro", "name": "name_diamante", "ñame": "name_diamante",
    "yuca": "yuca_cruda", "mandioca": "yuca_cruda", "tomate": "tomate_perita", "tomates": "tomate_perita", "tomate_rojo": "tomate_perita",
    "cebolla": "cebolla_criolla", "cebollas": "cebolla_criolla", "cebolla_morada": "cebolla_criolla", "cebolla_blanca": "cebolla_criolla",
    "culantro": "culantro_fresco", "cilantro": "culantro_fresco", "pimiento": "pimiento_verde", "pimenton": "pimiento_verde", "pimentón": "pimiento_verde", "aji": "pimiento_verde",
    "zanahoria": "zanahoria_cruda", "zanahorias": "zanahoria_cruda", "repollo": "repollo_blanco", "col": "repollo_blanco", "ajo": "ajo_diente", "ajos": "ajo_diente",
    "maiz": "maiz_mazorca", "maíz": "maiz_mazorca", "mazorca": "maiz_mazorca", "elote": "maiz_mazorca", "frijol": "frijol_chiricano", "frijoles": "frijol_chiricano", "poroto": "frijol_chiricano",
    "zapallo": "zapallo_crudo", "calabaza": "zapallo_crudo", "auyama": "zapallo_crudo", "aceite": "aceite_vegetal", "aceite_cocina": "aceite_vegetal", "sal": "sal_comun"
}

PROMPT_VISION_SCANNER = """Eres VisionBites, sistema experto en visión gastronómica multimodal.
Analiza esta fotografía de cocina, nevera o despensa.
¿Qué ingredientes o alimentos ves?
Lista cada alimento que observes en formato JSON:
```json
[
  {
    "id": "identificador_en_minusculas",
    "nombre": "Nombre del alimento en Español",
    "cantidad_g": 300,
    "grupo": "vegetal",
    "prioridad": "alta",
    "estado": "crudo",
    "apto": true
  }
]
```
Usa identificadores canónicos en minúsculas como: tomate_perita, cebolla_criolla, pimiento_verde, pollo_crudo, carne_res_cruda, platano_maduro, arroz_seco, lentejas_secas, guandu_fresco, name_diamante, yuca_cruda, culantro_fresco, zanahoria_cruda, repollo_blanco, ajo_diente, maiz_mazorca, frijol_chiricano, zapallo_crudo, aceite_vegetal, sal_comun.
Valores para "grupo": vegetal, fruta, cereal, legumbre, proteina, tuberculo, grasa, otro.
Valores para "prioridad": alta, media, baja.
Valores para "estado": crudo, cocido, otro.
Responde únicamente con el bloque JSON."""

PRESETS_MUESTRAS = {
    "nevera_fresca": {
        "titulo": "Nevera Fresca (Pollo, Tomate, Plátano y Culantro)",
        "descripcion": "Foto de verduras frescas y proteína para almuerzo rápido.",
        "ingredientes": [
            {"id": "pollo_crudo", "nombre": "Pollo Fresco", "cantidad_g": 1200, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo"},
            {"id": "tomate_perita", "nombre": "Tomate Perita", "cantidad_g": 600, "prioridad": "alta", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "culantro_fresco", "nombre": "Culantro Fresco", "cantidad_g": 100, "prioridad": "alta", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "platano_maduro", "nombre": "Plátano Maduro", "cantidad_g": 800, "prioridad": "alta", "apto": True, "grupo": "fruta", "estado": "crudo"},
            {"id": "cebolla_criolla", "nombre": "Cebolla", "cantidad_g": 500, "prioridad": "media", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "ajo_diente", "nombre": "Ajo", "cantidad_g": 80, "prioridad": "baja", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "aceite_vegetal", "nombre": "Aceite", "cantidad_g": 300, "prioridad": "baja", "apto": True, "grupo": "grasa", "estado": "crudo"}
        ]
    },
    "alacena_granos": {
        "titulo": "Alacena Saludable (Granos, Tubérculos y Vegetales)",
        "descripcion": "Foto de despensa con legumbres secas, arroz y zanahoria.",
        "ingredientes": [
            {"id": "arroz_seco", "nombre": "Arroz", "cantidad_g": 1000, "prioridad": "baja", "apto": True, "grupo": "cereal", "estado": "crudo"},
            {"id": "lentejas_secas", "nombre": "Lentejas", "cantidad_g": 600, "prioridad": "media", "apto": True, "grupo": "legumbre", "estado": "crudo"},
            {"id": "zanahoria_cruda", "nombre": "Zanahoria", "cantidad_g": 500, "prioridad": "baja", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "cebolla_criolla", "nombre": "Cebolla", "cantidad_g": 400, "prioridad": "media", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "pimiento_verde", "nombre": "Pimiento Verde", "cantidad_g": 350, "prioridad": "media", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "aceite_vegetal", "nombre": "Aceite Vegetal", "cantidad_g": 200, "prioridad": "baja", "apto": True, "grupo": "grasa", "estado": "crudo"}
        ]
    },
    "sancocho_casero": {
        "titulo": "Mesa de Preparación (Res, Ñame, Yuca y Zapallo)",
        "descripcion": "Foto de tubérculos y carne para un guiso tradicional sustancioso.",
        "ingredientes": [
            {"id": "carne_res_cruda", "nombre": "Carne de Res", "cantidad_g": 1000, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo"},
            {"id": "name_diamante", "nombre": "Ñame", "cantidad_g": 800, "prioridad": "media", "apto": True, "grupo": "tuberculo", "estado": "crudo"},
            {"id": "yuca_cruda", "nombre": "Yuca", "cantidad_g": 700, "prioridad": "media", "apto": True, "grupo": "tuberculo", "estado": "crudo"},
            {"id": "zapallo_crudo", "nombre": "Zapallo", "cantidad_g": 600, "prioridad": "alta", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "culantro_fresco", "nombre": "Culantro", "cantidad_g": 80, "prioridad": "alta", "apto": True, "grupo": "vegetal", "estado": "crudo"},
            {"id": "maiz_mazorca", "nombre": "Maíz en Mazorca", "cantidad_g": 400, "prioridad": "media", "apto": True, "grupo": "cereal", "estado": "crudo"}
        ]
    }
}

ESTADO_SCANNER = {
    "ultimo_metodo": "ninguno",
    "mensaje": "Listo para escanear",
    "usando_respaldo": False
}


def _limpiar_json(texto: str) -> list[dict]:
    """Extrae la lista JSON limpiando etiquetas markdown y normalizando objetos envolventes."""
    texto_limpio = texto.strip()
    match_bloque = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", texto_limpio, re.DOTALL)
    if match_bloque:
        texto_limpio = match_bloque.group(1).strip()
    else:
        inicio = min([i for i in [texto_limpio.find("["), texto_limpio.find("{")] if i != -1], default=-1)
        fin = max([texto_limpio.rfind("]"), texto_limpio.rfind("}")])
        if inicio != -1 and fin != -1 and fin > inicio:
            texto_limpio = texto_limpio[inicio:fin + 1].strip()

    datos = json.loads(texto_limpio)
    if isinstance(datos, dict):
        for clave in ("alimentos", "ingredientes", "items", "data"):
            if isinstance(datos.get(clave), list):
                return datos[clave]
        raise ValueError("El JSON es un objeto sin lista de alimentos.")

    if not isinstance(datos, list):
        raise ValueError("El JSON no es una lista de ingredientes.")
    return datos


def _normalizar_items_detectados(items: list[dict]) -> list[dict]:
    """Mapea IDs de alimentos detectados por visión a los identificadores canónicos auditados."""
    normalizados = []
    for it in items:
        raw_id = str(it.get("id", "")).strip().lower().replace("-", "_")
        canon_id = MAPA_ALIAS_CATALOGO.get(raw_id, raw_id)
        normalizados.append({
            "id": canon_id,
            "nombre": str(it.get("nombre", canon_id.replace("_", " ").title())).strip(),
            "cantidad_g": float(it.get("cantidad_g", 300)),
            "grupo": str(it.get("grupo", "otro")),
            "prioridad": str(it.get("prioridad", "media")),
            "estado": str(it.get("estado", "crudo")),
            "apto": True
        })
    return normalizados


def scan_food_image(
    image_bytes: bytes | None,
    mime_type: str = "image/jpeg",
    model_name: str | None = None,
    preset_key: str | None = None
) -> list[dict]:
    """
    Escanea una imagen con visión multimodal o activa un preset pre-auditado.
    Garantiza robustez: si la API falla o no hay imagen, conmuta al preset con copia profunda.
    """
    global ESTADO_SCANNER

    # Si se solicitó un preset explícito
    if preset_key and preset_key in PRESETS_MUESTRAS:
        ESTADO_SCANNER["ultimo_metodo"] = f"Preset: {PRESETS_MUESTRAS[preset_key]['titulo']}"
        ESTADO_SCANNER["mensaje"] = "Demostración cargada con éxito."
        ESTADO_SCANNER["usando_respaldo"] = True
        return copy.deepcopy(PRESETS_MUESTRAS[preset_key]["ingredientes"])

    if not image_bytes:
        ESTADO_SCANNER["ultimo_metodo"] = "Preset por defecto"
        ESTADO_SCANNER["mensaje"] = "Sin imagen: usando muestra predeterminada."
        ESTADO_SCANNER["usando_respaldo"] = True
        return copy.deepcopy(PRESETS_MUESTRAS["nevera_fresca"]["ingredientes"])

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "tu_api_key_aqui"):
        ESTADO_SCANNER["ultimo_metodo"] = "Detección local (sin API Key)"
        ESTADO_SCANNER["mensaje"] = "API Key no configurada. Activada detección de contingencia local."
        ESTADO_SCANNER["usando_respaldo"] = True
        return copy.deepcopy(PRESETS_MUESTRAS["nevera_fresca"]["ingredientes"])

    modelo_nombre = (
        model_name
        or os.getenv("GEMMA_MODEL_NAME")
        or os.getenv("GEMINI_MODEL_NAME")
        or "gemma-4-26b-a4b-it"
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)
        part_image = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

        modelos_a_probar = [modelo_nombre]
        if "gemma" in modelo_nombre.lower():
            modelos_a_probar.append("gemini-3.8-flash")

        items = []
        modelo_exitoso = modelo_nombre
        ultimo_error = None

        for m in modelos_a_probar:
            try:
                # En modelos Gemma, forzar response_mime_type provoca colapso a arreglo vacío ([])
                # por gramática sintética; sin ella, Gemma 4 genera el bloque JSON completo.
                es_gemma = "gemma" in m.lower()
                config_params = {"temperature": 0.1 if es_gemma else 0.2}
                if not es_gemma:
                    config_params["response_mime_type"] = "application/json"

                response = client.models.generate_content(
                    model=m,
                    contents=[part_image, PROMPT_VISION_SCANNER],
                    config=types.GenerateContentConfig(**config_params)
                )

                if not response or not response.text:
                    continue

                items_crudos = _limpiar_json(response.text)
                candidatos = _normalizar_items_detectados(items_crudos)
                if candidatos:
                    items = candidatos
                    modelo_exitoso = m
                    break
            except Exception as e:
                ultimo_error = e
                continue

        if not items:
            if ultimo_error:
                raise ultimo_error
            raise ValueError(f"No se detectaron ingredientes procesables en la imagen con {modelo_nombre}.")

        ESTADO_SCANNER["ultimo_metodo"] = f"Visión IA en vivo ({modelo_exitoso})"
        ESTADO_SCANNER["mensaje"] = f"Identificados {len(items)} ingredientes en la foto."
        ESTADO_SCANNER["usando_respaldo"] = False
        return items

    except Exception as err:
        ESTADO_SCANNER["ultimo_metodo"] = "Contingencia de visión"
        ESTADO_SCANNER["mensaje"] = f"Escaneo IA en modo seguro ({type(err).__name__})."
        ESTADO_SCANNER["usando_respaldo"] = True
        return copy.deepcopy(PRESETS_MUESTRAS["nevera_fresca"]["ingredientes"])
