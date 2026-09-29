"""
Servicio del recomendador: "Encuentra tu producto".

La herramienta pregunta a la clienta que busca y que estilo prefiere, y
recomienda productos REALES que estan en la base de datos. Si no hay
coincidencias, recomienda los productos disponibles con mayor disponibilidad.
"""

from database.db import get_db
import services.product_service as product_service
from services.settings_service import currency_symbol, get_setting

# Que entiende el asistente del cuestionario
NEEDS = [
    {
        "id": "necesidad",
        "label": "Accesorios",
        "icon": "💎",
        "question": "¿Que Estas buscando?",
        "options": [
            {"id": "accesorios", "label": "Accesorios", "icon": "💎", "categories": ["Accesorios", "Otros"]},
            {"id": "regalo", "label": "Regalo", "icon": "🎁", "categories": ["Accesorios", "Aretes", "Collares", "Pulseras"]},
            {"id": "diario", "label": "Algo para uso diario", "icon": "☀️", "categories": ["Aretes", "Pulseras", "Pinzas", "Maquillaje", "Skincare"]},
            {"id": "elegante", "label": "Algo elegante", "icon": "👑", "categories": ["Collares", "Aretes", "Accesorios"]},
        ],
    },
    {
        "id": "estilo",
        "label": "Estilo",
        "icon": "🎀",
        "question": "¿Que estilo prefieres?",
        "options": [
            {"id": "minimalista", "label": "Minimalista", "icon": "◻️", "keywords": ["minimalista", "delicado", "fino", "sencillo", "clasico"]},
            {"id": "elegante", "label": "Elegante", "icon": "👑", "keywords": ["elegante", "dorado", "sofisticado", "premium", "lujo"]},
            {"id": "casual", "label": "Casual", "icon": "🙂", "keywords": ["casual", "dia a dia", "comodo", "sencillo", "deportivo"]},
            {"id": "femenino", "label": "Femenino", "icon": "🦋", "keywords": ["femenino", "mariposa", "floral", "rosa", "delicado", "lindo"]},
        ],
    },
]

NEED_FALLBACK = {
    "accesorios": ["Accesorios", "Otros"],
    "regalo": ["Accesorios", "Aretes", "Collares", "Pulseras"],
    "diario": ["Aretes", "Pulseras", "Pinzas", "Maquillaje", "Skincare"],
    "elegante": ["Collares", "Aretes", "Accesorios"],
}

STYLE_FALLBACK = {
    "minimalista": ["minimalista", "delicado", "fino", "clasico", "collar", "cadena"],
    "elegante": ["elegante", "dorado", "clasico", "sofisticado", "premium"],
    "casual": ["casual", "dia a dia", "comodo", "pinza", "pulsera"],
    "femenino": ["mariposa", "floral", "rosa", "femenino", "lindo", "hermoso"],
}


def quiz():
    """Devuelve el cuestionario completo (lo consume la pagina web)."""
    return {
        "business": get_setting("business_name", "Shevelle Beauty"),
        "steps": [
            {
                "id": step["id"],
                "label": step["label"],
                "icon": step["icon"],
                "question": step["question"],
                "options": [
                    {"id": o["id"], "label": o["label"], "icon": o["icon"]}
                    for o in step["options"]
                ],
            }
            for step in NEEDS
        ],
    }


def _score(product, style_option):
    """Puntua un producto segun que tan bien encaja con las respuestas."""
    score = 0
    reasons = []

    haystack = f"{product['name']} {product['category']} {product.get('description') or ''}".lower()

    for keyword in style_option.get("keywords", []):
        if keyword in haystack:
            score += 4
            reasons.append(keyword)

    # Bonus si tiene buen margen y disponibilidad
    if product["stock"] > 0:
        score += 2
    if product["margin"] >= 30:
        score += 1

    return score, reasons


def recommend(need_id, style_id):
    """Devuelve hasta 3 productos reales recomendados."""
    all_products = product_service.list_products()
    available = [p for p in all_products if p["stock"] > 0]

    if not available:
        return {
            "items": [],
            "message": "Todavia no tienes productos con existencias. "
                       "Agrega productos en la seccion Productos para poder recomendar.",
            "currency": currency_symbol(),
        }

    style_option = {}
    for step in NEEDS:
        for option in step["options"]:
            if option["id"] == style_id:
                style_option = option
    categories = NEED_FALLBACK.get(need_id, NEED_FALLBACK["accesorios"])

    scored = []
    for product in available:
        score, reasons = _score(product, style_option)
        if product["category"] in categories:
            score += 5
        if score > 0:
            scored.append((score, product, reasons))

    scored.sort(key=lambda item: (-item[0], -item[1]["stock"]))

    # Si no hay coincidencias, recomienda los mas disponibles
    if not scored:
        scored = [(1, p, []) for p in sorted(available, key=lambda x: -x["stock"])[:3]]

    items = []
    for score, product, reasons in scored[:3]:
        items.append({
            "id": product["id"],
            "name": product["name"],
            "category": product["category"],
            "description": product["description"],
            "sale_price": product["sale_price"],
            "stock": product["stock"],
            "image": product.get("image"),
            "match": min(99, 60 + score * 4),
            "why": _why(product, style_id, reasons),
        })

    labels = {
        step["id"]: {o["id"]: o["label"] for o in step["options"]}
        for step in NEEDS
    }
    return {
        "items": items,
        "currency": currency_symbol(),
        "need_label": labels["necesidad"].get(need_id, need_id),
        "style_label": labels["estilo"].get(style_id, style_id),
        "message": None,
    }


def _why(product, style_id, reasons):
    style_names = {
        "minimalista": "un estilo limpio y delicado",
        "elegante": "un look elegante y sofisticado",
        "casual": "un estilo relajado para el dia a dia",
        "femenino": "un detalle muy femenino",
    }
    base = f"Es {product['name']} y combina con {style_names.get(style_id, 'tu estilo')}."
    if reasons:
        base += f" Tiene detalles de '{reasons[0]}' que encajan perfecto."
    base += f" Tienes {product['stock']} unidades disponibles."
    return base
