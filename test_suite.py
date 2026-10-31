"""
test_suite.py - Batería de pruebas automatizadas T01 a T10 para RESCATE 24.
Verifica que las garantías cuantitativas y de seguridad se cumplan rigurosamente.
"""

import copy
import pytest
from validator import validate_inventory, validate_recipes
from nutrition import load_nutrition, nutrition_per_serving
from optimizer import optimize
from ai_engine import generate_recipes, ULTIMO_ESTADO_IA


def test_t01_carga_csv_valido():
    """T01: Carga CSV de 20 alimentos válidos genera un plan exitoso."""
    import csv
    with open("data/inventario_demo.csv", mode="r", encoding="utf-8") as f:
        reader = list(csv.DictReader(f))
    
    assert len(reader) == 20
    inventario_valido = validate_inventory(reader)
    assert len(inventario_valido) == 20

    nutricion_db = load_nutrition("data/nutricion.csv")
    recetas = generate_recipes(inventario_valido)
    recetas_validas, _ = validate_recipes(recetas, inventario_valido)
    
    plan = optimize(inventario_valido, recetas_validas, nutricion_db, mode="rescate")
    assert plan["estado"] == "ok"
    assert plan["metricas"]["porciones_totales"] > 0
    assert plan["metricas"]["kg_utilizado"] > 0


def test_t02_error_duplicado_y_negativo():
    """T02: Cantidad -10g o ID duplicado -> Error claro; no se calcula un plan falso."""
    # Prueba ID duplicado
    datos_duplicados = [
        {"id": "arroz", "nombre": "Arroz", "cantidad_g": 500, "prioridad": "alta", "apto": True, "grupo": "cereal", "estado": "crudo"},
        {"id": "arroz", "nombre": "Arroz Repetido", "cantidad_g": 300, "prioridad": "alta", "apto": True, "grupo": "cereal", "estado": "crudo"}
    ]
    with pytest.raises(ValueError, match="ID duplicado"):
        validate_inventory(datos_duplicados)

    # Prueba cantidad negativa
    datos_negativos = [
        {"id": "pollo", "nombre": "Pollo", "cantidad_g": -10.0, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo"}
    ]
    with pytest.raises(ValueError, match="negativa"):
        validate_inventory(datos_negativos)


def test_t03_exclusion_no_apto_o_vencido():
    """T03: Ingrediente apto=false o fecha pasada queda fuera de optimización."""
    datos = [
        {"id": "pollo_vigente", "nombre": "Pollo", "cantidad_g": 1000, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo", "fecha_limite": "2026-11-05"},
        {"id": "carne_no_apta", "nombre": "Carne", "cantidad_g": 1000, "prioridad": "alta", "apto": False, "grupo": "proteina", "estado": "crudo", "fecha_limite": "2026-11-05"},
        {"id": "pescado_vencido", "nombre": "Pescado", "cantidad_g": 1000, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo", "fecha_limite": "2026-10-20"}
    ]
    resultado = validate_inventory(datos, fecha_referencia="2026-10-31")
    ids_admitidos = [x["id"] for x in resultado]
    assert ids_admitidos == ["pollo_vigente"]


def test_t04_rechazo_ingrediente_inexistente():
    """T04: Gemma genera ID inexistente -> Receta rechazada con motivo visible/registrado."""
    inventario = [
        {"id": "arroz", "nombre": "Arroz", "cantidad_g": 500, "prioridad": "alta", "apto": True, "grupo": "cereal", "estado": "crudo"}
    ]
    recetas_con_fantasma = [
        {
            "id": "receta_magica",
            "nombre": "Plato Mágico",
            "ingredientes": [
                {"id": "arroz", "cantidad_g_por_porcion": 100},
                {"id": "trufas_negras_fantasmas", "cantidad_g_por_porcion": 10}
            ],
            "metodo": "Mezclar.",
            "tiempo_min": 20
        }
    ]
    aprobadas, motivos = validate_recipes(recetas_con_fantasma, inventario)
    assert len(aprobadas) == 0
    assert any("trufas_negras_fantasmas" in m for m in motivos)


def test_t05_stock_insuficiente():
    """T05: Inventario insuficiente para una receta -> Receta recibe 0 porciones."""
    inventario = [
        {"id": "pollo_crudo", "nombre": "Pollo", "cantidad_g": 50, "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo"}
    ]
    # La receta requiere 160g de pollo por porción, pero solo hay 50g
    recetas = [
        {
            "id": "pollo_plato",
            "nombre": "Pollo",
            "ingredientes": [{"id": "pollo_crudo", "cantidad_g_por_porcion": 160}],
            "metodo": "Cocer.",
            "tiempo_min": 30
        }
    ]
    nutricion_db = {"pollo_crudo": {"kcal_100g": 120, "proteina_g_100g": 20, "carbohidratos_g_100g": 0, "grasa_g_100g": 2, "fibra_g_100g": 0}}
    plan = optimize(inventario, recetas, nutricion_db, mode="rescate")
    assert plan["platos"][0]["porciones"] == 0
    assert plan["inventario"][0]["usado_g"] == 0.0


def test_t06_calculo_exacto_proteina():
    """T06: Cálculo de proteína para 50 g con 10 g/100 g -> Exactamente 5.0 g."""
    receta = {
        "id": "test_r",
        "ingredientes": [{"id": "alimento_x", "cantidad_g_por_porcion": 50}]
    }
    db = {
        "alimento_x": {
            "kcal_100g": 100.0,
            "proteina_g_100g": 10.0,
            "carbohidratos_g_100g": 5.0,
            "grasa_g_100g": 1.0,
            "fibra_g_100g": None,
            "sodio_mg_100g": None
        }
    }
    macros = nutrition_per_serving(receta, db)
    assert macros["proteina_g"] == 5.0


def test_t07_conservacion_de_masa():
    """T07: Para cada ingrediente: inicial = usado + resto con tolerancia < 0.01 g."""
    import csv
    with open("data/inventario_demo.csv", mode="r", encoding="utf-8") as f:
        inv = validate_inventory(list(csv.DictReader(f)))
    nutri = load_nutrition("data/nutricion.csv")
    recetas, _ = validate_recipes(generate_recipes(inv), inv)
    
    plan = optimize(inv, recetas, nutri, mode="rescate")
    for item in plan["inventario"]:
        diferencia = abs((item["usado_g"] + item["restante_g"]) - item["inicial_g"])
        assert diferencia < 0.01, f"Fallo en {item['id']}: inicial={item['inicial_g']}, suma={item['usado_g'] + item['restante_g']}"


def test_t08_reoptimizacion_sin_invocar_ia():
    """T08: Cambiar modo con mismas recetas recalcula localmente sin invocar la IA."""
    import csv
    with open("data/inventario_demo.csv", mode="r", encoding="utf-8") as f:
        inv = validate_inventory(list(csv.DictReader(f)))
    nutri = load_nutrition("data/nutricion.csv")
    recetas, _ = validate_recipes(generate_recipes(inv), inv)

    plan_rescate = optimize(inv, recetas, nutri, mode="rescate")
    plan_balance = optimize(inv, recetas, nutri, mode="balance")

    assert plan_rescate["modo"] == "rescate"
    assert plan_balance["modo"] == "balance"
    # Ambos planes son consistentes y ejecutados de forma determinista
    assert plan_rescate["estado"] == "ok"
    assert plan_balance["estado"] == "ok"


def test_t09_fallback_por_corte_de_red():
    """T09: Si la API no está disponible, se activa el respaldo con etiqueta visible."""
    # Simulamos entorno sin GEMINI_API_KEY
    import os
    antigua_key = os.environ.get("GEMINI_API_KEY")
    try:
        os.environ["GEMINI_API_KEY"] = ""
        recetas = generate_recipes([])
        assert len(recetas) > 0
        assert ULTIMO_ESTADO_IA["usando_respaldo"] is True
    finally:
        if antigua_key is not None:
            os.environ["GEMINI_API_KEY"] = antigua_key


def test_t10_error_por_ingrediente_sin_nutricion():
    """T10: Catálogo nutricional sin ID requerido -> Error o nunca inventar macros."""
    receta_huerfana = {
        "id": "plato_raro",
        "ingredientes": [{"id": "ingrediente_desconocido", "cantidad_g_por_porcion": 100}]
    }
    with pytest.raises(ValueError, match="no encontrado en el catálogo"):
        nutrition_per_serving(receta_huerfana, {})


def test_t11_vision_scanner_preset():
    """T11: VisionBites - Escaneo visual con presets devuelve ingredientes validables."""
    from vision_scanner import scan_food_image
    items = scan_food_image(None, preset_key="nevera_fresca")
    assert len(items) >= 5
    validados = validate_inventory(items)
    assert len(validados) == len(items)
    assert all(i["cantidad_g"] > 0 for i in validados)


def test_t12_vision_scanner_fallback_sin_imagen():
    """T12: VisionBites - Manejo seguro ante imagen ausente o error sin romper la app."""
    from vision_scanner import scan_food_image, ESTADO_SCANNER
    items = scan_food_image(None)
    assert len(items) > 0
    assert ESTADO_SCANNER["usando_respaldo"] is True


def test_t13_pydantic_zero_trust_y_tildes():
    """T13: Pydantic zero-trust rechaza NaN/Inf y normaliza acentos en grupos alimentarios."""
    import math
    # Rechazo estricto de NaN en cantidad_g
    datos_nan = [
        {"id": "pollo", "nombre": "Pollo", "cantidad_g": float("nan"), "prioridad": "alta", "apto": True, "grupo": "proteina", "estado": "crudo"}
    ]
    with pytest.raises(ValueError, match="número válido"):
        validate_inventory(datos_nan)

    # Aceptación y normalización de grupo con tilde ("proteína" -> "proteina", "tubérculo" -> "tuberculo")
    datos_tildes = [
        {"id": "pollo", "nombre": "Pollo", "cantidad_g": 500, "prioridad": "alta", "apto": True, "grupo": "proteína", "estado": "crudo"},
        {"id": "yuca", "nombre": "Yuca", "cantidad_g": 400, "prioridad": "media", "apto": True, "grupo": "tubérculo", "estado": "crudo"}
    ]
    validados = validate_inventory(datos_tildes)
    assert validados[0]["grupo"] == "proteina"
    assert validados[1]["grupo"] == "tuberculo"


def test_t14_optimizador_caracteres_especiales_e_ingrediente_ausente():
    """T14: El solver maneja IDs con caracteres especiales y recetas con ingredientes sin stock sin arrojar KeyError."""
    inv = [{"id": "arroz_seco", "nombre": "Arroz", "cantidad_g": 500.0, "prioridad": "alta", "apto": True, "grupo": "cereal", "estado": "crudo"}]
    recetas = [
        {
            "id": "receta especial / con espacios - (v1.0)",
            "nombre": "Plato Complejo",
            "ingredientes": [
                {"id": "arroz_seco", "cantidad_g_por_porcion": 100},
                {"id": "ingrediente_fantasma", "cantidad_g_por_porcion": 50}
            ],
            "metodo": "Cocer.",
            "tiempo_min": 25
        }
    ]
    db = {
        "arroz_seco": {"kcal_100g": 365, "proteina_g_100g": 7.1, "carbohidratos_g_100g": 80, "grasa_g_100g": 0.7},
        "ingrediente_fantasma": {"kcal_100g": 100, "proteina_g_100g": 10, "carbohidratos_g_100g": 10, "grasa_g_100g": 1}
    }
    plan = optimize(inv, recetas, db, mode="balance")
    assert plan["estado"] == "ok"
    assert plan["platos"][0]["porciones"] == 0


def test_t15_todas_las_muestras_generan_recetas_offline():
    """T15: Todas las muestras guiadas (nevera, alacena, sancocho) producen recetas válidas sin internet."""
    from vision_scanner import scan_food_image
    from ai_engine import generate_recipes
    for preset in ["nevera_fresca", "alacena_granos", "sancocho_casero"]:
        items = validate_inventory(scan_food_image(None, preset_key=preset))
        recetas = generate_recipes(items)
        validas, motivos = validate_recipes(recetas, items)
        assert len(validas) >= 1, f"El preset '{preset}' falló en contingencia offline. Motivos: {motivos}"


def test_t16_normalizador_alias_vision():
    """T16: Detección visual normaliza términos coloquiales a IDs canónicos del catálogo."""
    from vision_scanner import _normalizar_items_detectados
    crudos = [
        {"id": "pechuga_pollo", "nombre": "Pechuga", "cantidad_g": 500},
        {"id": "tajadas", "nombre": "Plátano", "cantidad_g": 400},
        {"id": "culantro", "nombre": "Cilantro", "cantidad_g": 50}
    ]
    normalizados = _normalizar_items_detectados(crudos)
    assert normalizados[0]["id"] == "pollo_crudo"
    assert normalizados[1]["id"] == "platano_maduro"
    assert normalizados[2]["id"] == "culantro_fresco"


def test_t17_receta_paso_a_paso_gemma():
    """T17: Gemma 4 genera guía paso a paso con mise en place, cocción cronológica y consejo del chef."""
    from recipe_steps import generate_step_by_step_recipe
    plato = {
        "id": "pollo_guisado_demo",
        "nombre": "Pollo Guisado Criollo",
        "metodo": "Dorar pollo y sofreír vegetales a fuego medio.",
        "tiempo_min": 25,
        "porciones": 2
    }
    ingredientes = [
        {"id": "pollo_crudo", "nombre": "Pollo Fresco", "cantidad_g": 400},
        {"id": "tomate_perita", "nombre": "Tomate", "cantidad_g": 200}
    ]
    res = generate_step_by_step_recipe(plato, ingredientes, porciones=2, offline=True)
    assert res["plato_id"] == "pollo_guisado_demo"
    assert res["porciones"] == 2
    assert "Mise en place" in res["texto"]
    assert "Paso a paso de cocción" in res["texto"]
    assert "Consejo del chef" in res["texto"]


def test_t18_vision_scanner_gemma_mock_y_config(monkeypatch):
    """T18: VisionBites - Gemma 4 analiza fotos extrayendo JSON de ingredientes sin colapsar."""
    import json
    import sys
    from unittest.mock import MagicMock
    from vision_scanner import scan_food_image, ESTADO_SCANNER

    monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_123")
    monkeypatch.setenv("GEMMA_MODEL_NAME", "gemma-4-26b-a4b-it")

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps([
        {"id": "tomate_perita", "nombre": "Tomate Perita", "cantidad_g": 300, "grupo": "vegetal", "prioridad": "alta", "estado": "crudo", "apto": True},
        {"id": "pimiento_verde", "nombre": "Pimiento Verde", "cantidad_g": 200, "grupo": "vegetal", "prioridad": "media", "estado": "crudo", "apto": True}
    ])
    mock_client.models.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client
    monkeypatch.setitem(sys.modules, "google.genai", mock_genai)

    resultado = scan_food_image(b"fake_image_bytes", mime_type="image/jpeg")
    assert len(resultado) == 2
    assert resultado[0]["id"] == "tomate_perita"
    assert resultado[1]["id"] == "pimiento_verde"
    assert ESTADO_SCANNER["usando_respaldo"] is False
    assert "gemma-4-26b-a4b-it" in ESTADO_SCANNER["ultimo_metodo"]


if __name__ == "__main__":
    pytest.main(["-v", "test_suite.py"])

