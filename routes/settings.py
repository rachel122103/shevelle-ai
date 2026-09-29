"""Rutas de la configuracion del negocio (tabla settings)."""

from flask import Blueprint, current_app, jsonify, request

import services.ai_service as ai
from database.db import reset_demo_data
from services.settings_service import get_all_settings, save_settings

settings_bp = Blueprint("settings_api", __name__, url_prefix="/api/settings")

EDITABLE = (
    "business_name",
    "business_owner",
    "currency",
    "low_stock_threshold",
    "ai_enabled",
    "welcome_message",
)


@settings_bp.get("")
@settings_bp.get("/")
def read_settings():
    """GET /api/settings"""
    return jsonify({
        "success": True,
        "settings": get_all_settings(),
        "ai_configured": ai.is_configured(),
        "ai_mode": ai.mode_label(),
    })


@settings_bp.put("")
@settings_bp.put("/")
def write_settings():
    """PUT /api/settings"""
    data = request.get_json(silent=True) or request.form.to_dict()
    payload = {k: v for k, v in data.items() if k in EDITABLE}

    if "low_stock_threshold" in payload:
        try:
            value = int(float(payload["low_stock_threshold"]))
            if value < 0 or value > 999:
                raise ValueError
            payload["low_stock_threshold"] = str(value)
        except (TypeError, ValueError):
            return jsonify({"success": False, "message": "El limite de inventario debe ser un numero entero."}), 400

    if "ai_enabled" in payload:
        payload["ai_enabled"] = "true" if str(payload["ai_enabled"]).lower() in ("true", "1", "on", "si") else "false"

    settings = save_settings(payload)
    return jsonify({"success": True, "message": "Configuracion guardada correctamente.", "settings": settings})


@settings_bp.post("/reset-demo")
def reset_demo():
    """POST /api/settings/reset-demo - borra productos y ventas y recarga los datos de ejemplo."""
    summary = reset_demo_data(current_app._get_current_object())
    return jsonify({
        "success": True,
        "message": "Datos de demostracion restaurados correctamente.",
        "data": summary,
    })
