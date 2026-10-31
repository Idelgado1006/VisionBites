"""Regresiones del recorrido de cocina, sin solicitudes a modelos externos."""

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from ui_theme import PAGINAS


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from ui_components import detected_items_view
    recetas = json.loads(Path("data/recetas_respaldo.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(detected_items_view, "generate_recipes", lambda *a, **kw: recetas)
    return AppTest.from_file("app.py", default_timeout=20).run()


def click(app, label):
    next(b for b in app.button if b.label == label).click().run()
    assert not app.exception


@pytest.mark.parametrize("preset", ["nevera_fresca", "alacena_granos", "sancocho_casero"])
def test_ejemplo_despensa_edicion_y_recetas(app, preset):
    assert not app.exception
    app.selectbox(key="radio_preset_muestra").select(preset).run()
    click(app, "Guardar en mi despensa")
    assert app.session_state["pagina"] == PAGINAS[1]
    assert app.session_state["inventario"]
    next(n for n in app.number_input if n.label == "Cantidad disponible (g)").set_value(450)
    click(app, "Guardar ingrediente")
    assert app.session_state["inventario"][0]["cantidad_g"] == 450
    click(app, "Crear mis recetas")
    assert app.session_state["pagina"] == PAGINAS[2]
    assert app.session_state["recetas_validas"]
    assert app.get("download_button")


def test_plan_directo_y_cambio_de_cantidades_invalida_plan(app):
    click(app, "Ver ideas de recetas →")
    assert app.session_state["pagina"] == PAGINAS[2]
    app.segmented_control(key="pagina").set_value(PAGINAS[1]).run()
    click(app, "Guardar ingrediente")
    assert app.session_state["recetas_validas"] is None
    app.segmented_control(key="pagina").set_value(PAGINAS[2]).run()
    assert not app.exception
    assert any(b.label == "Probar un plan de ejemplo" for b in app.button)


def test_reinicio_exige_confirmacion_y_permite_cancelar(app):
    click(app, "Guardar en mi despensa")
    click(app, "Empezar de nuevo")
    assert app.session_state["inventario"]
    click(app, "Conservar mi cocina")
    assert app.session_state["inventario"]
    click(app, "Empezar de nuevo")
    click(app, "Sí, empezar de nuevo")
    assert app.session_state["inventario"] is None
    assert app.session_state["pagina"] == PAGINAS[0]


def test_modo_local_no_ofrece_analizar_fotos(app):
    app.toggle[0].set_value(True).run()
    app.segmented_control(key="metodo").set_value("Subir una foto").run()
    assert not app.exception
    assert any("no analiza fotografías" in i.value for i in app.info)
    assert not app.get("file_uploader")


def test_navegacion_no_queda_sin_pagina(app):
    app.segmented_control(key="pagina").set_value(None).run()
    assert not app.exception
    assert app.session_state["pagina"] == PAGINAS[0]


def test_resumen_solo_monta_el_grafico_visible(app):
    click(app, "Ver ideas de recetas →")
    assert not app.get("plotly_chart")
    app.session_state["vista_plan"] = "Aprovechamiento"
    app.run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    app.session_state["grafico_plan"] = "Nutrientes"
    app.run()
    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
