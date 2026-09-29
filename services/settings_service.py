"""Servicio de configuracion: lee y guarda los ajustes en la tabla settings."""

from database.db import get_db

DEFAULTS = {
    "business_name": "Shevelle Beauty",
    "business_owner": "",
    "currency": "RD$",
    "low_stock_threshold": "3",
    "ai_enabled": "true",
    "welcome_message": "¡Hola! Soy tu asistente de Shevelle AI.",
}


def get_all_settings():
    """Devuelve todos los ajustes como diccionario de texto."""
    db = get_db()
    rows = db.execute("SELECT key, value FROM settings").fetchall()
    data = dict(DEFAULTS)
    for row in rows:
        data[row["key"]] = row["value"]
    return data


def get_setting(key, default=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is None:
        return DEFAULTS.get(key, default)
    return row["value"]


def save_settings(new_settings):
    """Guarda (o actualiza) los ajustes recibidos."""
    db = get_db()
    for key, value in new_settings.items():
        if key not in DEFAULTS and key != "welcome_message":
            continue  # solo se permiten claves conocidas
        db.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, str(value)),
        )
    db.commit()
    return get_all_settings()


def currency_symbol():
    return get_setting("currency", "RD$")


def low_stock_threshold():
    try:
        return max(0, int(float(get_setting("low_stock_threshold", 3))))
    except (TypeError, ValueError):
        return 3
