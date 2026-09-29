"""Rutas de la API de ventas."""

from datetime import datetime

from flask import Blueprint, jsonify, request

import services.stats_service as stats
from database.db import get_db
import services.product_service as product_service

sales_bp = Blueprint("sales_api", __name__, url_prefix="/api/sales")

PAYMENT_METHODS = ["Efectivo", "Tarjeta", "Transferencia", "otro"]


def _parse_sale(data):
    """Valida los datos de una venta antes de guardarla."""
    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        raise ValueError("Selecciona un producto.")

    try:
        quantity = int(data.get("quantity", 1))
    except (TypeError, ValueError):
        raise ValueError("La cantidad debe ser un numero entero.")
    if quantity < 1:
        raise ValueError("La cantidad debe ser mayor que 0.")

    raw_price = data.get("sale_price")
    if raw_price in (None, ""):
        return product_id, quantity, None
    try:
        price = round(float(raw_price), 2)
    except (TypeError, ValueError):
        raise ValueError("El precio debe ser un numero.")
    if price < 0:
        raise ValueError("El precio no puede ser negativo.")
    return product_id, quantity, price


@sales_bp.get("")
@sales_bp.get("/")
def list_sales():
    """GET /api/sales?limit=50"""
    try:
        limit = min(500, max(1, int(request.args.get("limit", 50))))
    except (TypeError, ValueError):
        limit = 50

    db = get_db()
    rows = db.execute("SELECT * FROM sales ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)).fetchall()
    sales = [dict(r) for r in rows]

    for sale in sales:
        sale["total"] = round(sale["total"], 2)
        sale["profit"] = round(sale["profit"], 2)

    return jsonify({
        "success": True,
        "count": len(sales),
        "sales": sales,
        "summary": stats.profits_summary(),
    })


@sales_bp.post("")
@sales_bp.post("/")
def create_sale():
    """POST /api/sales  ->  descuenta el inventario y guarda la venta."""
    data = request.get_json(silent=True) or request.form.to_dict()
    product_id, quantity, custom_price = _parse_sale(data)

    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        return jsonify({"success": False, "message": "El producto no existe."}), 404

    if product["stock"] < quantity:
        return jsonify({
            "success": False,
            "message": "No hay suficiente inventario.",
            "available": product["stock"],
            "requested": quantity,
        }), 400

    sale_price = custom_price if custom_price is not None else float(product["sale_price"])
    purchase_price = float(product["purchase_price"])
    total = round(sale_price * quantity, 2)
    profit = round((sale_price - purchase_price) * quantity, 2)
    payment_method = str(data.get("payment_method") or "Efectivo")
    if payment_method not in PAYMENT_METHODS:
        payment_method = "Otro"
    customer = str(data.get("customer") or "").strip()[:80]

    # Todo dentro de una transaccion: o se guarda la venta y se descuenta el
    # inventario, o no ocurre nada.
    try:
        cursor = db.execute(
            """INSERT INTO sales
               (product_id, product_name, category, quantity, sale_price,
                purchase_price, total, profit, customer, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (product["id"], product["name"], product["category"], quantity,
             sale_price, purchase_price, total, profit, customer, payment_method),
        )
        db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product["id"]))
        db.commit()
    except Exception:
        db.rollback()
        raise

    sale = dict(db.execute("SELECT * FROM sales WHERE id = ?", (cursor.lastrowid,)).fetchone())
    remaining = product["stock"] - quantity

    return jsonify({
        "success": True,
        "message": "Venta registrada correctamente.",
        "sale": sale,
        "calculation": {
            "total": total,
            "formula_total": f"{sale_price} x {quantity} = {total}",
            "profit": profit,
            "formula_profit": f"({sale_price} - {purchase_price}) x {quantity} = {profit}",
        },
        "product": {"id": product["id"], "name": product["name"], "stock": remaining},
        "low_stock_warning": f"⚠️ {product['name']}: quedan {remaining} unidades." if remaining <= 3 else None,
    }), 201


@sales_bp.delete("/<int:sale_id>")
def delete_sale(sale_id):
    """DELETE /api/sales/<id>  ->  devuelve las unidades al inventario."""
    db = get_db()
    sale = db.execute("SELECT * FROM sales WHERE id = ?", (sale_id,)).fetchone()
    if sale is None:
        return jsonify({"success": False, "message": "La venta no existe."}), 404

    try:
        db.execute("DELETE FROM sales WHERE id = ?", (sale_id,))
        db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (sale["quantity"], sale["product_id"]))
        db.commit()
    except Exception:
        db.rollback()
        raise

    return jsonify({
        "success": True,
        "message": "Venta anulada correctamente. Se devolvieron las unidades al inventario.",
    })


@sales_bp.get("/preview")
def preview_sale():
    """GET /api/sales/preview?product_id=1&quantity=2&sale_price=350
    Calcula el total y la ganancia sin guardar nada (para el formulario)."""
    try:
        product_id = int(request.args.get("product_id", 0))
        quantity = max(1, int(request.args.get("quantity", 1)))
    except (TypeError, ValueError):
        return jsonify({"success": False, "message": "Datos numericos invalidos."}), 400

    product = product_service.get_product(product_id)
    if product is None:
        return jsonify({"success": False, "message": "El producto no existe."}), 404

    try:
        price = float(request.args.get("sale_price") or product["sale_price"])
    except (TypeError, ValueError):
        price = float(product["sale_price"])

    total = round(price * quantity, 2)
    profit = round((price - float(product["purchase_price"])) * quantity, 2)
    return jsonify({
        "success": True,
        "total": total,
        "profit": profit,
        "unit_price": price,
        "quantity": quantity,
        "available": product["stock"],
        "insufficient": product["stock"] < quantity,
    })
