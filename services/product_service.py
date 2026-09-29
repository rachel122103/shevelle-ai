"""Servicio de productos: logica de CRUD y consultas (la usan las rutas y la IA)."""

import math
import os
import uuid

from database.db import get_db
from services.settings_service import low_stock_threshold

CATEGORIES = [
    "Accesorios",
    "Aretes",
    "Collares",
    "Pulseras",
    "Pinzas",
    "Maquillaje",
    "Skincare",
    "Otros",
]

NUMERIC_FIELDS = ("purchase_price", "sale_price", "stock")


def row_to_dict(row):
    """Convierte una fila de SQLite en diccionario con campos extra utiles."""
    if row is None:
        return None
    product = dict(row)
    product["low_stock"] = product["stock"] <= low_stock_threshold()
    product["out_of_stock"] = product["stock"] <= 0
    product["profit_unit"] = round(
        float(product["sale_price"]) - float(product["purchase_price"]), 2
    )
    product["margin"] = (
        round((product["profit_unit"] / product["sale_price"]) * 100, 1)
        if float(product["sale_price"]) > 0
        else 0.0
    )
    return product


def list_products(search=None, category=None, stock_filter=None, order="recent"):
    """Devuelve la lista de productos con filtros opcionales."""
    db = get_db()
    sql = "SELECT * FROM products"
    clauses, params = [], []

    if search:
        clauses.append("(LOWER(name) LIKE ? OR LOWER(category) LIKE ? OR LOWER(description) LIKE ?)")
        like = f"%{search.lower()}%"
        params += [like, like, like]
    if category and category != "Todas":
        clauses.append("category = ?")
        params.append(category)

    if stock_filter == "low":
        clauses.append("stock <= ?")
        params.append(low_stock_threshold())
    elif stock_filter == "out":
        clauses.append("stock <= 0")
    elif stock_filter == "available":
        clauses.append("stock > 0")

    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    order_map = {
        "recent": "created_at DESC, id DESC",
        "name": "name COLLATE NOCASE ASC",
        "price_high": "sale_price DESC",
        "price_low": "sale_price ASC",
        "stock_low": "stock ASC, name ASC",
    }
    sql += " ORDER BY " + order_map.get(order, order_map["recent"])

    return [row_to_dict(r) for r in db.execute(sql, params).fetchall()]


def get_product(product_id):
    return row_to_dict(get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone())


def counts_by_category():
    rows = get_db().execute(
        "SELECT category, COUNT(*) AS total FROM products GROUP BY category ORDER BY category"
    ).fetchall()
    return {r["category"]: r["total"] for r in rows}


def _clean(data, creating=False):
    """Normaliza y valida los datos que llegan del formulario."""
    name = (data.get("name") or "").strip()
    if not name:
        raise ValueError("El nombre del producto es obligatorio.")
    if len(name) > 120:
        raise ValueError("El nombre es demasiado largo (maximo 120 caracteres).")

    category = (data.get("category") or "Otros").strip() or "Otros"
    if category not in CATEGORIES:
        category = "Otros"

    values = {}
    for field in NUMERIC_FIELDS:
        raw = data.get(field)
        try:
            value = float(raw if raw not in (None, "") else 0)
        except (TypeError, ValueError):
            raise ValueError(f"El campo '{field}' debe ser un numero.")
        if value < 0:
            raise ValueError(f"El campo '{field}' no puede ser negativo.")
        if math.isnan(value) or math.isinf(value):
            raise ValueError(f"El campo '{field}' no es un numero valido.")
        values[field] = round(value, 2)

    values["stock"] = int(values["stock"])
    values["name"] = name
    values["category"] = category
    values["description"] = (data.get("description") or "").strip()[:1000]
    values["image"] = (data.get("image") or "").strip() or None
    if creating:
        values.setdefault("image", None)
    return values


def create_product(data):
    values = _clean(data, creating=True)
    db = get_db()
    cursor = db.execute(
        """INSERT INTO products
           (name, category, description, purchase_price, sale_price, stock, image)
           VALUES (:name, :category, :description, :purchase_price, :sale_price, :stock, :image)""",
        values,
    )
    db.commit()
    return get_product(cursor.lastrowid)


def update_product(product_id, data):
    existing = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if existing is None:
        return None
    merged = dict(existing)
    merged.update({k: v for k, v in data.items() if v is not None or k in ("description", "image")})
    values = _clean(merged)

    db = get_db()
    db.execute(
        """UPDATE products SET
               name = :name, category = :category, description = :description,
               purchase_price = :purchase_price, sale_price = :sale_price,
               stock = :stock, image = :image
           WHERE id = :id""",
        {**values, "id": product_id},
    )
    db.commit()
    return get_product(product_id)


def delete_product(product_id):
    """Borra un producto. No se permite si ya tiene ventas registradas."""
    db = get_db()
    sold = db.execute(
        "SELECT COUNT(*) AS c FROM sales WHERE product_id = ?", (product_id,)
    ).fetchone()["c"]
    if sold:
        raise ValueError(
            "Este producto ya tiene ventas registradas y no se puede eliminar. "
            "Puedes borrarlo manualmente desde la base de datos si es necesario."
        )
    cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return cursor.rowcount > 0


def count_products():
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(stock), 0) AS units,
                  COALESCE(SUM(stock * purchase_price), 0) AS cost_value
           FROM products"""
    ).fetchone()
    return {
        "total": row["total"],
        "units": row["units"],
        "cost_value": round(row["cost_value"], 2),
    }


# --------------------------------------------------------------------------
# IMAGENES
# --------------------------------------------------------------------------
def save_image(file_storage):
    """Guarda una imagen subida y devuelve la ruta publica (/uploads/...)."""
    from flask import current_app

    if not file_storage or not file_storage.filename:
        return None
    extension = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
        raise ValueError("Formato de imagen no permitido (usa JPG, PNG, GIF, WEBP o SVG).")

    filename = f"{uuid.uuid4().hex}.{extension}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, filename))
    return f"/uploads/{filename}"
