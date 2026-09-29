# 🦋 Shevelle AI

**Tu asistente inteligente para hacer crecer tu negocio**

Aplicación web para administrar un pequeño negocio de accesorios y belleza
(**Shevelle Beauty**). Controla productos, inventario, ventas y ganancias, y
además incluye un asistente de inteligencia artificial que responde preguntas
sobre tu negocio y crea contenido para redes sociales.

---

## 1. ¿Qué es Shevelle AI?

Es un **sistema de administración de negocio** con un asistente de IA integrado.
La usuaria (la dueña del negocio) entra a la aplicación, administra sus productos
y ventas, y cuando necesita una idea para vender más, para publicar en Instagram
o para responderle a una clienta, simplemente **le pregunta al asistente**.

La aplicación está pensada para ser sencilla: cada botón tiene una función clara
y cada acción muestra un mensaje confirmando lo que pasó.

## 2. ¿Qué problema resuelve?

Un negocio pequeño de accesorios normalmente lleva sus ventas en un cuaderno o en
la memoria. Eso provoca:

| Problema | Cómo lo resuelve Shevelle AI |
|---|---|
| No saber cuánto se está ganando realmente | Calcula la ganancia de **cada venta** y la de hoy, la semana, el mes y el total |
| No saber qué productos quedan por agotarse | Alertas automáticas de inventario bajo |
| Perder tiempo escribiendo publicaciones | Generador de contenido con IA para Instagram, TikTok y WhatsApp |
| No saber qué responderle a una clienta | Asistente que crea respuestas usando **precios y stock reales** |
| No saber qué producto se vende más | Estadísticas y gráficos de los últimos 7 días |
| No saber qué recomendarle a una clienta | Herramienta **"Encuentra tu producto"** |

## 3. Tecnologías utilizadas

| Capa | Tecnología |
|---|---|
| **Frontend** | HTML5, CSS3, JavaScript (sin frameworks) |
| **Backend** | Python 3 + Flask |
| **Base de datos** | SQLite (se crea sola al iniciar) |
| **Inteligencia Artificial** | API compatible con OpenAI (vía variable de entorno `AI_API_KEY`) |
| **Variables de entorno** | `python-dotenv` (archivo `.env`) |
| **Peticiones HTTP** | `requests` |

**Todo el diseño es responsive**: funciona en computadora, tablet y celular. En
pantallas pequeñas la barra lateral se convierte en un menú con botón hamburguesa.

## 4. Estructura del proyecto

```
shevelle-ai/
├── app.py                      # Punto de entrada: crea la app y registra rutas
├── config.py                   # Lee las variables del archivo .env
├── requirements.txt            # Dependencias de Python
├── README.md                   # Este archivo
├── .env                        # Variables de entorno (NO se sube a Git)
├── .env.example                # Ejemplo de .env (sí se sube a Git)
├── .gitignore                  # Ignora .env, la base de datos y __pycache__
│
├── database/
│   ├── __init__.py
│   ├── db.py                   # Crea tablas, carga datos demo, abre/cierra conexión
│   └── database.db             # Se genera automáticamente al iniciar
│
├── routes/                     # Endpoints de la API (un archivo por módulo)
│   ├── __init__.py
│   ├── products.py             # CRUD de productos
│   ├── sales.py                # Registro de ventas
│   ├── dashboard.py            # Dashboard, ganancias y estadísticas
│   ├── ai.py                   # Chat, generador de contenido y recomendador
│   └── settings.py             # Configuración del negocio
│
├── services/                   # Lógica de negocio (separada de las rutas)
│   ├── __init__.py
│   ├── ai_service.py           # Conexión con la IA + modo demostración
│   ├── product_service.py      # Validaciones y consultas de productos
│   ├── stats_service.py        # Cálculos de ganancias y gráficos
│   ├── settings_service.py     # Lectura/escritura de la tabla settings
│   └── recommendation_service.py  # Lógica del recomendador
│
├── templates/                  # Páginas HTML (Jinja2)
│   ├── base.html               # Menú lateral + barra superior (base de todas)
│   ├── index.html              # 🏠 Inicio / Dashboard
│   ├── ai.html                 # 🤖 Asistente IA (chat)
│   ├── products.html           # 📦 Productos
│   ├── sales.html              # 🛒 Ventas
│   ├── profits.html            # 💰 Ganancias
│   ├── content.html            # 📱 Crear contenido
│   ├── recommend.html          # ✨ Encuentra tu producto
│   ├── stats.html              # 📊 Estadísticas
│   ├── settings.html           # ⚙️ Configuración
│   └── 404.html                # Página no encontrada
│
├── static/
│   ├── css/style.css           # Diseño lila / dorado / gris claro
│   ├── js/
│   │   ├── app.js              # API, notificaciones, modales, formato de dinero
│   │   ├── dashboard.js        # Lógica del inicio
│   │   ├── products.js         # Listado, búsqueda y filtros
│   │   ├── sales.js            # Formulario de venta e historial
│   │   ├── profits.js          # Ganancias y gráficos
│   │   ├── chat.js             # Chat con el asistente
│   │   ├── content.js          # Generador de contenido
│   │   ├── recommend.js        # Recomendador
│   │   ├── stats.js            # Estadísticas
│   │   └── settings.js         # Configuración
│   └── images/butterfly.svg    # Logotipo (mariposa)
│
└── uploads/                    # Imágenes de los productos (opcional)
```

## 5. Cómo instalar el proyecto

### Requisitos

- **Python 3.10 o superior** (verifica con `python --version`)
- No necesitas instalar MySQL ni nada más: **SQLite viene con Python**

### Paso 1 · Entrar a la carpeta del proyecto

```powershell
cd "C:\ruta\de\tu\proyecto\shevelle-ai"
```

### Paso 2 · Crear el entorno virtual

En **Windows (PowerShell o CMD)**:

```powershell
python -m venv env
```

Actívalo:

```powershell
env\Scripts\activate
```

> Si usas **Git Bash** o **WSL**: `source env/Scripts/activate`
> Si PowerShell dice que no se puede ejecutar el script:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y vuelve a intentar.

Verás que la terminal cambia a `(...\env) PS C:\...>`.

### Paso 3 · Instalar las dependencias

```powershell
pip install -r requirements.txt
```

Esto instala: **Flask**, **python-dotenv** y **requests**.

### Paso 4 · Configurar el archivo `.env`

El proyecto ya trae un archivo `.env` listo para usar. Ábrelo con Bloc de notas:

```powershell
notepad .env
```

Quedaría así:

```ini
AI_API_KEY=
AI_API_URL=https://api.openai.com/v1/chat/completions
AI_MODEL=gpt-4o-mini
CURRENCY=RD$
LOW_STOCK_THRESHOLD=3
```

> **La aplicación funciona aunque `AI_API_KEY` esté vacía.** En ese caso entra en
> **modo demostración**: el asistente responde con datos reales de tu base de datos
> usando plantillas inteligentes, y la aplicación muestra un aviso de que falta
> configurar la IA.

### Paso 5 · Iniciar el servidor

```powershell
python app.py
```

Verás esto en la terminal:

```
==============================================================
   Shevelle AI - Tu asistente inteligente para hacer crecer tu negocio
==============================================================
   Abre en el navegador:  http://127.0.0.1:5000
   Base de datos:         ...\database\database.db
   Modo de IA:            Modo demostracion (sin API)
==============================================================
```

### Paso 6 · Abrir en el navegador

Abre Chrome o Edge y escribe en la barra de direcciones:

```
http://127.0.0.1:5000
```

**Para cerrar la aplicación:** haz clic en la terminal y presiona `Ctrl + C`.

---

## 6. Cómo configurar la API de Inteligencia Artificial

La IA es **opcional**: todo funciona sin ella. Para activarla:

**Paso 1** · Consigue una API key:
- **OpenAI** → https://platform.openai.com/api-keys (hay créditos gratuitos para empezar)
- También puedes usar otro proveedor compatible (Gemini, Groq, Together, Ollama…)

**Paso 2** · Abre el archivo `.env` y pega tu llave:

```ini
AI_API_KEY=sk-tu_clave_real_aqui
```

**Paso 3** · Si usas otro proveedor, cambia también la URL y el modelo:

```ini
AI_API_KEY=tu_clave
AI_API_URL=https://api.groq.com/openai/v1/chat/completions
AI_MODEL=llama-3.1-8b-instant
```

**Paso 4** · Reinicia el servidor (`Ctrl + C` y luego `python app.py`).

**Paso 5** · Verifica: en la barra superior aparecerá **● IA conectada** en lugar de
**● IA sin configurar**. También puedes entrar en ⚙️ Configuración y mirar el estado.

> 🔒 **Seguridad:** la API key se guarda **solo en el archivo `.env`**, que está en
> `.gitignore` y **nunca** se envía al navegador. El JavaScript no puede verla.

Si la API da error (llave inválida, límite de uso, sin internet), la aplicación
**no se cae**: avisa el motivo exacto y continúa en modo demostración.

---

## 7. Cómo usar la aplicación

| Sección | Qué puedes hacer |
|---|---|
| 🏠 **Inicio** | Ver ventas de hoy, cantidad de productos, inventario bajo y ganancias. Lista de últimas ventas y alertas tipo *"⚠️ Aretes Mariposa: quedan 2 unidades."* |
| 🤖 **Asistente IA** | Hacerle preguntas sobre tu negocio por escrito |
| 📦 **Productos** | Agregar, editar, eliminar, buscar y filtrar productos |
| 🛒 **Ventas** | Registrar ventas con cálculo automático de total y ganancia |
| 💰 **Ganancias** | Ganancia de hoy, semana, mes y total, con gráfico de 7 días |
| 📱 **Contenido** | Generar publicaciones para Instagram, TikTok y WhatsApp |
| ✨ **Encuentra tu producto** | Recomendador que ayuda a elegir a las clientas |
| 📊 **Estadísticas** | Gráficos de ventas, categorías y valor del inventario |
| ⚙️ **Configuración** | Nombre del negocio, moneda, alerta de inventario y estado de la IA |

### Cómo probar cada función (ruta rápida)

**📦 Productos — agregar**
1. Entra a **Productos** → presiona **➕ Agregar producto**.
2. Llena nombre, categoría, cantidad, precio de compra y precio de venta.
3. Presiona **💾 Guardar producto** → aparece *"Producto agregado correctamente."*
4. Observa que la tarjeta calcula sola la ganancia por unidad.

**📦 Productos — buscar y filtrar**
1. Escribe en el buscador (ej. `arete`) → filtra al instante.
2. Elige una categoría en el desplegable.
3. Selecciona **⚠️ Inventario bajo** para ver solo los que se están acabando.
4. Prueba **🔴 Agotados**.

**📦 Productos — editar y eliminar**
1. En una tarjeta presiona **✏️** → se abre el formulario con los datos → cambia el precio → **Guardar cambios**.
2. Presiona **🗑️** → pide confirmación → **"Producto eliminado correctamente."**
   *(Si el producto ya tiene ventas, avisa que no se puede borrar para no romper el historial.)*

**🛒 Ventas — registrar**
1. Entra a **Ventas**.
2. Escribe el nombre del producto en el campo de búsqueda y selecciónalo de la lista.
3. Pon la cantidad y (opcionalmente) un precio distinto.
4. Mira cómo se calculan solos el **Total** y la **Ganancia**:
   `Total = precio × cantidad` y `Ganancia = (precio de venta − precio de compra) × cantidad`.
5. Presiona **✅ Registrar venta** → *"Venta registrada correctamente."* y el inventario baja solo.
6. Pide 99 unidades de un producto con 2 → aparece **"No hay suficiente inventario."**

**💰 Ganancias**
1. Registra varias ventas y entra a **Ganancias**.
2. Verás las cuatro tarjetas (hoy / semana / mes / total) y el gráfico de los últimos 7 días.
3. Si no hay ventas, aparece *"Todavía no hay suficientes datos para mostrar estadísticas."*

**🤖 Asistente IA — chat**
1. Entra a **Asistente IA**.
2. Presiona una sugerencia rápida o escribe tu propia pregunta, por ejemplo:
   - *"¿Qué productos tengo disponibles?"* → lista los productos **reales** de tu base de datos.
   - *"¿Qué productos tienen inventario bajo?"* → lista las alertas.
   - *"¿Cuánto estoy ganando este mes?"* → muestra tus cifras reales.
   - *"¿Qué puedo publicar hoy para promocionar mis aretes?"* → ideas de contenido.
   - *"¿Cómo respondo a un cliente que pide precio?"* → respuesta lista para copiar.
3. Presiona **Enviar ➤** o `Enter` (con `Shift + Enter` haces un salto de línea).

**📱 Crear contenido**
1. Entra a **Crear contenido**.
2. Selecciona un **producto** (solo aparecen los de tu base de datos).
3. Elige **plataforma** (Instagram / TikTok / WhatsApp), **tipo** de contenido y **tono**.
4. Presiona **✨ Generar contenido**.
5. Te da: texto principal, llamado a la acción y hashtags.
6. Presiona **📋 Copiar texto** para pegarlo directo en tu red social.

**✨ Encuentra tu producto**
1. Entra a **Encuentra tu producto**.
2. Responde *"¿Qué estás buscando?"* (Accesorios / Regalo / Uso diario / Elegante).
3. Responde *"¿Qué estilo prefieres?"* (Minimalista / Elegante / Casual / Femenino).
4. Te recomienda hasta 3 productos **reales** de tu inventario, con el porqué.

**📊 Estadísticas**
1. Entra a **Estadísticas**.
2. Verás ventas por día (barras), reparto por categoría (circular), top productos
   y el valor del inventario con tu **ganancia potencial**.

**⚙️ Configuración**
1. Cambia el nombre del negocio, la moneda o el límite de inventario → **💾 Guardar**.
2. Mira el estado de la IA y la guía para configurarla.
3. Activa o desactiva el uso de la IA (si la apagas, sigue funcionando con datos reales).

---

## 8. Endpoints de la API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/products` | Lista productos (`?search=`, `?category=`, `?stock=low`, `?order=`) |
| POST | `/api/products` | Crea un producto |
| GET | `/api/products/<id>` | Un producto |
| PUT | `/api/products/<id>` | Actualiza un producto |
| DELETE | `/api/products/<id>` | Elimina un producto |
| GET | `/api/sales` | Historial de ventas |
| POST | `/api/sales` | Registra una venta (descuenta inventario) |
| GET | `/api/sales/preview` | Calcula total y ganancia sin guardar |
| DELETE | `/api/sales/<id>` | Anula una venta (devuelve unidades) |
| GET | `/api/dashboard` | Tarjetas, últimas ventas y alertas |
| GET | `/api/profits` | Ganancias por periodo (`?period=day\|week\|month\|all`) |
| GET | `/api/stats` | Estadísticas completas para gráficos |
| POST | `/api/ai/chat` | Chat con el asistente |
| POST | `/api/ai/content` | Genera contenido para redes |
| GET | `/api/ai/recommend/quiz` | Cuestionario del recomendador |
| POST | `/api/ai/recommend` | Recomendación de productos |
| GET | `/api/ai/status` | Estado de la IA (sin exponer la llave) |
| GET/PUT | `/api/settings` | Configuración del negocio |
| GET | `/api/health` | Comprobación rápida del servidor |

---

## 9. ¿Qué usa IA y qué usa base de datos?

### 🤖 Usa inteligencia artificial

| Parte | Endpoint | Qué hace |
|---|---|---|
| **Chat del asistente** | `POST /api/ai/chat` | Analiza la pregunta, detecta la intención (ventas, contenido, clientes, negocio, inventario) y responde. **Usa la API si está configurada**; si no, genera la respuesta con plantillas inteligentes. |
| **Generador de contenido** | `POST /api/ai/content` | Escribe el texto, el llamado a la acción y los hashtags del producto elegido, según plataforma y tono. |

> En **ambos** casos, antes de responder se le entrega a la IA la información
> **real** de tu base de datos (productos, precios, stock, ventas, ganancias).
> Por eso **nunca inventa** productos ni cifras.

### 🗄️ Usa la base de datos

| Tabla | Campos | Para qué sirve |
|---|---|---|
| **products** | `id, name, category, description, purchase_price, sale_price, stock, image, created_at` | Catálogo e inventario |
| **sales** | `id, product_id, product_name, category, quantity, sale_price, purchase_price, total, profit, customer, payment_method, created_at` | Historial y cálculo de ganancias |
| **settings** | `key, value` | Nombre del negocio, moneda, límite de inventario, mensaje de bienvenida |

Todo lo demás (tarjetas del panel, gráficos, alertas, recomendador, filtros y
búsquedas) se calcula **consultando SQLite**.

---

## 10. Datos de demostración

La primera vez que inicias la aplicación se crean **8 productos de ejemplo**:

| Producto | Categoría | Compra | Venta | Stock |
|---|---|---|---|---|
| Aretes Mariposa 🦋 | Aretes | 180 | 350 | 12 |
| Aretes Dorados | Aretes | 150 | 300 | 8 |
| Pinza Mariposa | Pinzas | 90 | 200 | 2 |
| Collar Minimalista | Collares | 220 | 450 | 5 |
| Pulsera Dorada | Pulseras | 130 | 280 | 1 |
| Labial Rosa Suave | Maquillaje | 160 | 320 | 7 |
| Crema Hidratante Floral | Skincare | 260 | 520 | 4 |
| Set de Joyería Mixto | Accesorios | 500 | 1000 | 3 |

> ⚠️ **Son datos ficticios de demostración.** Puedes **borrarlos** cuando quieras
> desde la sección **Productos** (botón 🗑️) o eliminar todos de golpe con:
>
> ```powershell
> # Cierra el servidor (Ctrl + C) y ejecuta:
> python -c "from app import create_app; from config import Config; from database.db import reset_demo_data; reset_demo_data(create_app(Config))"
> ```

---

## 11. Problemas frecuentes

| Síntoma | Solución |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Activaste mal el entorno virtual. Ejecuta `env\Scripts\activate` y luego `pip install -r requirements.txt` |
| `Address already in use / puerto 5000 ocupado` | Cierra la otra ventana del servidor, o cambia `PORT=5001` en el `.env` |
| La página abre pero está en blanco | Presiona `Ctrl + F5` para recargar sin caché |
| Dice *"La API key no es válida"* | Revisa `AI_API_KEY` en el `.env` (sin comillas ni espacios) y reinicia |
| Dice *"límite de uso (429)"* | Esperaste un momento o cambia de modelo en `AI_MODEL` |
| La IA no responde | Comprueba tu conexión a internet y que el `.env` tenga la llave |
| No aparecen los productos de ejemplo | Cierra el servidor, borra `database/database.db` y vuelve a iniciar |

---

## 12. Autor

Proyecto escolar de **Shevelle Beauty** — *Tu asistente inteligente para hacer crecer tu negocio* 🦋
