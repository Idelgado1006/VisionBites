"""
optimizer.py - Motor de optimización entera determinista con PuLP.
Cumple estrictamente las reglas matemáticas de VisionBites:
- Cero sobreasignación: ningún ingrediente excede el stock físico disponible.
- Nombres de variables inmunes a caracteres especiales (espacios, guiones, tildes).
- Invariante de conservación de masa: inicial_g = usado_g + restante_g (< 0.01g).
- Resiliencia de ejecución: captura de excepciones del solver y eliminación de warnings.
"""

import warnings
from typing import Any
import pulp
from nutrition import nutrition_per_serving

PESOS_PRIORIDAD = {"alta": 3.0, "media": 2.0, "baja": 1.0}


def _calcular_indice_q(receta: dict, mapa_inventario: dict[str, dict], macros: dict) -> float:
    """Calcula el índice de calidad/diversidad alimentaria Q_r en [0, 1]."""
    ingredientes = receta.get("ingredientes", [])
    if not ingredientes:
        return 0.0

    peso_total_porcion = sum(float(i.get("cantidad_g_por_porcion", 0.0)) for i in ingredientes)
    if peso_total_porcion <= 0:
        return 0.0

    peso_vegetales = 0.0
    grupos_en_receta: set[str] = set()

    for i in ingredientes:
        cant_g = float(i.get("cantidad_g_por_porcion", 0.0))
        inv_item = mapa_inventario.get(i.get("id", ""), {})
        grupo = inv_item.get("grupo", "otro")
        grupos_en_receta.add(grupo)
        if grupo == "vegetal":
            peso_vegetales += cant_g

    prop_vegetales = peso_vegetales / peso_total_porcion
    comp_vegetal = min(1.0, prop_vegetales / 0.30)
    comp_diversidad = min(1.0, len(grupos_en_receta) / 4.0)

    fibra = macros.get("fibra_g")
    if fibra is not None and fibra >= 0:
        comp_fibra = min(1.0, float(fibra) / 6.0)
        q_r = (0.40 * comp_vegetal) + (0.30 * comp_diversidad) + (0.30 * comp_fibra)
    else:
        q_r = (0.5714 * comp_vegetal) + (0.4286 * comp_diversidad)

    return max(0.0, min(1.0, q_r))


def _calcular_urgencia(receta: dict, mapa_inventario: dict[str, dict]) -> float:
    """Calcula la urgencia U_r = SUMA_i [(gramos_por_porcion(i)/1000) * peso_prioridad(i)]."""
    u_r = 0.0
    for i in receta.get("ingredientes", []):
        cant_g = float(i.get("cantidad_g_por_porcion", 0.0))
        inv_item = mapa_inventario.get(i.get("id", ""), {})
        peso_prio = PESOS_PRIORIDAD.get(inv_item.get("prioridad", "baja"), 1.0)
        u_r += (cant_g / 1000.0) * peso_prio
    return u_r


def _crear_variable_entera(prob: pulp.LpProblem, nombre: str, limite_sup: int) -> pulp.LpVariable:
    """Crea una variable entera usando la API moderna de PuLP o fallback retrocompatible."""
    if hasattr(prob, "add_variable"):
        return prob.add_variable(nombre, lowBound=0, upBound=limite_sup, cat=pulp.LpInteger)
    return pulp.LpVariable(nombre, lowBound=0, upBound=limite_sup, cat=pulp.LpInteger)


def optimize(
    inventory: list[dict],
    recipes: list[dict],
    nutrition_db: dict,
    mode: str = "balance",
    max_total_portions: int = 30
) -> dict:
    """Resuelve la optimización lineal entera para asignar porciones a recetas."""
    if not inventory:
        return {
            "modo": mode.lower(), "estado": "error", "mensaje": "Inventario vacío.",
            "platos": [], "inventario": [],
            "metricas": {"kg_inicial_apto": 0.0, "kg_utilizado": 0.0, "porcentaje_uso": 0.0, "porciones_totales": 0}
        }

    if not recipes:
        inv_resumen = [
            {"id": item["id"], "nombre": item.get("nombre", item["id"]),
             "grupo": item.get("grupo", "otro"), "prioridad": item.get("prioridad", "baja"),
             "inicial_g": float(item["cantidad_g"]), "usado_g": 0.0, "restante_g": float(item["cantidad_g"])}
            for item in inventory
        ]
        kg_inicial = sum(float(item["cantidad_g"]) for item in inventory) / 1000.0
        return {
            "modo": mode.lower(), "estado": "ok", "platos": [], "inventario": inv_resumen,
            "metricas": {
                "kg_inicial_apto": round(kg_inicial, 3), "kg_utilizado": 0.0,
                "porcentaje_uso": 0.0, "porciones_totales": 0, "kg_prioridad_alta_usado": 0.0
            }
        }

    mapa_inventario = {item["id"]: item for item in inventory}
    macros_por_receta = {r["id"]: nutrition_per_serving(r, nutrition_db) for r in recipes}
    urgencias = {r["id"]: _calcular_urgencia(r, mapa_inventario) for r in recipes}
    q_indices = {r["id"]: _calcular_indice_q(r, mapa_inventario, macros_por_receta[r["id"]]) for r in recipes}
    max_urgencia = max(urgencias.values()) if urgencias and max(urgencias.values()) > 0 else 1.0

    prob = pulp.LpProblem("VisionBites_Plan", pulp.LpMaximize)

    # Nombres de variables limpios e inmunes a caracteres especiales en IDs
    vars_x: dict[str, pulp.LpVariable] = {}
    for idx, r in enumerate(recipes, start=1):
        v_name = f"var_receta_{idx}"
        vars_x[r["id"]] = _crear_variable_entera(prob, v_name, max_total_portions)

    # Restricción de tope de producción total
    prob += pulp.lpSum([vars_x[r["id"]] for r in recipes]) <= max_total_portions, "Tope_Produccion_Total"

    # Restricciones de capacidad por ingrediente del inventario
    for idx, item in enumerate(inventory, start=1):
        i_id = item["id"]
        capacidad = float(item["cantidad_g"])
        consumos = [
            vars_x[r["id"]] * float(ing["cantidad_g_por_porcion"])
            for r in recipes
            for ing in r.get("ingredientes", [])
            if ing["id"] == i_id
        ]
        if consumos:
            prob += pulp.lpSum(consumos) <= capacidad, f"Capacidad_Ing_{idx}"

    # Si una receta requiere un ingrediente ausente del inventario, forzar a 0 porciones
    for r in recipes:
        for ing in r.get("ingredientes", []):
            if ing["id"] not in mapa_inventario:
                prob += vars_x[r["id"]] == 0, f"SinStock_{r['id']}_{ing['id']}"

    # Función objetivo
    if mode.lower() == "rescate":
        prob += pulp.lpSum([vars_x[r["id"]] * urgencias[r["id"]] for r in recipes]), "Obj_Rescate"
    else:
        coefs = {r["id"]: (0.60 * (urgencias[r["id"]] / max_urgencia)) + (0.40 * q_indices[r["id"]]) for r in recipes}
        prob += pulp.lpSum([vars_x[r["id"]] * coefs[r["id"]] for r in recipes]), "Obj_Balance"

    # Resolución protegida contra fallos internos del solver
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            solver = pulp.PULP_CBC_CMD(msg=False)
            status = prob.solve(solver)
    except Exception:
        status = pulp.LpStatusNotSolved

    porciones_asignadas = (
        {r["id"]: int(round(vars_x[r["id"]].varValue or 0)) for r in recipes}
        if status == pulp.LpStatusOptimal
        else {r["id"]: 0 for r in recipes}
    )

    consumo_por_ingrediente = {item["id"]: 0.0 for item in inventory}
    platos_resultado = []
    for r in recipes:
        r_id = r["id"]
        porc = porciones_asignadas.get(r_id, 0)
        consumo_receta = {}
        for ing in r.get("ingredientes", []):
            i_id = ing["id"]
            g_usado = porc * float(ing["cantidad_g_por_porcion"])
            consumo_receta[i_id] = consumo_receta.get(i_id, 0.0) + g_usado
            if i_id in consumo_por_ingrediente:
                consumo_por_ingrediente[i_id] += g_usado

        platos_resultado.append({
            "id": r_id, "nombre": r["nombre"], "porciones": porc,
            "ingredientes": r.get("ingredientes", []),
            "macros_por_porcion": macros_por_receta[r_id], "consumo_g": consumo_receta,
            "metodo": r.get("metodo", ""), "tiempo_min": r.get("tiempo_min", 30),
            "q_indice": round(q_indices[r_id], 2), "urgencia": round(urgencias[r_id], 2)
        })

    inventario_resumen = []
    total_inicial_g, total_usado_g, total_alta_usada_g = 0.0, 0.0, 0.0
    for item in inventory:
        i_id = item["id"]
        inicial = float(item["cantidad_g"])
        usado = round(consumo_por_ingrediente.get(i_id, 0.0), 3)
        restante = round(max(0.0, inicial - usado), 3)

        # Verificación estricta de invariante de conservación de masa (< 0.01 g)
        delta_masa = abs((usado + restante) - inicial)
        if delta_masa >= 0.01:
            raise ValueError(f"Violación de conservación de masa en '{i_id}': delta={delta_masa}")

        inventario_resumen.append({
            "id": i_id, "nombre": item.get("nombre", i_id), "grupo": item.get("grupo", "otro"),
            "prioridad": item.get("prioridad", "baja"), "inicial_g": inicial, "usado_g": usado, "restante_g": restante
        })
        total_inicial_g += inicial
        total_usado_g += usado
        if item.get("prioridad") == "alta":
            total_alta_usada_g += usado

    porcentaje_uso = (total_usado_g / total_inicial_g * 100.0) if total_inicial_g > 0 else 0.0
    return {
        "modo": mode.lower(), "estado": "ok" if status == pulp.LpStatusOptimal else "no_optimo",
        "platos": platos_resultado, "inventario": inventario_resumen,
        "metricas": {
            "kg_inicial_apto": round(total_inicial_g / 1000.0, 3),
            "kg_utilizado": round(total_usado_g / 1000.0, 3),
            "porcentaje_uso": round(porcentaje_uso, 1),
            "porciones_totales": sum(porciones_asignadas.values()),
            "kg_prioridad_alta_usado": round(total_alta_usada_g / 1000.0, 3)
        }
    }
