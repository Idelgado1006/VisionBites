"""Ingreso de ingredientes mediante ejemplos, fotografía o cámara."""

import json
from html import escape

import streamlit as st
from ai_engine import generate_recipes
from ui_theme import PAGINAS, navegar
from validator import validate_inventory, validate_recipes
from vision_scanner import scan_food_image, PRESETS_MUESTRAS, ESTADO_SCANNER

MUESTRAS = {
    "nevera_fresca": ("Una nevera fresquita", "Pollo, tomate, plátano y culantro. Una combinación de todos los días, con mucho por aprovechar."),
    "alacena_granos": ("Lo bueno de la alacena", "Arroz, lentejas y vegetales. Esos básicos que siempre te salvan una comida."),
    "sancocho_casero": ("Sabor a casa", "Res, ñame, yuca y zapallo. Ingredientes para una comida que sabe a hogar."),
}


def _procesar_y_guardar_inventario(imagen_bytes, mime_type, modelo_vision, preset_key,
                                  generar_plan_directo=False, modelo_recetas=None,
                                  forzar_offline=False) -> None:
    try:
        with st.status("Preparando tu cocina…", expanded=True) as estado:
            st.write("Identificando ingredientes y revisando las cantidades…")
            # El modo local nunca envía la fotografía al modelo.
            items = scan_food_image(None if forzar_offline else imagen_bytes,
                                    mime_type=mime_type, model_name=modelo_vision, preset_key=preset_key)
            validados = validate_inventory(items)
            validas, candidatas = None, None
            if generar_plan_directo:
                st.write("Buscando recetas con estos ingredientes…")
                if forzar_offline or preset_key:
                    with open("data/recetas_respaldo.json", encoding="utf-8") as archivo:
                        candidatas = json.load(archivo)
                else:
                    candidatas = generate_recipes(validados, model_name=modelo_recetas)
                validas, _ = validate_recipes(candidatas, validados)
            estado.update(label="Ingredientes listos", state="complete", expanded=False)
        st.session_state.inventario = validados
        st.session_state.recetas_candidatas = candidatas
        st.session_state.recetas_validas = validas
        st.session_state.pop("editor_ingredientes_detectados", None)
        st.session_state.origen_inventario = ESTADO_SCANNER.copy()
        if imagen_bytes and ESTADO_SCANNER["usando_respaldo"]:
            st.session_state.ultimo_aviso_ui = "No se pudo analizar tu foto. Cargamos ingredientes de ejemplo; revísalos antes de cocinar."
        else:
            st.session_state.ultimo_aviso_ui = f"Listo: {len(validados)} ingredientes en tu despensa." + (
                " Tus recetas ya están preparadas." if validas else " Revisa las cantidades y crea tu plan.")
        navegar(PAGINAS[2] if validas else PAGINAS[1])
    except (ValueError, OSError, RuntimeError) as err:
        st.error(f"No pudimos preparar tu despensa. Inténtalo de nuevo o elige otro ejemplo. Detalle: {err}")


def _preview(datos: dict) -> None:
    filas = []
    for titulo, es_fresco in [("Para usar pronto", True), ("Básicos de despensa", False)]:
        items = [i for i in datos["ingredientes"] if (i["prioridad"] == "alta") == es_fresco]
        if not items:
            continue
        filas.append(f'<h4 class="ingredient-group">{titulo}</h4>')
        for item in items:
            filas.append(f'<div class="ingredient-row ingredient-simple"><b>{escape(item["nombre"])}</b>'
                         f'<span class="ingredient-amount">{item["cantidad_g"]:,.0f} g</span></div>')
    st.markdown('<div class="op-card"><div class="preview-header"><h3>Dentro de esta despensa</h3></div>'
                + "".join(filas) + '</div>', unsafe_allow_html=True)


def render_scanner_view(modelo_vision=None, modelo_recetas=None, forzar_offline=False) -> None:
    st.markdown('<div class="section-heading"><h2>¿Qué tienes hoy en la cocina?</h2></div>', unsafe_allow_html=True)
    metodos = ["Probar con un ejemplo", "Subir una foto", "Tomar foto ahora"]
    metodo = st.segmented_control("Cómo añadir ingredientes", metodos, default=metodos[0],
                                  key="metodo", label_visibility="collapsed", width="stretch") or metodos[0]
    if metodo == "Probar con un ejemplo":
        seleccion, vista = st.columns([1, 1.1], gap="large")
        with seleccion:
            preset = st.selectbox("Elige una despensa de ejemplo", list(MUESTRAS),
                                  format_func=lambda x: MUESTRAS[x][0], key="radio_preset_muestra")
            datos = PRESETS_MUESTRAS[preset]
            titulo, descripcion = MUESTRAS[preset]
            st.markdown(f'<div class="sample-story"><h3>{titulo}</h3><p>{descripcion}</p></div>', unsafe_allow_html=True)
            if st.button("Guardar en mi despensa", type="primary", use_container_width=True):
                _procesar_y_guardar_inventario(None, "image/jpeg", modelo_vision, preset, False, modelo_recetas, forzar_offline)
            if st.button("Ver ideas de recetas →", use_container_width=True):
                _procesar_y_guardar_inventario(None, "image/jpeg", modelo_vision, preset, True, modelo_recetas, forzar_offline)
            st.caption("Son datos de ejemplo. Puedes cambiar las cantidades después.")
        with vista:
            _preview(datos)
    else:
        st.caption("Coloca los ingredientes con buena luz y procura que todos se vean. Revisarás las cantidades antes de crear tus recetas.")
        if forzar_offline:
            st.info("El modo local usa ingredientes de ejemplo y no analiza fotografías. Desactívalo en Ajustes avanzados para usar tu foto.")
            return
        if metodo == "Subir una foto":
            archivo = st.file_uploader("Elige una foto de tu cocina", type=["jpg", "jpeg", "png", "webp"], key="foto_archivo")
        else:
            archivo = None
            if st.toggle("Activar cámara", key="activar_camara"):
                archivo = st.camera_input("Haz una foto de tus ingredientes", key="foto_camara")
            else:
                st.info("La cámara está apagada. Actívala cuando tengas tus ingredientes a mano.")
        if archivo is not None:
            imagen, acciones = st.columns([1, 1])
            with imagen:
                st.image(archivo.getvalue(), caption="Tu foto está lista para revisar", use_container_width=True)
            with acciones:
                st.markdown("### Una foto, muchas ideas")
                st.write("Identificaremos los ingredientes y estimaremos sus cantidades. Podrás corregir todo en tu despensa.")
                if st.button("Identificar mis ingredientes", type="primary", use_container_width=True):
                    _procesar_y_guardar_inventario(archivo.getvalue(), archivo.type or "image/jpeg",
                                                  modelo_vision, None, False, modelo_recetas, forzar_offline)
