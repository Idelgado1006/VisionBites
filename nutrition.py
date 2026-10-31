"""
nutrition.py - Carga del catálogo nutricional y cálculo de macronutrientes por porción.
Garantiza fidelidad cuantitativa estricta: datos auditados (USDA/INCAP), indexación
resiliente a estados físicos y resolución segura de rutas de archivos.
"""

import csv
import math
import os
from typing import Any

# Columnas obligatorias mínimas para cálculo nutricional completo
CABECERAS_NUTRICION_REQUERIDAS = {
    "id", "estado", "kcal_100g", "proteina_g_100g", "carbohidratos_g_100g", "grasa_g_100g"
}


def _resolver_ruta_segura(ruta: str) -> str:
    """Resuelve la ruta absoluta si la relativa no se encuentra en el directorio de trabajo."""
    if os.path.exists(ruta):
        return ruta
    ruta_relativa_modulo = os.path.join(os.path.dirname(os.path.abspath(__file__)), ruta)
    if os.path.exists(ruta_relativa_modulo):
        return ruta_relativa_modulo
    return ruta


def _parse_float_or_none(val: Any) -> float | None:
    """Convierte valores a float respetando valores nulos o ausentes."""
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str == "" or val_str.lower() in ("null", "none", "nan", "sin dato"):
        return None
    try:
        num = float(val_str)
        return None if (math.isnan(num) or math.isinf(num)) else num
    except (ValueError, TypeError):
        return None


def load_nutrition(path: str = "data/nutricion.csv") -> dict[str, dict]:
    """
    Carga el catálogo nutricional referenciado desde CSV con soporte UTF-8-SIG (anti-BOM).
    Indexa por ID directo y por clave compuesta 'id:estado'.
    """
    ruta_resuelta = _resolver_ruta_segura(path)
    if not os.path.exists(ruta_resuelta):
        raise FileNotFoundError(f"Catálogo nutricional no encontrado en la ruta: '{path}'")

    nutrition_db: dict[str, dict] = {}

    with open(ruta_resuelta, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = [str(col).strip() for col in (reader.fieldnames or [])]
        if not CABECERAS_NUTRICION_REQUERIDAS.issubset(set(fieldnames)):
            missing = CABECERAS_NUTRICION_REQUERIDAS - set(fieldnames)
            raise ValueError(f"El archivo {path} carece de cabeceras obligatorias: {missing}")

        for num_fila, row in enumerate(reader, start=2):
            item_id = str(row.get("id", "")).strip().lower()
            if not item_id:
                continue
            estado = str(row.get("estado", "crudo")).strip().lower()

            try:
                kcal = float(row["kcal_100g"])
                proteina = float(row["proteina_g_100g"])
                carbs = float(row["carbohidratos_g_100g"])
                grasa = float(row["grasa_g_100g"])
            except (ValueError, KeyError, TypeError) as err:
                raise ValueError(f"Fila {num_fila} ('{item_id}'): Valores nutricionales numéricos inválidos ({err}).")

            fibra = _parse_float_or_none(row.get("fibra_g_100g"))
            sodio = _parse_float_or_none(row.get("sodio_mg_100g"))
            fuente = str(row.get("fuente", "Sin fuente especificada")).strip()

            info = {
                "id": item_id,
                "estado": estado,
                "kcal_100g": kcal,
                "proteina_g_100g": proteina,
                "carbohidratos_g_100g": carbs,
                "grasa_g_100g": grasa,
                "fibra_g_100g": fibra,
                "sodio_mg_100g": sodio,
                "fuente": fuente
            }

            # Indexar por id y por id:estado para resolver variantes (ej. cocido vs crudo)
            nutrition_db[item_id] = info
            nutrition_db[f"{item_id}:{estado}"] = info

    return nutrition_db


def nutrition_per_serving(recipe: dict, nutrition_db: dict) -> dict[str, float | None]:
    """
    Calcula los macronutrientes y energía por porción de una receta según la fórmula:
    N(r) = SUMA [ (cantidad_g_por_porcion(i) / 100) * N_100g(i) ]
    
    T10: Si un ingrediente requerido no existe en el catálogo, lanza ValueError
    para evitar atribuir números ficticios al plan.
    """
    ingredientes = recipe.get("ingredientes", [])
    if not ingredientes:
        return {
            "kcal": 0.0, "proteina_g": 0.0, "carbohidratos_g": 0.0, "grasa_g": 0.0,
            "fibra_g": None, "sodio_mg": None
        }

    total_kcal = 0.0
    total_proteina = 0.0
    total_carbs = 0.0
    total_grasa = 0.0
    total_fibra: float = 0.0
    total_sodio: float = 0.0

    tiene_fibra_completa = True
    tiene_sodio_completo = True

    for ing in ingredientes:
        ing_id = str(ing.get("id", "")).strip().lower()
        try:
            cant_g = float(ing.get("cantidad_g_por_porcion", 0.0))
            if math.isnan(cant_g) or math.isinf(cant_g) or cant_g < 0:
                raise ValueError("Cantidad no válida.")
        except (ValueError, TypeError):
            raise ValueError(f"Cantidad por porción inválida para '{ing_id}'.")

        factor = cant_g / 100.0

        # Resolución en dos pasos: buscar id:estado si fue provisto, o id directo
        estado_ing = str(ing.get("estado", "")).strip().lower()
        nutri = nutrition_db.get(f"{ing_id}:{estado_ing}") or nutrition_db.get(ing_id)

        if not nutri:
            # T10: Catálogo sin ID requerido -> Jamás inventar macros
            raise ValueError(f"Ingrediente '{ing_id}' no encontrado en el catálogo nutricional auditado.")

        total_kcal += factor * nutri["kcal_100g"]
        total_proteina += factor * nutri["proteina_g_100g"]
        total_carbs += factor * nutri["carbohidratos_g_100g"]
        total_grasa += factor * nutri["grasa_g_100g"]

        fibra_val = nutri.get("fibra_g_100g")
        if fibra_val is not None and tiene_fibra_completa:
            total_fibra += factor * fibra_val
        else:
            tiene_fibra_completa = False

        sodio_val = nutri.get("sodio_mg_100g")
        if sodio_val is not None and tiene_sodio_completo:
            total_sodio += factor * sodio_val
        else:
            tiene_sodio_completo = False

    return {
        "kcal": round(total_kcal, 2),
        "proteina_g": round(total_proteina, 2),
        "carbohidratos_g": round(total_carbs, 2),
        "grasa_g": round(total_grasa, 2),
        "fibra_g": round(total_fibra, 2) if tiene_fibra_completa else None,
        "sodio_mg": round(total_sodio, 2) if tiene_sodio_completo else None
    }
