"""
ui_components - Módulos de interfaz de usuario desacoplados para VisionBites.
Cada vista tiene una única responsabilidad y respeta el límite estricto de líneas.
"""

from .scanner_view import render_scanner_view
from .detected_items_view import render_detected_items_view
from .recipes_macro_view import render_recipes_macro_view
from .nutrition_summary_view import render_nutrition_summary_view

__all__ = [
    "render_scanner_view",
    "render_detected_items_view",
    "render_recipes_macro_view",
    "render_nutrition_summary_view",
]

