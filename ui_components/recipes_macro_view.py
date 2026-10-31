"""Recetas legibles, simulador de porciones y guía paso a paso con Gemma 4."""

from html import escape
import streamlit as st
from recipe_steps import generate_step_by_step_recipe
from ui_theme import PAGINAS, navegar, render_empty


def _calcular_proporcion_calorica(mac: dict) -> tuple[float, float, float]:
    valores = [max(0, float(mac.get(k, 0))) * factor for k, factor in
               [("proteina_g", 4), ("carbohidratos_g", 4), ("grasa_g", 9)]]
    total = sum(valores)
    return tuple(v / total * 100 for v in valores) if total else (0.0, 0.0, 0.0)


def _render_receta(plato: dict, idx: int) -> None:
    mac = plato["macros_por_porcion"]
    porciones = plato["porciones"]
    p, c, g = _calcular_proporcion_calorica(mac)
    fibra = f"{mac['fibra_g']:.1f} g" if mac.get("fibra_g") is not None else "sin dato"
    st.markdown(f'''<article class="op-card">
    <div class="recipe-meta"><span class="eyebrow">RECETA {idx:02} · {plato.get('tiempo_min', 25)} MIN</span>
    <span class="badge-pill pastel-sage">{porciones} {'porción' if porciones == 1 else 'porciones'}</span></div>
    <h3 class="recipe-title">{escape(plato['nombre'])}</h3>
    <p class="recipe-method">{escape(plato.get('metodo', 'Cocina los ingredientes cuidando su cocción y textura.'))}</p>
    <div class="recipe-macros">
    <div><strong>{mac['kcal']:.0f}</strong>kcal / porción</div>
    <div><strong>{mac['proteina_g']:.1f} g</strong>Proteína</div>
    <div><strong>{mac['carbohidratos_g']:.1f} g</strong>Carbohidratos</div>
    <div><strong>{mac['grasa_g']:.1f} g</strong>Grasas</div></div>
    <div style="display:flex;height:7px;overflow:hidden;border-radius:5px;background:#eeece2" role="img"
    aria-label="Distribución energética: proteína {p:.0f}%, carbohidratos {c:.0f}%, grasa {g:.0f}%">
    <span style="width:{p}%;background:#b9b2cf"></span><span style="width:{c}%;background:#e3c987"></span>
    <span style="width:{g}%;background:#9bbebd"></span></div>
    <p style="font-size:.73rem;color:var(--text-secondary);margin:.7rem 0 0">Fibra: {fibra} por porción · Valores de referencia USDA / INCAP</p>
    </article>''', unsafe_allow_html=True)


def _render_simulador(plato: dict, mapa: dict, idx: int) -> None:
    with st.expander(f"Ingredientes y porciones · {plato['nombre']}"):
        porciones = int(plato["porciones"])
        simuladas = st.slider("¿Para cuántas porciones quieres ver las cantidades?", 1, max(16, porciones),
                               porciones, key=f"sim_porc_{plato['id']}_{idx}")
        st.caption("Esta vista simula cantidades; no modifica la asignación de ingredientes del plan.")
        ingredientes = plato.get("ingredientes") or [
            {"id": k, "cantidad_g_por_porcion": v / porciones}
            for k, v in plato.get("consumo_g", {}).items()
        ]
        excedidos = []
        filas = []
        for ingrediente in ingredientes:
            info = mapa.get(ingrediente["id"], {})
            nombre = info.get("nombre", ingrediente["id"].replace("_", " ").title())
            gramos = float(ingrediente["cantidad_g_por_porcion"]) * simuladas
            if gramos > float(info.get("cantidad_g", 0)):
                excedidos.append(nombre)
            filas.append(f'<div class="ingredient-row" style="grid-template-columns:1fr auto"><b>{escape(nombre)}</b>'
                         f'<span class="ingredient-amount">{gramos:.0f} g</span></div>')
        st.markdown("".join(filas), unsafe_allow_html=True)
        if excedidos:
            st.warning("Para estas porciones te falta cantidad de: " + ", ".join(excedidos) + ".")
        mac = plato["macros_por_porcion"]
        st.caption(f"Total de la preparación: {mac['kcal'] * simuladas:.0f} kcal · "
                   f"{mac['proteina_g'] * simuladas:.1f} g de proteína · "
                   f"{mac['carbohidratos_g'] * simuladas:.1f} g de carbohidratos · "
                   f"{mac['grasa_g'] * simuladas:.1f} g de grasas")


def _render_paso_a_paso(plato: dict, mapa: dict, idx: int, modelo_recetas: str, offline: bool) -> str | None:
    """Renderiza la sección de cocina paso a paso con Gemma 4."""
    if "recetas_paso_a_paso" not in st.session_state or not isinstance(st.session_state.recetas_paso_a_paso, dict):
        st.session_state.recetas_paso_a_paso = {}

    guia = st.session_state.recetas_paso_a_paso.get(plato["id"])
    porciones = int(plato["porciones"])
    
    ingredientes_detalle = [
        {"id": k, "nombre": mapa.get(k, {}).get("nombre", k.replace("_", " ").title()), "cantidad_g": v}
        for k, v in plato.get("consumo_g", {}).items()
    ]

    with st.expander(f"👩‍🍳 Receta paso a paso (Gemma 4) · {plato['nombre']}", expanded=bool(guia)):
        if guia:
            st.markdown(f'<div style="margin-bottom:.6rem"><span class="badge-pill pastel-lav">✨ Redactado por {escape(guia.get("modelo", "Gemma 4"))}</span></div>', unsafe_allow_html=True)
            st.markdown(guia["texto"])
            if st.button("Volver a generar paso a paso", key=f"regen_{plato['id']}_{idx}"):
                with st.spinner("Gemma 4 está recalculando tu receta paso a paso..."):
                    nueva_guia = generate_step_by_step_recipe(plato, ingredientes_detalle, porciones, model_name=modelo_recetas, offline=offline)
                    st.session_state.recetas_paso_a_paso[plato["id"]] = nueva_guia
                    st.rerun()
            return guia["texto"]
        else:
            st.caption(f"Gemma 4 redactará las instrucciones de cocción, tiempos y cortes adaptados a tus {porciones} porciones.")
            if st.button("Obtener receta paso a paso con Gemma 4", key=f"btn_paso_{plato['id']}_{idx}", type="primary", use_container_width=True):
                with st.spinner(f"Gemma 4 está redactando la receta paso a paso para {plato['nombre']}..."):
                    nueva_guia = generate_step_by_step_recipe(plato, ingredientes_detalle, porciones, model_name=modelo_recetas, offline=offline)
                    st.session_state.recetas_paso_a_paso[plato["id"]] = nueva_guia
                    st.rerun()
            return None


def render_recipes_macro_view(
    plan: dict,
    mapa_inventario: dict[str, dict],
    modelo_recetas: str = "gemma-4-26b-a4b-it",
    offline: bool = False
) -> None:
    activos = [p for p in (plan or {}).get("platos", []) if p["porciones"] > 0]
    if not activos:
        render_empty("Falta un poquito para cocinar", "Las cantidades disponibles no alcanzan para una porción completa. Revisa tu despensa o añade otro ingrediente.")
        if st.button("Revisar mi despensa", type="primary", use_container_width=True):
            navegar(PAGINAS[1])
        return
    st.markdown("### A la mesa, con lo que tienes")
    st.caption("Las porciones respetan tus cantidades disponibles. Consulta los gramos o genera el paso a paso guiado con Gemma 4.")
    texto_descarga = ["MI PLAN DE COCINA · VISIONBITES (CON GEMMA 4)\n"]
    for idx, plato in enumerate(activos, 1):
        _render_receta(plato, idx)
        _render_simulador(plato, mapa_inventario, idx)
        paso_texto = _render_paso_a_paso(plato, mapa_inventario, idx, modelo_recetas, offline)
        texto_descarga.append(f"\n{plato['nombre']} · {plato['porciones']} porciones\n{plato.get('metodo', '')}\n")
        for id_ingrediente, gramos in plato.get("consumo_g", {}).items():
            nombre = mapa_inventario.get(id_ingrediente, {}).get("nombre", id_ingrediente)
            texto_descarga.append(f"- {nombre}: {gramos:.0f} g\n")
        mac = plato["macros_por_porcion"]
        texto_descarga.append(f"Por porción: {mac['kcal']:.0f} kcal; proteína {mac['proteina_g']:.1f} g; "
                              f"carbohidratos {mac['carbohidratos_g']:.1f} g; grasas {mac['grasa_g']:.1f} g.\n")
        if paso_texto:
            texto_descarga.append(f"\nGUÍA PASO A PASO (GEMMA 4):\n{paso_texto}\n")
            
    st.download_button("Guardar mi plan de cocina", "".join(texto_descarga), file_name="mi-plan-visionbites.txt",
                       mime="text/plain", use_container_width=True)
    reservados = [p["nombre"] for p in plan["platos"] if p["porciones"] == 0]
    if reservados:
        with st.expander("Más ideas para otro momento"):
            st.write(", ".join(reservados))
            st.caption("Estas recetas son compatibles, pero el plan actual prioriza otras por las cantidades o el límite de porciones.")
