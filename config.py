"""
Configuración de Shevelle AI.

Todas las variables sensibles (como AI_API_KEY) se leen desde el archivo .env
y NUNCA se escriben dentro del código.
"""

import os
from pathlib import Path

# Carpeta raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent

# Cargar el archivo .env (si existe) antes de leer las variables
try:
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # Si python-dotenv no está instalado, se leen las variables del sistema.
    print("[AVISO] python-dotenv no esta instalado. No se pudo leer el archivo .env")


class Config:
    """Configuracion general de la aplicacion."""

    # --- Servidor ---
    SECRET_KEY = os.getenv("SECRET_KEY", "shevelle-ai-clave-de-desarrollo")
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"

    # --- Base de datos ---
    DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "database" / "database.db"))
    DATABASE = os.getenv("DATABASE_NAME", "Shevelle AI")

    # --- Informacion del negocio (editable desde Configuracion) ---
    BUSINESS_NAME = os.getenv("BUSINESS_NAME", "Shevelle Beauty")
    BUSINESS_OWNER = os.getenv("BUSINESS_OWNER", "")
    CURRENCY = os.getenv("CURRENCY", "RD$")
    LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", "3"))

    # --- Carpeta de imagenes subidas por la usuaria ---
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # maximo 4 MB por imagen
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

    # --- Inteligencia Artificial ---
    # La llave NUNCA se envia al navegador: solo la usa Python.
    AI_API_KEY = os.getenv("AI_API_KEY", "").strip()
    # URL compatible con el formato de OpenAI (chat/completions).
    AI_API_URL = os.getenv(
        "AI_API_URL", "https://api.openai.com/v1/chat/completions"
    ).strip()
    AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini").strip()
    AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.8"))
    AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "700"))
    AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "30"))

    # --- Rutas / textos de la aplicacion ---
    APP_NAME = "Shevelle AI"
    APP_TAGLINE = "Tu asistente inteligente para hacer crecer tu negocio"
