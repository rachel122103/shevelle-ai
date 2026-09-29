"""
Shevelle AI - Aplicacion web para administrar el negocio de accesorios y belleza.

Punto de entrada. Aqui se crea la aplicacion de Flask, se registran las rutas,
se inicia la base de datos y se definen las paginas.

Para iniciar:
    python app.py
"""

import os

from flask import Flask, jsonify, render_template

from config import Config
from database.db import close_db, get_db, init_db
from routes.ai import ai_bp
from routes.dashboard import dashboard_bp
from routes.products import products_bp
from routes.sales import sales_bp
from routes.settings import settings_bp
from services import ai_service, recommendation_service
from services.settings_service import get_all_settings

# Paginas de la aplicacion
PAGES = {
    "inicio": ("dashboard.html", "🏠 Inicio"),
    "asistente": ("ai.html", "🤖 Asistente IA"),
    "productos": ("products.html", "📦 Productos"),
    "ventas": ("sales.html", "🛒 Ventas"),
    "ganancias": ("profits.html", "💰 Ganancias"),
    "contenido": ("content.html", "📱 Contenido"),
    "estadisticas": ("stats.html", "📊 Estadísticas"),
    "configuracion": ("settings.html", "⚙️ Configuración"),
    "recomendador": ("recommend.html", "✨ Encuentra tu producto"),
}


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.json.ensure_ascii = False  # para que los textos salgan con acentos
    app.teardown_appcontext(close_db)

    # --- Rutas de la API ---
    app.register_blueprint(products_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(settings_bp)

    # --- Base de datos: crea tablas y datos de demostracion ---
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    init_db(app)

    # --- Imagenes de los productos ---
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    @app.route("/")
    def index():
        settings = get_all_settings()
        return render_template(
            "index.html",
            title=app.config["APP_NAME"],
            tagline=app.config["APP_TAGLINE"],
            settings=settings,
            business=settings.get("business_name", app.config["BUSINESS_NAME"]),
            pages=PAGES,
            active="inicio",
            ai_configured=ai_service.is_configured(),
        )

    @app.route("/<page>")
    def show_page(page):
        entry = PAGES.get(page)
        if entry is None:
            return render_template("404.html", title="Pagina no encontrada", pages=PAGES, active=None), 404

        template, _ = entry
        settings = get_all_settings()
        return render_template(
            template,
            title=app.config["APP_NAME"],
            tagline=app.config["APP_TAGLINE"],
            settings=settings,
            business=settings.get("business_name", app.config["BUSINESS_NAME"]),
            pages=PAGES,
            active=page,
            ai_configured=ai_service.is_configured(),
            quiz=recommendation_service.quiz() if page == "recomendador" else None,
        )

    # --- Utilidades para el frontend ---
    @app.context_processor
    def inject_globals():
        return {
            "currency": get_all_settings().get("currency", "RD$"),
            "app_name": app.config["APP_NAME"],
            "app_tagline": app.config["APP_TAGLINE"],
        }

    @app.route("/api/health")
    def health():
        """Comprobacion rapida: GET /api/health"""
        db = get_db()
        products_count = db.execute("SELECT COUNT(*) AS c FROM products").fetchone()["c"]
        sales_count = db.execute("SELECT COUNT(*) AS c FROM sales").fetchone()["c"]
        return jsonify({
            "success": True,
            "app": app.config["APP_NAME"],
            "database": os.path.basename(app.config["DB_PATH"]),
            "products": products_count,
            "sales": sales_count,
            "ai_configured": ai_service.is_configured(),
            "ai_mode": ai_service.mode_label(),
        })

    # --- Errores ---
    @app.errorhandler(ValueError)
    def invalid_value(error):
        """Los errores de validacion del negocio se muestran como mensajes claros."""
        from flask import request

        message = str(error) or "Los datos enviados no son validos."
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": message}), 400
        return render_template("404.html", title="Error", pages=PAGES, active=None), 400

    @app.errorhandler(404)
    def not_found(_error):
        from flask import request

        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Endpoint no encontrado."}), 404
        return render_template("404.html", title="Pagina no encontrada", pages=PAGES, active=None), 404

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"success": False, "message": "La imagen es demasiado grande (maximo 4 MB)."}), 413

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({"success": False, "message": "Ocurrio un error inesperado en el servidor."}), 500

    return app


app = create_app()


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("   Shevelle AI - Tu asistente inteligente para hacer crecer tu negocio")
    print("=" * 62)
    print(f"   Abre en el navegador:  http://127.0.0.1:{app.config['PORT']}")
    print(f"   Base de datos:        {app.config['DB_PATH']}")
    print(f"   Modo de IA:           {ai_service.mode_label()}")
    if not ai_service.is_configured():
        print("   -> Configura AI_API_KEY en el archivo .env para activar la IA.")
    print("=" * 62 + "\n")
    app.run(
        host=app.config["HOST"],
        port=app.config["PORT"],
        debug=app.config["DEBUG"],
        use_reloader=False,
    )
