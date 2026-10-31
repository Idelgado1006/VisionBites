"""Despensa con vista de lista para móvil y edición de cantidades."""

import json
from html import escape

import pandas as pd
import streamlit as st
from ai_engine import generate_recipes
from ui_theme import PAGINAS, navegar, render_empty
from validator import validate_inventory, validate_recipes
from vision_scanner import scan_food_image

GRUPOS = ["vegetal", "fruta", "cereal", "legumbre", "proteina", "tuberculo", "grasa", "otro"]
PRIORIDADES = ["alta", "media", "baja"]


def _guardar(registros: list[dict]) -> None:
    st.session_state.inventario = validate_inventory(registros)
    st.session_state.recetas_validas = None
    st.session_state.recetas_candidatas = None
    st.session_state.pop("editor_ingredientes_detectados", None)
    st.session_state.ultimo_aviso_ui = "Cambios guardados. Ya puedes crear tus recetas."
    st.rerun()


def _editar_ingrediente(inventario: list[dict]) -> None:
    with st.expander("Cambiar cantidades o editar un ingrediente"):
        indice = st.selectbox("¿Qué ingrediente quieres editar?", range(len(inventario)),
                              format_func=lambda x: inventario[x]["nombre"])
        item = inventario[indice]
        with st.form(f"editar_{item['id']}"):
            nombre = st.text_input("Nombre", item["nombre"])
            c1, c2 = st.columns(2)
            cantidad = c1.number_input("Cantidad disponible (g)", min_value=1.0, max_value=25000.0,
                                       value=float(item["cantidad_g"]), step=10.0)
            prioridad = c2.selectbox("Cuándo consumirlo", PRIORIDADES, index=PRIORIDADES.index(item["prioridad"]),
                                     format_func=lambda x: {"alta": "Pronto", "media": "En unos días", "baja": "Puede esperar"}[x])
            c3, c4 = st.columns(2)
            grupo = c3.selectbox("Grupo", GRUPOS, index=GRUPOS.index(item.get("grupo", "otro")))
            estados = ["crudo", "cocido", "otro"]
            estado = c4.selectbox("Estado", estados, index=estados.index(item.get("estado", "crudo")))
            apto = st.checkbox("Incluir en mis recetas", value=True)
            if st.form_submit_button("Guardar ingrediente", use_container_width=True):
                registros = [dict(i) for i in inventario]
                registros[indice].update(nombre=nombre, cantidad_g=cantidad, prioridad=prioridad,
                                         grupo=grupo, estado=estado, apto=apto)
                try:
                    _guardar(registros)
                except ValueError as err:
                    st.error(f"Revisa los datos: {err}")


def _agregar_ingrediente(inventario: list[dict]) -> None:
    db = st.session_state.nutricion_db
    ids = sorted(k for k in db if ":" not in k and k not in {i["id"] for i in inventario})
    if not ids:
        return
    with st.expander("Añadir otro ingrediente"):
        with st.form("agregar_ingrediente"):
            nuevo = st.selectbox("Ingrediente del catálogo", ids, format_func=lambda x: x.replace("_", " ").title())
            cantidad = st.number_input("Cantidad (g)", min_value=1, max_value=25000, value=300, step=10)
            grupo = st.selectbox("Grupo de alimento", GRUPOS)
            prioridad = st.selectbox("Prioridad", PRIORIDADES)
            if st.form_submit_button("Añadir a mi despensa", use_container_width=True):
                try:
                    _guardar(inventario + [{"id": nuevo, "nombre": nuevo.replace("_", " ").title(),
                        "cantidad_g": cantidad, "grupo": grupo, "prioridad": prioridad,
                        "estado": db[nuevo].get("estado", "crudo"), "apto": True}])
                except ValueError as err:
                    st.error(f"No se pudo añadir el ingrediente: {err}")


def render_detected_items_view(modelo_recetas="gemini-2.5-flash", forzar_offline=False) -> None:
    inv = st.session_state.inventario
    if not inv:
        render_empty("Tu despensa está esperando", "Sube una foto de tus ingredientes o empieza con una nevera de ejemplo. Después podrás ajustar las cantidades.")
        c1, c2 = st.columns(2)
        if c1.button("Añadir mis ingredientes", use_container_width=True):
            navegar(PAGINAS[0])
        if c2.button("Usar la nevera de ejemplo", type="primary", use_container_width=True):
            st.session_state.inventario = validate_inventory(scan_food_image(None, preset_key="nevera_fresca"))
            st.session_state.origen_inventario = {"usando_respaldo": True, "mensaje": "Ingredientes de ejemplo."}
            st.rerun()
        return

    origen = st.session_state.get("origen_inventario", {})
    if origen.get("usando_respaldo"):
        st.caption("Estás usando ingredientes de ejemplo. Cámbialos por lo que tienes en casa antes de cocinar.")
    frescos = sum(i["prioridad"] == "alta" for i in inv)
    with st.container(key="inventory-metrics"):
        columnas = st.columns(2)
        for col, titulo, valor in zip(columnas, ["Ingredientes en casa", "Para usar pronto"], [str(len(inv)), str(frescos)]):
            col.markdown(f'<div class="metric-tile"><div class="metric-label">{titulo}</div><div class="metric-value">{valor}</div></div>', unsafe_allow_html=True)
    st.markdown("### Un vistazo a tus ingredientes")
    st.caption("Las cantidades de una foto son estimadas. Revísalas para obtener un plan más útil.")
    vista = st.radio("Vista de la despensa", ["Lista", "Tabla editable"], horizontal=True, label_visibility="collapsed")
    registros = inv
    if vista == "Lista":
        filas = []
        for titulo, es_fresco in [("Para usar pronto", True), ("Básicos de despensa", False)]:
            items = [i for i in inv if (i["prioridad"] == "alta") == es_fresco]
            if not items:
                continue
            filas.append(f'<h4 class="ingredient-group">{titulo}</h4>')
            for item in items:
                filas.append(f'<div class="ingredient-row ingredient-simple"><b>{escape(item["nombre"])}</b>'
                             f'<span class="ingredient-amount">{item["cantidad_g"]:,.0f} g</span></div>')
        st.markdown('<div class="op-card">' + "".join(filas) + '</div>', unsafe_allow_html=True)
        _editar_ingrediente(inv)
    else:
        editado = st.data_editor(pd.DataFrame(inv), hide_index=True, use_container_width=True,
            column_order=["nombre", "cantidad_g", "prioridad", "grupo", "estado", "apto"],
            column_config={
                "id": None, "nombre": st.column_config.TextColumn("Ingrediente", required=True),
                "cantidad_g": st.column_config.NumberColumn("Cantidad (g)", min_value=1, max_value=25000, required=True, format="%.0f g"),
                "prioridad": st.column_config.SelectboxColumn("Prioridad", options=PRIORIDADES, required=True),
                "grupo": st.column_config.SelectboxColumn("Grupo", options=GRUPOS, required=True),
                "estado": st.column_config.SelectboxColumn("Estado", options=["crudo", "cocido", "otro"], required=True),
                "apto": st.column_config.CheckboxColumn("Incluir"),
            }, key="editor_ingredientes_detectados")
        registros = editado.to_dict(orient="records")
        if st.button("Guardar cambios en la tabla", use_container_width=True):
            try:
                _guardar(registros)
            except ValueError as err:
                st.error(f"Revisa las cantidades y los nombres: {err}")
    _agregar_ingrediente(inv)
    if st.button("Crear mis recetas", type="primary", use_container_width=True):
        try:
            validado = validate_inventory(registros)
            with st.status("Buscando qué cocinar…", expanded=True) as estado:
                st.write("Combinando tus ingredientes y revisando las porciones disponibles.")
                if forzar_offline:
                    with open("data/recetas_respaldo.json", encoding="utf-8") as archivo:
                        candidatas = json.load(archivo)
                else:
                    candidatas = generate_recipes(validado, model_name=modelo_recetas)
                validas, _ = validate_recipes(candidatas, validado)
                estado.update(label="Recetas revisadas", state="complete", expanded=False)
            st.session_state.inventario = validado
            st.session_state.recetas_candidatas = candidatas
            st.session_state.recetas_validas = validas
            if validas:
                st.session_state.ultimo_aviso_ui = f"Encontramos {len(validas)} recetas compatibles con tu despensa."
                navegar(PAGINAS[2])
            else:
                st.warning("No encontramos recetas con esta combinación. Añade otro ingrediente o prueba una despensa de ejemplo.")
        except (ValueError, OSError, RuntimeError) as err:
            st.error(f"No pudimos crear el plan. Revisa tu despensa e inténtalo otra vez. Detalle: {err}")
