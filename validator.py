"""
validator.py - Validación estricta y zero-trust para inventario y recetas.
Cumple con las directivas de backend-profesional (Pydantic, validación en frontera)
y arquitectura-organizacion-limpia (cero contratos inventados, single source of truth).
"""

from datetime import date, datetime
import math
import unicodedata
from typing import Any
from pydantic import BaseModel, Field, field_validator

# Conjuntos canónicos de validación según el Documento Maestro (Sección 4.1)
PRIORIDADES_VALIDAS = {"alta", "media", "baja"}
GRUPOS_VALIDOS = {"vegetal", "fruta", "cereal", "legumbre", "proteina", "tuberculo", "grasa", "otro"}
ESTADOS_VALIDOS = {"crudo", "cocido", "otro"}
CAMPOS_OBLIGATORIOS_INVENTARIO = ["id", "nombre", "cantidad_g", "prioridad", "apto", "grupo", "estado"]


def _remover_tildes(texto: str) -> str:
    """Elimina acentos y diacríticos para normalizar entradas de formularios o usuarios."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _parsear_booleano(valor: Any) -> bool:
    """Normaliza representaciones comunes de booleanos provenientes de CSV, formularios o pandas."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        if math.isnan(valor):
            return False
        return bool(valor)
    if isinstance(valor, str):
        v = valor.strip().lower()
        if v in ("true", "1", "si", "sí", "yes", "t"):
            return True
        if v in ("false", "0", "no", "f", "nan", "none", "null"):
            return False
    return bool(valor)


def _parsear_fecha(valor: Any) -> date | None:
    """Parsea fechas desde objetos date, datetime, timestamps de pandas o cadenas ISO."""
    if valor is None:
        return None
    if isinstance(valor, (datetime, date)):
        return valor.date() if isinstance(valor, datetime) else valor
    v_str = str(valor).strip()
    if not v_str or v_str.lower() in ("nan", "none", "null", "nat"):
        return None
    # Trunca componentes de tiempo si provienen de pandas Timestamp ('YYYY-MM-DD HH:MM:SS')
    fecha_limpia = v_str.replace("T", " ").split(" ")[0].strip()
    try:
        return datetime.strptime(fecha_limpia, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Formato de fecha_limite inválido (se requiere AAAA-MM-DD).")


class InventarioItemModel(BaseModel):
    """Modelo zero-trust Pydantic para validar y tipar cada alimento en la frontera."""
    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    cantidad_g: float
    prioridad: str
    apto: bool = True
    grupo: str
    estado: str
    fecha_limite: date | None = None

    @field_validator("id")
    @classmethod
    def normalizar_id(cls, v: str) -> str:
        s = v.strip().lower()
        if not s:
            raise ValueError("El 'id' no puede estar vacío.")
        return s

    @field_validator("cantidad_g")
    @classmethod
    def validar_cantidad(cls, v: float) -> float:
        if math.isnan(v) or math.isinf(v):
            raise ValueError("La cantidad en gramos debe ser un número válido.")
        if v < 0:
            raise ValueError(f"Cantidad negativa inválida ({v} g).")
        return v

    @field_validator("prioridad")
    @classmethod
    def validar_prioridad(cls, v: str) -> str:
        p = _remover_tildes(str(v).strip().lower())
        if p not in PRIORIDADES_VALIDAS:
            raise ValueError(f"Prioridad inválida '{v}'. Opciones: {PRIORIDADES_VALIDAS}.")
        return p

    @field_validator("grupo")
    @classmethod
    def validar_grupo(cls, v: str) -> str:
        g = _remover_tildes(str(v).strip().lower())
        if g not in GRUPOS_VALIDOS:
            raise ValueError(f"Grupo alimentario inválido '{v}'. Opciones: {GRUPOS_VALIDOS}.")
        return g

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v: str) -> str:
        e = _remover_tildes(str(v).strip().lower())
        if e not in ESTADOS_VALIDOS:
            raise ValueError(f"Estado inválido '{v}'. Opciones: {ESTADOS_VALIDOS}.")
        return e


def validate_inventory(inventory: list[dict], fecha_referencia: str = "2026-10-31") -> list[dict]:
    """
    Valida la lista de ingredientes del inventario bajo política zero-trust con Pydantic.
    
    Reglas contractuales:
    - Rechaza IDs duplicados o cantidades negativas (lanza ValueError).
    - Valida tipos y dominios de prioridad, grupo y estado (resiliente a tildes).
    - Excluye ingredientes no aptos (apto=False) o con fecha_limite expirada.
    """
    if not isinstance(inventory, list):
        raise ValueError("El inventario debe ser una lista de registros.")

    ref_date = datetime.strptime(fecha_referencia or "2026-10-31", "%Y-%m-%d").date()
    ids_registrados: set[str] = set()
    inventario_elegible: list[dict] = []

    for idx, item in enumerate(inventory, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Fila {idx}: Registro inválido, se esperaba un diccionario.")

        # Verificación de presencia y contenido en campos obligatorios
        for campo in CAMPOS_OBLIGATORIOS_INVENTARIO:
            if campo not in item or item[campo] is None:
                raise ValueError(f"Fila {idx}: Campo obligatorio faltante o vacío: '{campo}'.")
            # Permitir booleano False o número 0 sin confundirlos con strings vacíos
            if not isinstance(item[campo], (bool, int, float)) and str(item[campo]).strip() == "":
                raise ValueError(f"Fila {idx}: Campo obligatorio faltante o vacío: '{campo}'.")

        item_id = str(item["id"]).strip().lower()
        if not item_id:
            raise ValueError(f"Fila {idx}: El 'id' no puede estar vacío.")

        # T02: Detección y rechazo inmediato de IDs duplicados
        if item_id in ids_registrados:
            raise ValueError(f"Fila {idx}: ID duplicado detectado: '{item_id}'. Cada ingrediente requiere un ID único.")
        ids_registrados.add(item_id)

        # Validación de fecha de caducidad
        try:
            fecha_lim_parsed = _parsear_fecha(item.get("fecha_limite"))
        except ValueError as e:
            raise ValueError(f"Fila {idx} ('{item_id}'): {e}")

        # Validación zero-trust mediante Pydantic
        try:
            item_model = InventarioItemModel(
                id=item_id,
                nombre=str(item["nombre"]).strip(),
                cantidad_g=item["cantidad_g"],
                prioridad=str(item["prioridad"]),
                apto=_parsear_booleano(item["apto"]),
                grupo=str(item["grupo"]),
                estado=str(item["estado"]),
                fecha_limite=fecha_lim_parsed,
            )
        except Exception as exc:
            # Propagar mensaje semántico para mantener contratos de error
            raise ValueError(f"Fila {idx} ('{item_id}'): {exc}")

        # T03: Exclusión de alimentos no aptos
        if not item_model.apto:
            continue

        # T03: Exclusión de alimentos con fecha límite vencida respecto a la fecha de referencia
        if item_model.fecha_limite and item_model.fecha_limite < ref_date:
            continue

        inventario_elegible.append({
            "id": item_model.id,
            "nombre": item_model.nombre,
            "cantidad_g": float(item_model.cantidad_g),
            "prioridad": item_model.prioridad,
            "apto": True,
            "grupo": item_model.grupo,
            "estado": item_model.estado,
            "fecha_limite": item_model.fecha_limite.isoformat() if item_model.fecha_limite else None
        })

    return inventario_elegible


def validate_recipes(recipes: list[dict], inventory: list[dict]) -> tuple[list[dict], list[str]]:
    """
    Valida que las recetas cumplan con los contratos y utilicen exclusivamente
    ingredientes existentes en el inventario elegible.
    """
    if not isinstance(recipes, list):
        return [], ["El conjunto de recetas no es una lista válida."]

    ids_inventario_disponibles = {item["id"] for item in inventory}
    recetas_validas: list[dict] = []
    motivos_descarte: list[str] = []
    ids_recetas_vistos: set[str] = set()

    for idx, receta in enumerate(recipes, start=1):
        if not isinstance(receta, dict):
            motivos_descarte.append(f"Propuesta {idx}: Estructura no válida (se esperaba objeto JSON).")
            continue

        r_id = str(receta.get("id", f"receta_{idx}")).strip().lower()
        r_nombre = str(receta.get("nombre", f"Receta {idx}")).strip()

        if r_id in ids_recetas_vistos:
            r_id = f"{r_id}_{idx}"
        ids_recetas_vistos.add(r_id)

        ingredientes = receta.get("ingredientes")
        if not isinstance(ingredientes, list) or len(ingredientes) == 0:
            motivos_descarte.append(f"Receta '{r_nombre}': Lista de ingredientes vacía o malformada.")
            continue

        ingredientes_receta_ids: set[str] = set()
        receta_es_valida = True
        ingredientes_limpios: list[dict] = []

        for ing in ingredientes:
            if not isinstance(ing, dict) or "id" not in ing or "cantidad_g_por_porcion" not in ing:
                motivos_descarte.append(f"Receta '{r_nombre}': Ingrediente con estructura deficiente.")
                receta_es_valida = False
                break

            ing_id = str(ing["id"]).strip().lower()

            # T04: Gemma/IA genera ID inexistente -> Descarte inmediato
            if ing_id not in ids_inventario_disponibles:
                motivos_descarte.append(
                    f"Receta '{r_nombre}': Ingrediente '{ing_id}' no existe en el inventario elegible."
                )
                receta_es_valida = False
                break

            # No se permiten ingredientes duplicados dentro de la misma preparación
            if ing_id in ingredientes_receta_ids:
                motivos_descarte.append(f"Receta '{r_nombre}': Ingrediente duplicado '{ing_id}'.")
                receta_es_valida = False
                break
            ingredientes_receta_ids.add(ing_id)

            try:
                g_porcion = float(ing["cantidad_g_por_porcion"])
                if math.isnan(g_porcion) or math.isinf(g_porcion):
                    raise ValueError("Cantidad no puede ser NaN o infinita.")
            except (ValueError, TypeError):
                motivos_descarte.append(f"Receta '{r_nombre}': Gramos por porción inválidos para '{ing_id}'.")
                receta_es_valida = False
                break

            if g_porcion <= 0:
                motivos_descarte.append(f"Receta '{r_nombre}': Gramos por porción deben ser > 0 ({g_porcion} g).")
                receta_es_valida = False
                break

            ingredientes_limpios.append({
                "id": ing_id,
                "cantidad_g_por_porcion": g_porcion
            })

        if receta_es_valida:
            recetas_validas.append({
                "id": r_id,
                "nombre": r_nombre,
                "ingredientes": ingredientes_limpios,
                "metodo": str(receta.get("metodo", "Cocinar adecuadamente los alimentos.")),
                "tiempo_min": int(receta.get("tiempo_min", 30))
            })

    return recetas_validas, motivos_descarte
