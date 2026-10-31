"""Identidad visual compartida de la cocina VisionBites."""

import base64
from html import escape
from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"
PAGINAS = ["Añadir ingredientes", "Mi despensa", "Mis recetas"]


def aplicar_estilo_minimalista() -> None:
    """Carga estilos locales, sin depender de fuentes o servicios externos."""
    css = "\n".join((ASSETS / name).read_text(encoding="utf-8") for name in (
        "theme.css", "components.css", "responsive.css",
    ))
    st.html(f"<style>{css}</style>")


def ilustracion_cocina() -> str:
    contenido = base64.b64encode((ASSETS / "cocina.svg").read_bytes()).decode()
    return f"data:image/svg+xml;base64,{contenido}"


def render_brand() -> None:
    st.markdown('''<div class="brand"><span class="brand-mark" aria-hidden="true">v<span>°</span></span>
    <div>VisionBites<small>Un poquito de magia en tu cocina</small></div></div>''', unsafe_allow_html=True)


def render_header(pagina: str) -> None:
    st.markdown('<div class="topline"><span class="mobile-brand">VisionBites</span><span class="topline-kicker">DE TU DESPENSA, A TU MESA</span>'
                '<span class="topline-note">Hecho para cocinar en casa</span></div>', unsafe_allow_html=True)
    if pagina == PAGINAS[0]:
        st.markdown(f'''<section class="kitchen-hero">
        <div class="hero-copy"><span class="eyebrow">MENOS DESPERDICIO. MÁS SABOR.</span>
        <h1>Algo rico empieza<br>con lo que <em>ya tienes.</em></h1>
        <p>Una foto, tus ingredientes y nuevas ideas para comer bien.</p>
        <span class="hero-note">Tu cocina. Tus ingredientes. Muchas posibilidades.</span></div>
        <img src="{ilustracion_cocina()}" alt="Olla verde con verduras frescas sobre un mantel de cocina" />
        </section>''', unsafe_allow_html=True)
    else:
        titulo, descripcion = (
            ("Tu despensa, en orden.", "Un vistazo a lo que tienes, para aprovecharlo mejor.")
            if pagina == PAGINAS[1] else
            ("De aquí sale algo rico.", "Ideas con tus ingredientes y porciones que se adaptan a ti.")
        )
        st.markdown(f'<div class="page-heading"><h1>{titulo}</h1><p>{descripcion}</p></div>', unsafe_allow_html=True)


def render_stepper_hci(n_ingredientes: int, n_recetas: int, modo: str) -> None:
    """El progreso acompaña la navegación, sin duplicar controles."""
    st.segmented_control("Navegación principal", PAGINAS, key="pagina", selection_mode="single",
                         format_func=lambda p: f"{PAGINAS.index(p) + 1}. {['Ingredientes', 'Despensa', 'Recetas'][PAGINAS.index(p)]}",
                         label_visibility="collapsed", width="stretch", on_change=_mantener_pagina)


def _mantener_pagina() -> None:
    # Segmented control permite deseleccionar; la navegación siempre necesita una página.
    if st.session_state.pagina is None:
        st.session_state.pagina = PAGINAS[0]
    st.session_state.scroll_cocina = True


def navegar(pagina: str) -> None:
    # Se aplica antes de crear el radio en la siguiente ejecución de Streamlit.
    st.session_state.ir_a = pagina
    st.session_state.scroll_cocina = True
    st.rerun()


def restaurar_inicio_de_pagina() -> None:
    """Evita conservar el scroll de la pantalla anterior al cambiar de paso."""
    if st.session_state.pop("scroll_cocina", False):
        st.html('''<script>requestAnimationFrame(() => {
          document.querySelector('[data-testid="stMain"]')?.scrollTo(0, 0);
        });</script>''', unsafe_allow_javascript=True)


def mostrar_aviso() -> None:
    aviso = st.session_state.pop("ultimo_aviso_ui", None)
    if aviso:
        st.success(aviso)


def render_empty(titulo: str, texto: str) -> None:
    st.markdown(f'<div class="empty-state"><span class="empty-seed" aria-hidden="true">↗</span>'
                f'<h3>{escape(titulo)}</h3><p>{escape(texto)}</p></div>', unsafe_allow_html=True)
