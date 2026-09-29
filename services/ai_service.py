"""
Servicio de Inteligencia Artificial de Shevelle AI.

Funciona de dos maneras:

1. **Con API configurada** -> envia la pregunta a un servicio compatible con
   OpenAI (`AI_API_KEY`, `AI_API_URL`, `AI_MODEL` en el archivo .env).
2. **Sin API configurada (modo demostracion)** -> responde con plantillas
   inteligentes construidas con los DATOS REALES de la base de datos.

En los dos casos la IA trabaja con informacion verdadera de la base de datos,
nunca con productos inventados.
"""

import json
import re
from datetime import datetime

from flask import current_app, has_app_context
import requests

import services.stats_service as stats
import services.product_service as products
from config import Config
from services.settings_service import currency_symbol, get_setting

# --------------------------------------------------------------------------
# 1. CONFIGURACION DE LA IA
# --------------------------------------------------------------------------
NO_API_MESSAGE = (
    "La inteligencia artificial no esta configurada todavia. "
    "Para activarla, edita el archivo .env, coloca tu AI_API_KEY y reinicia "
    "la aplicacion. Mientras tanto, Shevelle AI sigue funcionando y te responde "
    "con los datos reales de tu inventario y tus ventas."
)


def is_configured():
    """True si existe una API key configurada en el .env.

    Funciona tanto dentro como fuera del contexto de la aplicacion, para que
    se pueda mostrar el estado de la IA al arrancar el servidor.
    """
    if has_app_context():
        key = current_app.config.get("AI_API_KEY", "")
    else:
        key = getattr(Config, "AI_API_KEY", "")
    return bool((key or "").strip())


def mode_label():
    return "IA conectada" if is_configured() else "Modo demostracion (sin API)"


# --------------------------------------------------------------------------
# 2. UTILIDADES DE FORMATO
# --------------------------------------------------------------------------
def money(value):
    symbol = currency_symbol()
    try:
        value = float(value or 0)
    except (TypeError, ValueError):
        value = 0.0
    formatted = f"{value:,.2f}"
    return f"{symbol} {formatted}"


def normalize(text):
    """Quita acentos y pasa a minusculas para comparar palabras mas facilmente."""
    text = (text or "").lower()
    text = text.replace("á", "a").replace("é", "e").replace("í", "i")
    text = text.replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    text = text.replace("ü", "u")
    return re.sub(r"[^a-z0-9\s]", " ", text)


# --------------------------------------------------------------------------
# 3. DETECCION DE INTENCION
# --------------------------------------------------------------------------
# Palabras clave por tipo de pregunta. Se comparan sobre el texto ya
# normalizado (sin acentos y en minusculas). Solo se guarda UNA forma por
# raiz para que "producto" y "productos" no cuenten como dos coincidencias.
INTENT_KEYWORDS = {
    "inventario": [
        "inventario", "stock", "existencia", "unidade", "queda", "quedan",
        "agotado", "agotar", "reabastecer", "reponer", "faltan", "repuesto",
        "pocas unidades", "se estan acabando",
    ],
    "productos": [
        "producto", "catalogo", "categoria", "tienes", "disponible", "disponibles",
        "que vendes", "vendes", "opcion", "articulo", "que tienes", "que hay",
        "mi catalogo", "listado", "existen",
    ],
    "ganancias": [
        "ganancia", "ganando", "gana", "gane", "ganado", "ganamos", "utilidad",
        "profit", "facturado", "facturacion", "cuanto gane", "cuanto gan",
        "cuanto llevo", "rentable", "dinero", "margen", "cuanto entregu",
        "entregue", "cual es mi ganancia",
    ],
    "ventas": [
        "venta", "vender", "vendi", "vendido", "promocion", "descuento",
        "atraer", "cliente nuevo", "como vender", "regalo", "oferta",
        "atraer cliente", "mas venta", "vender mas",
    ],
    "contenido": [
        "contenido", "caption", "publicar", "publicacion", "publico", "tiktok",
        "instagram", "facebook", "historia", "hashtag", "copy", "post", "reel",
        "guion", "video", "viral", "red social", "anuncio", "idear", "idea para",
        "que puedo publicar", "que publico",
    ],
    "atencion": [
        "respondo", "responder", "responde", "respuesta", "pregunta", "preguntas",
        "frecuente", "faq", "duda", "consulta", "pide", "pidio", "reclamo",
        "que le digo", "que le puedo decir", "como le explico", "le explico",
        "atencion al cliente", "cliente escribio", "me escriben",
    ],
    "analisis": [
        "analiza", "analisis", "reporte", "resumen", "estadistica", "desempeno",
        "como va", "como voy", "mi negocio", "diagnostico", "consejo", "recomienda",
        "recomendacion", "que deberia", "sugerencia", "mejor producto",
    ],
}

PLATFORMS = ["Instagram", "TikTok", "WhatsApp"]
TONES = ["Elegante", "Casual", "Femenino", "Profesional", "Juvenil"]
CONTENT_TYPES = ["Publicacion", "Historia", "Video", "Promocion", "Descripcion de producto"]


def detect_intent(message):
    """Clasifica la pregunta de la usuaria en una categoria."""
    text = normalize(message)
    scores = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        scores[intent] = sum(1 for keyword in keywords if keyword in text)

    # Si pregunta directamente ("?") con palabras de atencion, gana atencion.
    if scores.get("atencion", 0) > 0 and ("?" in message or "responde" in text):
        scores["atencion"] += 3
    if re.search(r"\b(hola|buenas|hey|gracias)\b", text) and sum(scores.values()) == 0:
        return "saludo"

    best = max(scores, key=lambda key: scores[key])
    return best if scores[best] > 0 else "general"


# --------------------------------------------------------------------------
# 4. CONTEXTO REAL DE LA BASE DE DATOS
# --------------------------------------------------------------------------
def build_context(intent):
    """Reune datos REALES de la base de datos para darselos a la IA."""
    catalog = products.list_products()
    available = [p for p in catalog if p["stock"] > 0]
    low = stats.low_stock_products()
    summary = stats.profits_summary()
    cur = currency_symbol()
    biz = get_setting("business_name", "Shevelle Beauty")

    lines = [f"NEGOCIO: {biz}", f"PRODUCTOS REGISTRADOS: {len(catalog)}"]

    if available:
        lines.append("PRODUCTOS DISPONIBLES (nombre | categoria | precio | unidades):")
        lines += [
            f"- {p['name']} | {p['category']} | {cur} {p['sale_price']} | "
            f"{p['stock']} unidades | {p['description'][:110]}"
            for p in available[:25]
        ]
    else:
        lines.append("PRODUCTOS DISPONIBLES: ninguno (no hay stock registrado).")

    if low:
        lines.append("ALERTAS DE INVENTARIO:")
        lines += [f"- {p['name']}: quedan {p['stock']} unidades" for p in low[:15]]

    lines += [
        f"VENTAS HOY: {summary['day']['sales']} ventas | ingresos {cur} "
        f"{summary['day']['revenue']} | ganancia {cur} {summary['day']['profit']}",
        f"VENTAS ESTA SEMANA: {summary['week']['sales']} ventas | ganancia {cur} {summary['week']['profit']}",
        f"VENTAS ESTE MES: {summary['month']['sales']} ventas | ganancia {cur} {summary['month']['profit']}",
        f"TOTAL HISTORICO: {summary['all']['sales']} ventas | ganancia {cur} {summary['all']['profit']}",
    ]

    tops = stats.top_products(3)
    if tops:
        lines.append("PRODUCTOS MAS VENDIDOS: " + ", ".join(
            f"{t['name']} ({t['units']} u.)" for t in tops
        ))

    return "\n".join(lines)


def _api_error_message(error):
    text = str(error)
    if "401" in text or "unauthorized" in text.lower():
        return "La APIKey no es valida o no tiene permisos. Revisa AI_API_KEY en el archivo .env."
    if "404" in text:
        return "El modelo o la URL de la API no existen. Revisa AI_MODEL y AI_API_URL en el archivo .env."
    if "429" in text:
        return "La API de IA esta limitada por uso (error 429). Intenta de nuevo en un momento."
    if "timeout" in text.lower():
        return "La API de IA tardo demasiado en responder. Intenta de nuevo."
    if "connection" in text.lower() or "network" in text.lower():
        return "No se pudo conectar con la API de IA. Revisa tu conexion a internet."
    return f"Error al llamar a la API de IA: {text[:180]}"


def call_ai_api(messages):
    """Llama a la API de IA y devuelve el texto de la respuesta."""
    payload = {
        "model": current_app.config["AI_MODEL"],
        "messages": messages,
        "temperature": current_app.config["AI_TEMPERATURE"],
        "max_tokens": current_app.config["AI_MAX_TOKENS"],
    }
    response = requests.post(
        current_app.config["AI_API_URL"],
        headers={
            "Authorization": f"Bearer {current_app.config['AI_API_KEY']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=current_app.config["AI_TIMEOUT"],
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


# --------------------------------------------------------------------------
# 5. CHAT: RESPUESTAS EN MODO DEMOSTRACION
# --------------------------------------------------------------------------
def _demo_inventory(low, available):
    cur = currency_symbol()
    if not low:
        return ("Excelente: ningun producto esta en inventario bajo. "
                f"Tienes {len(available)} productos disponibles para vender.")
    lines = ["Aqui tienes los productos que necesitan atencion:"]
    for p in low:
        alert = "AGOTADO, debes reabastecer ya" if p["stock"] <= 0 else f"quedan {p['stock']} unidades"
        lines.append(f"- {p['name']} ({p['category']}): {alert}. Precio {cur} {p['sale_price']}.")
    lines.append("")
    lines.append("Sugerencia: comprueba hoy mismo si puedes reponer estos productos, "
                 "porque son los que mas se venden en un negocio de accesorios.")
    return "\n".join(lines)


def _demo_products(available, category=None):
    cur = currency_symbol()
    if not available:
        return ("No tienes productos con existencias en este momento. "
                "Ve a la seccion Productos y agrega al menos uno para poder vender.")
    if category:
        filtered = [p for p in available if p["category"] == category]
        if not filtered:
            return f"No hay productos disponibles de la categoria '{category}'."
        available = filtered
    lines = [f"Estos son tus productos REALES disponibles ahora mismo ({len(available)}):"]
    lines += [
        f"- {p['name']} | {p['category']} | {cur} {p['sale_price']} | {p['stock']} disponibles"
        for p in available[:20]
    ]
    return "\n".join(lines)


def _demo_profits(summary):
    cur = currency_symbol()
    if summary["all"]["sales"] == 0:
        return ("Todavia no tienes ventas registradas, asi que no puedo calcular ganancias reales. "
                "Registra tu primera venta en la seccion Ventas y en este mismo chat te dire "
                "cuanto estas ganando.")
    return (
        "Estas son tus ganancias REALES:\n"
        f"- Hoy: {cur} {summary['day']['profit']} de ganancia "
        f"({summary['day']['sales']} ventas, ingresos {cur} {summary['day']['revenue']}).\n"
        f"- Esta semana: {cur} {summary['week']['profit']} "
        f"({summary['week']['sales']} ventas).\n"
        f"- Este mes: {cur} {summary['month']['profit']} "
        f"({summary['month']['sales']} ventas).\n"
        f"- Total historico: {cur} {summary['all']['profit']} "
        f"({summary['all']['sales']} ventas y {summary['all']['units']} unidades vendidas)."
    )


def _demo_sales(message, summary, available):
    cur = currency_symbol()
    if summary["all"]["sales"] == 0:
        return ("Aun no tienes ventas registradas. Aqui van ideas concretas para empezar a vender hoy:\n"
                "1. Publica en Instagram una foto con luz natural de tu producto mas bonito, "
                "con un precio visible y un mensaje como 'Disponible hoy'.\n"
                "2. Crea unBundle de 2 piezas con 10% de descuento: regalar una pulsera al comprar aretes "
                "es la forma mas facil de vender mas.\n"
                "3. Escribe un mensaje directo a 5 personas que te compraron antes y mostrales el catalogo nuevo.\n"
                "4. Sube un TikTok de 15 segundos mostrando 3 productos que usarias tu misma, sin musica y con luz.")
    top = stats.top_products(1)
    best = top[0]["name"] if top else (available[0]["name"] if available else "tu producto estrella")
    return (
        f"Tu negocio lleva {summary['all']['sales']} ventas y {cur} {summary['all']['profit']} de ganancia. "
        f"Tu producto mas vendido es **{best}**, asi que rodealo de ofertas.\n\n"
        "Promociones que te recomiendo:\n"
        "- 2x1 en articulos de mayor rotacion (como " + best + ") solo los fines de semana.\n"
        "- Descuento del 15% por compra de 3 o mas piezas.\n"
        "- Envio gratis a partir de una cantidad minima, uniendolo con un regalo pequeño.\n"
        "- Sorteo entre quienes etiquetas a una amiga en tus historias: casi no cuesta y trae clientas nuevas.\n\n"
        "Y recuerda: registra cada venta en la aplicacion para que yo pueda decirte "
        "que producto rota mas y cual te deja mas ganancia."
    )


def _demo_content(message, available):
    if not available:
        return ("Todavia no tienes productos registrados, asi que no puedo crear contenido real. "
                "Agrega un producto y vuelvo a intentarlo.")
    referencia = [p for p in available if any(word in normalize(message) for word in normalize(p["name"]).split())]
    objetivo = referencia or available[:3]
    cur = currency_symbol()
    ideas = []
    for p in objetivo:
        ideas.append(
            f"- **{p['name']}** ({cur} {p['sale_price']}): foto con fondo lila o dorado, "
            f"texto corto 'Elegancia que se nota' y etiqueta a 3 cuentas de amigas para ganar alcance."
        )
    return (
        "Ideas de contenido para hoy, basadas en tus productos REALES:\n"
        + "\n".join(ideas)
        + "\n\nGuion rapido para TikTok: empieza mostrando el producto en la mano (segundo 1-3), "
        "di en voz alta 'esto lo llevo YO todo el dia', muestra 2angkatang detonantes: "
        "el detalle y el precio, y cierra con 'link en el perfil'. "
        "Repite el mismo producto en 3 formatos distintos."
    )


def _demo_attention(message, available, low):
    cur = currency_symbol()
    text = normalize(message)
    qty_match = re.search(r"\b(\d+)\b", message)
    qty = int(qty_match.group(1)) if qty_match else 1

    if any(word in text for word in ["precio", "costo", "cuanto cuesta", "cuanto vale", "valor"]):
        if available:
            top = available[:6]
            lista = "\n".join(f"- {p['name']}: {cur} {p['sale_price']}" for p in top)
            return (
                "Puedes responderle a tu cliente asi:\n\n"
                f"\"Hola! Claro que si, con gusto te ayudamos. Nuestros precios son:\n{lista}\n"
                "Todos incluyen empaque para regalo. Cual te gusto mas?\"\n\n"
                "Dato real de tu negocio: tienes " + str(len(available)) + " productos disponibles."
            )
        return ("No tengo productos con existencias todavia, asi que no puedo darte precios reales. "
                "Registra productos en la app para poder responder preguntas de precios.")

    if any(word in text for word in ["envio", "entrega", "domicilio"]):
        return ("Respuesta sugerida:\n\n\"Hola! Enviamos a toda la ciudad y a lugares cercanos. "
                "El envio es gratis en compras mayores a un monto minimo, y si compras varias piezas "
                "te lo ajustamos para que recibas en 24-48 horas. Te confirmamos por WhatsApp.\"\n\n"
                "Personaliza el monto y el tiempo segun lo que uses en tu negocio.")

    if any(word in text for word in ["devolucion", "cambio", "reclamo", "enojada", "molesta"]):
        return ("Respuesta sugerida:\n\n\"Hola, disculpa la molestia. Lamentamos mucho tu "
                "incomodidad. Podemos cambiarte la pieza o resolverlo como te resulte mas comodo. "
                "Envianos una foto por este mismo medio y lo solucionamos hoy mismo. Gracias por "
                "avisarnos y por confiar en Shevelle Beauty.\"\n\n"
                "Un buen reclamo bien atendido genera mas clientas que una venta perdida.")

    if any(word in text for word in ["pedido", "cuantos", "tienen", "disponible", "stock"]):
        disponibles = [p for p in available if p["stock"] >= qty]
        if disponibles:
            lista = "\n".join(f"- {p['name']} (quedan {p['stock']})" for p in disponibles[:5])
            return (
                "Puedes responder:\n\n\"Hola! Si, tenemos disponibilidad. Esto es lo que te "
                f"puede interesar:\n{lista}\nTe lo separamos hoy mismo.\"\n\n"
                f"Revise tu inventario: {len(disponibles)} de tus {len(available)} productos "
                "tienen unidades suficientes para esa cantidad."
            )
        return ("\"Hola! En este momento esos productos se agotaron, pero puede que la semana "
                "entrante lleguen de nuevo. Si te gustaron te aviso apenas tenga existencias.\" "
                "Avisame de nuevo en un dia para recordartelo.")

    return (
        "Te propongo esta respuesta general, bien cercana y profesional:\n\n"
        "\"Hola! gracias por escribirnos. Claro que si, con gusto te ayudamos a elegir. "
                "Cuentanos que occasion es y que buscas, y te enviamos las opciones que mejor "
        "te funcionan junto con su precio y disponibilidad.\"\n\n"
        "Datos que puedes usar hoy:\n"
        f"- Productos disponibles: {len(available)}.\n"
        f"- Productos en inventario bajo: {len(low)} (no los prometas si estan agotados)."
    )


def _demo_analysis(summary, low, available):
    if summary["all"]["sales"] == 0:
        return ("No tengo ventas para analizar todavia. Cuando registres ventas, podre decirte "
                "que producto se vende mas, que margen te deja mejor y que debes reabastecer.\n\n"
                "Mientras tanto, asegurate de tener al menos 5 productos registrados y "
                "publica 3 veces por semana en Instagram.")
    tops = stats.top_products(3)
    cur = currency_symbol()
    lines = [
        "Analisis de tu negocio con datos REALES:",
        f"- Ventas totales: {summary['all']['sales']} | ganancia acumulada: {cur} {summary['all']['profit']}.",
    ]
    if tops:
        lines.append("- Productos estrella: " + ", ".join(f"{t['name']} ({t['units']} u.)" for t in tops) + ".")
    if low:
        lines.append("- Productos a punto de agotarse: " + ", ".join(
            f"{p['name']} ({p['stock']} u.)" for p in low[:5]
        ) + ".")
    lines += [
        "",
        "Recomendaciones:",
        "1. Ponle promocion a tus productos estrella: son los que ya se venden solos.",
        "2. Reabastece los productos con inventario bajo antes de que se acaben.",
        "3. Revisa cada semana cuales productos no vendieron y dales un precio o publicacion nueva.",
    ]
    return "\n".join(lines)


def _demo_general(available):
    return (
        "Puedo ayudarte con varias cosas sobre tu negocio:\n\n"
        "- **Ventas**: ideas de promociones, como atraer clientas y que vender primero.\n"
        "- **Contenido**: ideas de publicaciones, TikToks e historias con tus productos.\n"
        "- **Clientes**: respuestas a preguntas frecuentes sobre precios, envios y disponibilidad.\n"
        "- **Negocio**: analisis de tus ventas, ganancias y alertas de inventario.\n"
        "- **Productos**: consultarme cuales tienes disponibles y sus precios.\n\n"
        f"Ahora mismo tienes {len(available)} productos disponibles. "
        "Preguntame, por ejemplo: '¿Que puedo publicar hoy?' o '¿Cuales productos tengo disponibles?'"
    )


def demo_answer(intent, message, available, low, summary):
    """Genera la respuesta inteligente sin API, usando datos reales."""
    if intent == "saludo":
        return (
            "¡Hola! ¿Como estas? Soy el asistente de Shevelle AI. "
            "Puedo ayudarte con tus ventas, tu contenido, tus clientes o revisar "
            "como va tu inventario. ¿Que necesitas hoy?"
        )
    if intent == "inventario":
        return _demo_inventory(low, available)
    if intent == "productos":
        return _demo_products(available)
    if intent == "ganancias":
        return _demo_profits(summary)
    if intent == "ventas":
        return _demo_sales(message, summary, available)
    if intent == "contenido":
        return _demo_content(message, available)
    if intent == "atencion":
        return _demo_attention(message, available, low)
    if intent == "analisis":
        return _demo_analysis(summary, low, available)
    return _demo_general(available)


# --------------------------------------------------------------------------
# 6. CHAT PRINCIPAL
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """Eres la asistente de Shevelle AI, una aplicacion para administrar un pequeno negocio de accesorios y belleza llamado Shevelle Beauty.

REGLAS IMPORTANTES:
1. Responde SIEMPRE en espanol, con un tono amable, profesional y cercano (trata de "tu", nunca de "usted" formal).
2. USA UNICAMENTE los datos reales de la base de datos que te entrego. NUNCA inventes productos, precios, clientes o cifras.
3. Si un dato no aparece en la informacion proporcionada, di que no tienes ese dato registrado.
4. Se breve y practica: usa listas con vinetas cuando ayuden a ordenar ideas.
5. Puedes dar Ideas y sugerencias de marketing, esas si son tu especialidad.
6. Conociste al producto usa nombres exactos de la base de datos.

DATOS REALES DEL NEGOCIO:
"""


def chat(message, history=None):
    """Procesa un mensaje del chat y devuelve la respuesta."""
    message = (message or "").strip()
    if not message:
        raise ValueError("Escribe un mensaje antes de enviar.")

    intent = detect_intent(message)
    available = [p for p in products.list_products() if p["stock"] > 0]
    low = stats.low_stock_products()
    summary = stats.profits_summary()
    context = build_context(intent)

    used_api = False
    notice = None

    if is_configured() and get_setting("ai_enabled", "true") == "true":
        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT + context}]
            for item in (history or [])[-8:]:
                if item.get("role") in ("user", "assistant") and item.get("content"):
                    messages.append({"role": item["role"], "content": item["content"]})
            messages.append({"role": "user", "content": message})
            reply = call_ai_api(messages)
            used_api = True
        except requests.RequestException as error:
            reply = demo_answer(intent, message, available, low, summary)
            notice = _api_error_message(error)
        except (KeyError, IndexError, ValueError) as error:
            reply = demo_answer(intent, message, available, low, summary)
            notice = _api_error_message(error)
    else:
        reply = demo_answer(intent, message, available, low, summary)
        notice = None if is_configured() else NO_API_MESSAGE

    return {
        "reply": reply,
        "intent": intent,
        "source": "api" if used_api else "demo",
        "mode": mode_label(),
        "ai_configured": is_configured(),
        "notice": notice,
        "used_real_data": True,
    }


# --------------------------------------------------------------------------
# 7. GENERADOR DE CONTENIDO
# --------------------------------------------------------------------------
# Textos base por plataforma, tipo de contenido y tono.
OPENERS = {
    "Elegante": ["Elegancia que se nota.", "Un detalle que eleva cualquier look.", "Sofisticada en cada linea."],
    "Casual": ["Esto meambio el outfit.", "Lo que siempre uso.", "Simple y bonito."],
    "Femenino": ["Porque mereces sentirte linda.", "Un toque de feminineidad para tu dia.", "Details que enamoran."],
    "Profesional": ["Calidad que respalda tu estilo.", "Presentamos nuestra newest coleccion.", "Elegancia y confianza en cada pieza."],
    "Juvenil": ["Ojo con esto.", "No te lo pierdas.", "Nuevo drop, te va a encantar."],
}

HASHTAG_SETS = {
    "Instagram": ["#ShevelleBeauty", "#Accesorios", "#ModaFemenina", "#Aretes", "#Belleza", "#AccesoriosDorado", "#Emprendimiento", "#TiendaOnline"],
    "TikTok": ["#TikTok", "#Accesorios", "#TikTokShop", "#Belleza", "#Aretes", "#ParaTi", "#Emprendimiento", "#FYP"],
    "WhatsApp": ["#ShevelleBeauty", "#Ventas", "#Accesorios", "#Belleza"],
}

CTA_BY_TYPE = {
    "Publicacion": "Escrivenos por WhatsApp para apartar el tuyo. 🌸",
    "Historia": "Respondele a este mensaje con un 💬 y te enviamos el precio al instante.",
    "Video": "Guarda este video para cuando lo quieras y comentalo 'QUIERO' para recibir informacion.",
    "Promocion": "Solo por hoy, con tu pedido te enviamos un detalle extra de regalo. 🎁 Escribenos para aprovecharlo.",
    "Descripcion de producto": "Disponible ahora mismo. Pidelo por WhatsApp y te lo entregamos con empaque para regalo. 🎀",
}


def _fmt_price(price):
    return money(price)


def _demo_content_text(product, platform, content_type, tone):
    """Genera el contenido sin API usando plantillas + datos reales."""
    import random

    rng = random.Random(f"{product['id']}{platform}{content_type}{tone}{datetime.now().hour}")

    name = product["name"]
    category = product["category"]
    price = product["sale_price"]
    stock = product["stock"]
    cur = currency_symbol()

    openers = OPENERS.get(tone, OPENERS["Elegante"])
    opener = rng.choice(openers)
    description = (product.get("description") or "").strip()

    body = {
        "Publicacion": (
            f"{opener}\n\n"
            f"Nuestro {name} de la categoria {category} esta disponible "
            f"en Shevelle Beauty por {_fmt_price(price)}.\n\n"
            + (f"{description}\n\n" if description else "")
            + f"Empaque listo para regalo y entrega en poco tiempo."
        ),
        "Historia": (
            f"{opener}\n\n"
            f"¿Te imaginas luciendo {name}?\n"
            f"Precio: {_fmt_price(price)}\n"
            f"Quedan {stock} unidades disponibles."
        ),
        "Video": (
            f"[GUION DE VIDEO - 15 segundos]\n\n"
            f"0-3s: Muestra {name} en la mano, con buena luz.\n"
            f"3-8s: Ensena el detalle de cerca (dije, broche, textura).\n"
            f"8-12s: Dilo en voz alta: 'Esto lo llevo yo todos los dias y me lo preguntan siempre'.\n"
            f"12-15s: Aparece el precio {_fmt_price(price)} y el mensaje 'link en el perfil'."
        ),
        "Promocion": (
            f"{opener}\n\n"
            f"🔥 PROMOCION de {name} 🔥\n\n"
            f"Lleva 2 unidades de {category} y te dejo la segunda a mitad de precio.\n"
            f"Precio normal: {_fmt_price(price)} c/u.\n"
            f"Válido hasta agotar existencias (quedan {stock})."
        ),
        "Descripcion de producto": (
            f"{name}\n\n"
            f"Categoria: {category}\n"
            f"Precio de venta: {_fmt_price(price)}\n"
            + (f"Descripcion: {description}\n" if description else "")
            + f"Disponibilidad: {stock} unidades\n"
            f"Marca: Shevelle Beauty"
        ),
    }.get(content_type, f"{opener}\n\n{name} - {category} - {_fmt_price(price)}")

    cta = CTA_BY_TYPE.get(content_type, "Escribinos por WhatsApp para pedir el tuyo. 🌸")
    if stock <= 3:
        cta += " ¡Ultimas unidades disponibles!"

    hashtags = rng.sample(HASHTAG_SETS.get(platform, HASHTAG_SETS["Instagram"]), 6)
    return {
        "texto": body,
        "llamado_accion": cta,
        "hashtags": hashtags,
        "hashtags_text": " ".join(hashtags),
    }


def generate_content(product, platform, content_type, tone):
    """Genera contenido para redes. Usa la IA si esta configurada."""
    platform = platform if platform in PLATFORMS else "Instagram"
    content_type = content_type if content_type in CONTENT_TYPES else "Publicacion"
    tone = tone if tone in TONES else "Elegante"

    product_info = (
        f"- Nombre: {product['name']}\n"
        f"- Categoria: {product['category']}\n"
        f"- Descripcion: {product.get('description') or '(sin descripcion)'}\n"
        f"- Precio de venta: {_fmt_price(product['sale_price'])}\n"
        f"- Unidades en inventario: {product['stock']}"
    )

    result = None
    notice = None
    used_api = False
    ai_enabled = get_setting("ai_enabled", "true") == "true"

    if is_configured() and ai_enabled:
        prompt = (
            "Genera contenido de marketing para redes sociales.\n\n"
            f"PRODUCTO:\n{product_info}\n\n"
            f"PLATAFORMA: {platform}\n"
            f"TIPO DE CONTENIDO: {content_type}\n"
            f"TONO: {tone}\n\n"
            "Responde EXCLUSIVAMENTE con un objeto JSON valido, sin texto adicional, "
            'con esta estructura exacta:\n'
            '{"texto": "texto principal del post", '
            '"llamado_accion": "frase corta para que el cliente escriba o compre", '
            '"hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", '
            '"#hashtag5", "#hashtag6"]}\n\n'
            "No uses comillas sin escapar dentro de los valores. Maximo 80 palabras en el texto."
        )
        try:
            raw = call_ai_api([
                {"role": "system", "content": SYSTEM_PROMPT + build_context("contenido")},
                {"role": "user", "content": prompt},
            ])
            result = _parse_json_content(raw)
            used_api = True
        except (requests.RequestException, ValueError, KeyError) as error:
            notice = _api_error_message(error)
        except Exception as error:  # respuesta mal formada u otros fallos
            notice = f"La IA no devolvio un formato valido ({type(error).__name__})."

    if result is None:
        result = _demo_content_text(product, platform, content_type, tone)
        if notice is None:
            if not is_configured():
                notice = NO_API_MESSAGE
            elif not ai_enabled:
                notice = ("La IA esta desactivada en Configuracion, asi que se genero "
                          "el texto con datos reales de tu base de datos.")

    result.update({
        "product": product["name"],
        "platform": platform,
        "content_type": content_type,
        "tone": tone,
        "source": "api" if used_api else "demo",
        "ai_configured": is_configured(),
        "notice": notice,
    })
    return result


def _parse_json_content(raw):
    """Convierte la respuesta de la IA en un diccionario con el formato pedido."""
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("La IA no devolvio un objeto JSON.")
    data = json.loads(match.group(0))

    texto = str(data.get("texto", "")).strip()
    cta = str(data.get("llamado_accion", "")).strip()
    hashtags = data.get("hashtags") or []
    if isinstance(hashtags, str):
        hashtags = [h.strip() for h in hashtags.split() if h.strip()]
    hashtags = [h if h.startswith("#") else f"#{h.lstrip('#')}" for h in hashtags][:10]

    if not texto:
        raise ValueError("La IA devolvio un texto vacio.")
    return {
        "texto": texto,
        "llamado_accion": cta or CTA_BY_TYPE["Publicacion"],
        "hashtags": hashtags,
        "hashtags_text": " ".join(hashtags),
    }
