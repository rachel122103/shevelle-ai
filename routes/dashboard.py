"""Rutas del Dashboard y de las Estadisticas."""

from flask import Blueprint, jsonify

import services.product_service as product_service
import services.stats_service as stats
from database.db import get_db
from services.settings_service import currency_symbol, get_setting, low_stock_threshold

dashboard_bp = Blueprint("dashboard_api", __name__, url_prefix="/api")


@dashboard_bp.get("/dashboard")
def dashboard():
    """GET /api/dashboard -> tarjetas, ultimas ventas y alertas de inventario."""
    db = get_db()
    summary = stats.profits_summary()
    counts = product_service.count_products()
    low = stats.low_stock_products()
    cur = currency_symbol()

    recent = db.execute(
        """SELECT s.*, p.image
           FROM sales s LEFT JOIN products p ON p.id = s.product_id
           ORDER BY s.created_at DESC, s.id DESC LIMIT 5"""
    ).fetchall()

    recent_sales = []
    for row in recent:
        sale = dict(row)
        sale["total"] = round(sale["total"], 2)
        sale["profit"] = round(sale["profit"], 2)
        recent_sales.append(sale)

    alerts = [
        {
            "level": "danger" if p["stock"] <= 0 else "warning",
            "text": f"⚠️ {p['name']}: quedan {p['stock']} unidades.",
            "product_id": p["id"],
            "stock": p["stock"],
        }
        for p in low[:6]
    ]

    tops = stats.top_products(3)
    inventory = stats.inventory_value()

    return jsonify({
        "success": True,
        "business": {
            "name": get_setting("business_name", "Shevelle Beauty"),
            "currency": cur,
        },
        "cards": {
            "sales_today": {
                "label": "Ventas de hoy",
                "value": summary["day"]["revenue"],
                "formatted": f"{cur} {summary['day']['revenue']:,.2f}",
                "count": summary["day"]["sales"],
                "units": summary["day"]["units"],
                "icon": "🛒",
            },
            "products": {
                "label": "Productos",
                "value": counts["total"],
                "formatted": f"{counts['total']} productos",
                "units": counts["units"],
                "icon": "📦",
            },
            "low_stock": {
                "label": "Inventario bajo",
                "value": len(low),
                "formatted": f"{len(low)} productos",
                "icon": "⚠️",
            },
            "profits": {
                "label": "Ganancias del mes",
                "value": summary["month"]["profit"],
                "formatted": f"{cur} {summary['month']['profit']:,.2f}",
                "count": summary["month"]["sales"],
                "icon": "💰",
            },
        },
        "recent_sales": recent_sales,
        "alerts": alerts,
        "top_products": tops,
        "inventory": inventory,
        "summary": summary,
        "week": summary["week"],
        "threshold": low_stock_threshold(),
    })


@dashboard_bp.get("/stats")
def statistics():
    """GET /api/stats -> series, top productos, categorias e inventario."""
    return jsonify({"success": True, **stats.full_stats()})


@dashboard_bp.get("/profits")
def profits():
    """GET /api/profits?period=day|week|month|all"""
    from flask import request

    period = request.args.get("period", "day")
    if period not in stats.PERIODS:
        period = "day"
    return jsonify({
        "success": True,
        "period": period,
        "period_label": stats.PERIODS[period],
        "summary": stats.profits_summary(),
        "series": stats.sales_series(7),
        "top_products": stats.top_products(5),
    })


@dashboard_bp.get("/sales")
def all_sales():
    """GET /api/sales/all -> listado completo para graficos."""
    db = get_db()
    rows = db.execute(
        "SELECT product_name, quantity, total, profit, created_at FROM sales ORDER BY created_at DESC LIMIT 200"
    ).fetchall()
    return jsonify({"success": True, "count": len(rows), "sales": [dict(r) for r in rows]})
