"""
Servicio de estadisticas y ganancias.

Todas las consultas usan la tabla `sales`. Si no hay ventas, las funciones
devuelven 0 y un indicador `has_data` en False, para que el frontend pueda
mostrar el mensaje "Todavia no hay suficientes datos para mostrar estadisticas".
"""

from datetime import datetime, timedelta

from database.db import get_db
from services.settings_service import currency_symbol, low_stock_threshold

# Periodos soportados por /api/profits
PERIODS = {
    "day": "hoy",
    "week": "esta semana",
    "month": "este mes",
    "all": "todo el tiempo",
}


def _range_for(period):
    """Devuelve (fecha_inicio_sql, fecha_fin_sql) segun el periodo pedido."""
    today = datetime.now()
    start = {
        "day": today.replace(hour=0, minute=0, second=0, microsecond=0),
        "week": (today - timedelta(days=today.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        ),
        "month": today.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
        "all": None,
    }.get(period, today.replace(hour=0, minute=0, second=0, microsecond=0))
    return start, "%Y-%m-%d %H:%M:%S"


def _sums_between(start):
    db = get_db()
    if start is None:
        row = db.execute(
            """SELECT COUNT(*) AS sales_count,
                      COALESCE(SUM(total), 0)  AS total,
                      COALESCE(SUM(profit), 0) AS profit,
                      COALESCE(SUM(quantity), 0) AS units
               FROM sales"""
        ).fetchone()
    else:
        row = db.execute(
            """SELECT COUNT(*) AS sales_count,
                      COALESCE(SUM(total), 0)  AS total,
                      COALESCE(SUM(profit), 0) AS profit,
                      COALESCE(SUM(quantity), 0) AS units
               FROM sales
               WHERE created_at >= ?""",
            (start.strftime("%Y-%m-%d %H:%M:%S"),),
        ).fetchone()
    return {
        "sales": row["sales_count"],
        "units": row["units"],
        "revenue": round(row["total"], 2),
        "profit": round(row["profit"], 2),
    }


def profits_summary():
    """Ganancias de hoy, semana, mes y total general."""
    return {
        "day": _sums_between(_range_for("day")[0]),
        "week": _sums_between(_range_for("week")[0]),
        "month": _sums_between(_range_for("month")[0]),
        "all": _sums_between(None),
        "currency": currency_symbol(),
        "has_data": _sums_between(None)["sales"] > 0,
    }


def sales_series(days=7):
    """Ventas y ganancias de los ultimos N dias (para el grafico de barras)."""
    db = get_db()
    start = (datetime.now() - timedelta(days=days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    rows = db.execute(
        """SELECT date(created_at) AS day,
                  COALESCE(SUM(total), 0)  AS total,
                  COALESCE(SUM(profit), 0) AS profit,
                  COUNT(*) AS sales
           FROM sales
           WHERE created_at >= ?
           GROUP BY day
           ORDER BY day""",
        (start.strftime("%Y-%m-%d %H:%M:%S"),),
    ).fetchall()

    found = {r["day"]: r for r in rows}
    labels_es = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"]
    series = []
    for offset in range(days):
        day = (start + timedelta(days=offset)).strftime("%Y-%m-%d")
        row = found.get(day)
        series.append(
            {
                "date": day,
                "label": labels_es[(start + timedelta(days=offset)).weekday()],
                "revenue": round(row["total"], 2) if row else 0.0,
                "profit": round(row["profit"], 2) if row else 0.0,
                "sales": row["sales"] if row else 0,
            }
        )
    return series


def top_products(limit=5):
    """Productos con mas unidades vendidas."""
    db = get_db()
    rows = db.execute(
        """SELECT product_name,
                  SUM(quantity) AS units,
                  SUM(total)    AS revenue,
                  SUM(profit)   AS profit
           FROM sales
           GROUP BY product_name
           ORDER BY units DESC
           LIMIT ?""",
        (limit,),
    ).fetchall()
    return [
        {
            "name": r["product_name"],
            "units": r["units"],
            "revenue": round(r["revenue"], 2),
            "profit": round(r["profit"], 2),
        }
        for r in rows
    ]


def sales_by_category():
    """Reparto de las ventas por categoria (para el grafico circular)."""
    db = get_db()
    rows = db.execute(
        """SELECT COALESCE(NULLIF(category,''), 'Otros') AS category,
                  SUM(total)  AS revenue,
                  SUM(profit) AS profit,
                  SUM(quantity) AS units
           FROM sales
           GROUP BY category
           ORDER BY revenue DESC"""
    ).fetchall()
    return [
        {
            "category": r["category"],
            "revenue": round(r["revenue"], 2),
            "profit": round(r["profit"], 2),
            "units": r["units"],
        }
        for r in rows
    ]


def low_stock_products():
    """Productos que estan en inventario bajo o agotados."""
    db = get_db()
    limit = low_stock_threshold()
    rows = db.execute(
        "SELECT * FROM products WHERE stock <= ? ORDER BY stock ASC, name ASC",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


def inventory_value():
    """Valor del inventario segun el precio de compra y segun el precio de venta."""
    db = get_db()
    row = db.execute(
        """SELECT COALESCE(SUM(stock), 0) AS units,
                  COALESCE(SUM(stock * purchase_price), 0) AS cost_value,
                  COALESCE(SUM(stock * sale_price), 0)     AS retail_value
           FROM products"""
    ).fetchone()
    return {
        "units": row["units"],
        "cost_value": round(row["cost_value"], 2),
        "retail_value": round(row["retail_value"], 2),
        "potential_profit": round(row["retail_value"] - row["cost_value"], 2),
    }


def full_stats():
    """Paquete completo de datos para la pagina de Estadisticas."""
    summary = profits_summary()
    return {
        "summary": summary,
        "series": sales_series(7),
        "top_products": top_products(5),
        "by_category": sales_by_category(),
        "inventory": inventory_value(),
        "low_stock": len(low_stock_products()),
        "has_data": summary["all"]["sales"] > 0,
    }
