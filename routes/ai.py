"""Rutas de la Inteligencia Artificial: chat, contenido y recomendador."""

from flask import Blueprint, current_app, jsonify, request

import services.ai_service as ai
import services.product_service as product_service
import services.recommendation_service as recommender
from services.settings_service import get_all_settings

ai_bp = Blueprint("ai_api", __name__, url_prefix="/api/ai")


@ai_bp.post("/chat")
def chat():
    """POST /api/ai/chat  { message, history }"""
    data = request.get_json(silent=True) or request.form.to_dict()
    message = str(data.get("message", "")).strip()
    history = data.get("history") or []

    if not message:
        return jsonify({"success": False, "message": "Escribe un mensaje antes de enviar."}), 400
    if len(message) > 1000:
        return jsonify({"success": False, "message": "El mensaje es demasiado largo."}), 400
    if not isinstance(history, list):
        history = []

    result = ai.chat(message, history)
    return jsonify({"success": True, **result})


@ai_bp.post("/content")
def content():
    """POST /api/ai/content  { product_id, platform, content_type, tone }"""
    data = request.get_json(silent=True) or request.form.to_dict()

    try:
        product_id = int(data.get("product_id", 0))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Selecciona un producto."}), 400

    product = product_service.get_product(product_id)
    if product is None:
        return jsonify({"success": False, "message": "El producto no existe."}), 404

    platform = str(data.get("platform", "Instagram"))
    content_type = str(data.get("content_type", "Publicacion"))
    tone = str(data.get("tone", "Elegante"))

    result = ai.generate_content(product, platform, content_type, tone)
    result["full_text"] = f"{result['texto']}\n\n{result['llamado_accion']}\n\n{result['hashtags_text']}"
    return jsonify({"success": True, **result})


@ai_bp.get("/recommend/quiz")
def recommend_quiz():
    """GET /api/ai/recommend/quiz -> el cuestionario de 'Encuentra tu producto'."""
    return jsonify({"success": True, **recommender.quiz()})


@ai_bp.post("/recommend")
def recommend():
    """POST /api/ai/recommend  { need, style }"""
    data = request.get_json(silent=True) or request.form.to_dict()
    need = str(data.get("need", "")).strip()
    style = str(data.get("style", "")).strip()

    valid_needs = {o["id"] for step in recommender.NEEDS for o in step["options"]}
    valid_styles = {o["id"] for step in recommender.NEEDS for o in step["options"]}
    if need not in valid_needs or style not in valid_styles:
        return jsonify({"success": False, "message": "Selecciona una opcion de cada pregunta."}), 400

    return jsonify({"success": True, **recommender.recommend(need, style)})


@ai_bp.get("/status")
def status():
    """GET /api/ai/status -> indica si la IA esta configurada (sin mostrar la key)."""
    return jsonify({
        "success": True,
        "ai_configured": ai.is_configured(),
        "mode": ai.mode_label(),
        "model": current_app.config["AI_MODEL"],
        "message": None if ai.is_configured() else ai.NO_API_MESSAGE,
    })


@ai_bp.get("/settings-context")
def settings_context():
    """GET /api/ai/settings-context -> ajustes visibles (sin datos sensibles)."""
    settings = get_all_settings()
    return jsonify({
        "success": True,
        "settings": settings,
        "ai_configured": ai.is_configured(),
    })
