"""VisionBites: una cocina cercana, guiada y adaptable a cualquier pantalla."""

import json
import streamlit as st

from nutrition import load_nutrition
from optimizer import optimize
from ui_theme import (
    PAGINAS, aplicar_estilo_minimalista, mostrar_aviso, navegar,
    render_empty, render_header, render_stepper_hci, restaurar_inicio_de_pagina,
)
from ui_components import (
    render_scanner_view, render_detected_items_view,
    render_recipes_macro_view, render_nutrition_summary_view,
)
from ui_components.sidebar_view import render_sidebar
from validator import validate_inventory, validate_recipes
from vision_scanner import scan_food_image

st.set_page_config(page_title="VisionBites · Tu cocina de todos los días", layout="wide",
                   initial_sidebar_state="auto")
aplicar_estilo_minimalista()

for clave in ("inventario", "recetas_candidatas", "recetas_validas", "ultimo_aviso_ui"):
    if clave not in st.session_state:
        st.session_state[clave] = None
if "nutricion_db" not in st.session_state:
    st.session_state.nutricion_db = load_nutrition("data/nutricion.csv")
if "ir_a" in st.session_state:
    st.session_state.pagina = st.session_state.pop("ir_a")
if "pagina" not in st.session_state:
    st.session_state.pagina = PAGINAS[0]

modo, porciones, modelo_vision, modelo_recetas, offline = render_sidebar()
render_header(st.session_state.pagina)
render_stepper_hci(len(st.session_state.inventario or []), len(st.session_state.recetas_validas or []), modo)
mostrar_aviso()

if st.session_state.pagina == PAGINAS[0]:
    render_scanner_view(modelo_vision, modelo_recetas, offline)
elif st.session_state.pagina == PAGINAS[1]:
    render_detected_items_view(modelo_recetas, offline)
elif st.session_state.inventario and st.session_state.recetas_validas:
    plan = optimize(st.session_state.inventario, st.session_state.recetas_validas,
                    st.session_state.nutricion_db, mode=modo, max_total_portions=porciones)
    st.caption(f"Hasta {porciones} porciones · " +
               ("Buscando variedad y equilibrio" if modo == "balance" else "Priorizando tus ingredientes frescos") +
               " · Puedes cambiarlo en las preferencias de la barra lateral.")
    recetas, resumen = st.tabs(["Recetas", "Aprovechamiento"], key="vista_plan", on_change="rerun")
    if recetas.open:
        with recetas:
            render_recipes_macro_view(plan, {i["id"]: i for i in st.session_state.inventario},
                                      modelo_recetas=modelo_recetas, offline=offline)
    if resumen.open:
        with resumen:
            render_nutrition_summary_view(plan, modo)
else:
    render_empty("Tu próxima receta está por llegar", "Añade tus ingredientes o prueba nuestra nevera de ejemplo. Te ayudamos a convertirlos en un plan de cocina.")
    izquierda, derecha = st.columns(2)
    with izquierda:
        if st.button("Añadir mis ingredientes", use_container_width=True):
            navegar(PAGINAS[0])
    with derecha:
        if st.button("Probar un plan de ejemplo", type="primary", use_container_width=True):
            inventario = validate_inventory(scan_food_image(None, preset_key="nevera_fresca"))
            with open("data/recetas_respaldo.json", encoding="utf-8") as archivo:
                candidatas = json.load(archivo)
            validas, _ = validate_recipes(candidatas, inventario)
            st.session_state.inventario = inventario
            st.session_state.origen_inventario = {"usando_respaldo": True, "mensaje": "Ingredientes de ejemplo."}
            st.session_state.recetas_candidatas = candidatas
            st.session_state.recetas_validas = validas
            st.session_state.ultimo_aviso_ui = "Tu plan de ejemplo está listo. ¡Vamos a cocinar!"
            st.rerun()

st.markdown('<footer class="footer-note"><span>VisionBites · Pequeños ingredientes, buenas ideas.</span>'
            '<span>Referencias nutricionales USDA / INCAP</span></footer>', unsafe_allow_html=True)
restaurar_inicio_de_pagina()
