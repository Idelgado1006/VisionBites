"""Preferencias de cocina; los detalles del motor permanecen opcionales."""

import os
import streamlit as st
from ui_theme import PAGINAS, navegar, render_brand


def render_sidebar() -> tuple[str, int, str, str, bool]:
    with st.sidebar:
        render_brand()
        st.markdown('<div class="sidebar-label">A TU GUSTO</div>', unsafe_allow_html=True)
        st.markdown("#### ¿Qué cocinamos hoy?")
        st.caption("Ajusta tu plan. Nosotros hacemos las cuentas.")
        modo = st.radio(
            "Quiero priorizar",
            ["balance", "rescate"],
            format_func=lambda x: "Comer variado" if x == "balance" else "Aprovechar los frescos",
            key="modo_cocina",
            help="Cambiar la prioridad recalcula tus recetas con los ingredientes disponibles.",
        )
        st.caption("Combinamos variedad y aprovechamiento." if modo == "balance" else
                   "Primero, lo que conviene consumir pronto.")
        porciones = st.number_input("Porciones como máximo", 1, 16, 6, step=1, key="tope_porciones")
        st.markdown('<div class="sidebar-tip"><b>Una cocina con más cariño</b>'
                    'Revisa tu nevera antes de comprar. A veces, la próxima comida ya está en casa.</div>',
                    unsafe_allow_html=True)
        with st.expander("Ajustes avanzados"):
            modelo_defecto = os.getenv("GEMMA_MODEL_NAME") or "gemma-4-26b-a4b-it"
            modelos_disponibles = list(dict.fromkeys([
                modelo_defecto,
                "gemma-4-31b-it",
                "gemini-2.5-flash",
                "gemini-2.0-flash",
            ]))
            vision = st.selectbox("Modelo para las fotos", modelos_disponibles, index=0)
            recetas = st.selectbox("Modelo para recetas y paso a paso", modelos_disponibles, index=0)
            offline = st.toggle("Usar solo ejemplos locales", value=False,
                                help="Usa el recetario y las muestras locales, sin llamadas a los modelos.")
        if st.session_state.get("confirmar_reinicio"):
            st.caption("¿Vaciar los ingredientes y las recetas de esta sesión?")
            if st.button("Sí, empezar de nuevo", use_container_width=True):
                for key in ("inventario", "recetas_candidatas", "recetas_validas", "recetas_paso_a_paso",
                            "ultimo_aviso_ui", "editor_ingredientes_detectados", "foto_archivo", "foto_camara",
                            "metodo", "activar_camara", "origen_inventario", "confirmar_reinicio"):
                    st.session_state.pop(key, None)
                navegar(PAGINAS[0])
            if st.button("Conservar mi cocina", use_container_width=True):
                st.session_state.confirmar_reinicio = False
                st.rerun()
        elif st.button("Empezar de nuevo", type="tertiary", key="reiniciar_cocina"):
            st.session_state.confirmar_reinicio = True
            st.rerun()
        st.caption("VisionBites · Cocina con lo que tienes")
    return modo, porciones, vision, recetas, offline
