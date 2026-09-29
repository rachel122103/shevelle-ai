"""
Manejo de la base de datos SQLite de Shevelle AI.

Aqui se crean las tablas, se abre/cierra la conexion y se cargan los
productos de demostracion la primera vez que se inicia la aplicacion.
"""

import os
import sqlite3

from flask import current_app, g

# --------------------------------------------------------------------------
# 1. ESQUEMA DE LA BASE DE DATOS
# --------------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    category       TEXT    NOT NULL,
    description    TEXT    DEFAULT '',
    purchase_price REAL    NOT NULL DEFAULT 0,
    sale_price     REAL    NOT NULL DEFAULT 0,
    stock          INTEGER NOT NULL DEFAULT 0,
    image          TEXT,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS sales (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id     INTEGER NOT NULL,
    product_name   TEXT    NOT NULL,
    category       TEXT    DEFAULT '',
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    sale_price     REAL    NOT NULL,
    purchase_price REAL    NOT NULL DEFAULT 0,
    total          REAL    NOT NULL,
    profit         REAL    NOT NULL,
    customer       TEXT    DEFAULT '',
    payment_method TEXT    DEFAULT 'Efectivo',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX IF NOT EXISTS idx_sales_created_at ON sales (created_at);
CREATE INDEX IF NOT EXISTS idx_sales_product    ON sales (product_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
"""

# Productos de demostracion (se pueden eliminar desde la aplicacion)
DEMO_PRODUCTS = [
    (
        "Aretes Mariposa",
        "Aretes",
        "Aretes con forma de mariposa, detalles dorados y acabado elegante. Ideales para ocasiones especiales.",
        180.0, 350.0, 12, "Aretes",
    ),
    (
        "Aretes Dorados",
        "Aretes",
        "Aretes clasicos color dorado, pequenos y comodidos para usar todos los dias.",
        150.0, 300.0, 8, "Aretes",
    ),
    (
        "Pinza Mariposa",
        "Pinzas",
        "Pinza para cabello con decoracion de mariposa y broche resistente, no se desliza.",
        90.0, 200.0, 2, "Pinzas",
    ),
    (
        "Collar Minimalista",
        "Collares",
        "Collar delicado de cadena fina con dije minimalista. Un regalo que nunca falla.",
        220.0, 450.0, 5, "Collares",
    ),
    (
        "Pulsera Dorada",
        "Pulseras",
        "Pulsera dorado con ajuste comodo y detalles delicados, combina con cualquier outfit.",
        130.0, 280.0, 1, "Pulseras",
    ),
    (
        "Labial Rosa Suave",
        "Maquillaje",
        "Labial de tono rosa suave y acabado humectante, ideal para el dia a dia.",
        160.0, 320.0, 7, "Maquillaje",
    ),
    (
        "Crema Hidratante Floral",
        "Skincare",
        "Crema hidratante con extracto de flores para mantener la piel suave y luminosa.",
        260.0, 520.0, 4, "Skincare",
    ),
    (
        "Set de Joyeria Mixto",
        "Accesorios",
        "Set con aretes, pulsera y collar en tonos dorados. Perfecto para regalar.",
        500.0, 1000.0, 3, "Accesorios",
    ),
]

DEFAULT_SETTINGS = {
    "business_name": "Shevelle Beauty",
    "business_owner": "",
    "currency": "RD$",
    "low_stock_threshold": "3",
    "ai_enabled": "true",
    "welcome_message": (
        "¡Hola! Soy tu asistente de Shevelle AI. "
        "Puedo ayudarte con ventas, contenido, clientes y analisis de tu negocio."
    ),
}


# --------------------------------------------------------------------------
# 2. CONEXION
# --------------------------------------------------------------------------
def get_db():
    """Devuelve la conexion SQLite de la peticion actual (una sola vez)."""
    if "db" not in g:
        db_path = current_app.config["DB_PATH"]
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        g.db = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exception=None):
    """Cierra la conexion al terminar la peticion."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


# --------------------------------------------------------------------------
# 3. INICIALIZACION
# --------------------------------------------------------------------------
def init_db(app):
    """Crea las tablas y carga datos basicos. Se ejecuta al arrancar."""

    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
        _seed_if_empty(db)
        _sync_settings(db, app.config)
        db.commit()
        close_db()


def _seed_if_empty(db):
    """Inserta los productos de demostracion solo si la tabla esta vacia."""
    count = db.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
    if count == 0:
        db.executemany(
            """INSERT INTO products
               (name, category, description, purchase_price, sale_price, stock)
               VALUES (?, ?, ?, ?, ?, ?)""",
            [
                (name, cat, desc, purchase, sale, stock)
                for (name, cat, desc, purchase, sale, stock, _emoji) in DEMO_PRODUCTS
            ],
        )


def _sync_settings(db, config):
    """Inserta la configuracion por defecto que todavia no exista."""
    db.executemany(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        list(DEFAULT_SETTINGS.items()),
    )
    # El umbral de inventario bajo puede venir del .env
    if str(config.get("LOW_STOCK_THRESHOLD", 3)) != "3":
        db.execute(
            "INSERT INTO settings (key, value) VALUES ('low_stock_threshold', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(config["LOW_STOCK_THRESHOLD"]),),
        )


def reset_demo_data(app):
    """Borra todos los datos y vuelve a cargar los productos de ejemplo.

    Devuelve un resumen con las cantidades restauradas para que la interfaz
    pueda confirmarlo al usuario.
    """
    with app.app_context():
        db = get_db()
        db.execute("DELETE FROM sales")
        db.execute("DELETE FROM products")
        db.execute("DELETE FROM sqlite_sequence WHERE name IN ('products','sales')")
        _seed_if_empty(db)
        db.commit()
        summary = {
            "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "sales": db.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
        }
        close_db()
        return summary
