# 📋 Mapeo de Requerimientos e Historias de Usuario

Sistema Inteligente de Ventas, Inventario y Recomendaciones para Tienda de Artículos Religiosos (**MilanFramework**).

---

## 📌 Requerimientos Funcionales (RF)

| ID | Requerimiento | Módulo | Implementación en el Proyecto |
|---|---|---|---|
| **RF01** | Inicio de sesión con usuario y contraseña | Autenticación | `core/security/auth.py`, `interfaces/api/routes_auth.py` (`POST /api/auth/login`) |
| **RF02** | Distinción de dos roles: Administrador y Vendedor con permisos diferenciados | Autenticación | `core/security/permissions.py`, `interfaces/api/dependencies.py` (`require_admin`, `get_current_user`) |
| **RF03** | Administrador puede crear, consultar, editar y desactivar productos | Productos | `interfaces/api/routes_products.py`, `skills/db_repository/skill.py` |
| **RF04** | Asociar cada producto a una categoría y a un precio válido (>= 0) | Productos | `core/database/models.py` (`Product`), `core/security/guardrails.py` (`validate_product_data`) |
| **RF05** | Ambos roles pueden consultar el listado con búsqueda y filtro por categoría | Productos | `interfaces/api/routes_products.py` (`GET /api/products`), `interfaces/web_ui/app.js` |
| **RF06** | Registrar una venta con uno o más productos, cantidades y total calculado | Ventas | `core/database/models.py` (`Sale`, `SaleItem`), `interfaces/api/routes_sales.py` (`POST /api/sales`) |
| **RF07** | Toda venta descuenta automáticamente el stock de los productos vendidos | Ventas | `skills/db_repository/skill.py` (`_register_sale`: descuento atómico de stock) |
| **RF08** | Generar resumen diario con ventas, total vendido, transacciones y productos con mayor movimiento | Ventas | `agents/sales_agent/agent.py`, `skills/db_repository/skill.py` (`get_daily_summary`), `interfaces/api/routes_sales.py` (`GET /api/sales/daily`) |
| **RF09** | Mostrar stock actual, stock mínimo y el historial de entradas/salidas de cada producto | Inventario | `core/database/models.py` (`InventoryMovement`), `skills/stock_monitor/skill.py`, `interfaces/api/routes_inventory.py` |
| **RF10** | Administrador puede registrar festividades religiosas con fechas, productos y factor de demanda | Festividades | `core/database/models.py` (`Festivity`), `interfaces/api/routes_festivities.py` (`POST /api/festivities`) |
| **RF11** | Entrenar y usar modelo de segmentación de productos basado en frecuencia, recencia, varianza y festividades | ML / Recomendaciones | `skills/product_segmentation/model.py`, `skills/product_segmentation/skill.py` |
| **RF12** | Generar recomendaciones de compra (producto, cantidad y motivo) cruzando inventario, historial y festividades | Recomendaciones | `skills/demand_forecaster/skill.py`, `agents/purchase_advisor_agent/agent.py` |
| **RF13** | Recomendaciones presentadas en lenguaje natural comprensible para un usuario no técnico | Recomendaciones | `skills/nl_explainer/skill.py`, `agents/purchase_advisor_agent/prompts/` |
| **RF14** | Solo el administrador puede ver las recomendaciones de compra | Recomendaciones | `interfaces/api/routes_recommendations.py` (`Depends(require_admin)`), UI `.admin-only` |
| **RF15** | Dashboard con ventas, inventario, alertas, productos más vendidos y recomendaciones | Dashboard | `interfaces/api/routes_dashboard.py`, `interfaces/web_ui/index.html` (Dashboard consolidado) |

---

## 🔒 Requerimientos No Funcionales (RNF)

| ID | Requerimiento | Estrategia de Cumplimiento |
|---|---|---|
| **RNF01** | Usabilidad para personas sin formación técnica, lenguaje simple | Interfaz gráfica intuitiva (`interfaces/web_ui/`), explicaciones empáticas generadas por `nl_explainer` sin jerga técnica. |
| **RNF02** | Pantallas principales cargan en menos de 3 segundos | Respuestas JSON ultrarrápidas con FastAPI y SQLite indexado; frontend SPA ligero sin dependencias pesadas. |
| **RNF03** | Contraseñas cifradas con algoritmo de hash seguro | `core/security/auth.py` implementa PBKDF2-HMAC-SHA256 con salt criptográfico de 16 bytes e iteraciones. |
| **RNF04** | Validación de roles tanto en frontend como en backend | Backend: inyección de dependencias `require_admin` en FastAPI (HTTP 403 Forbidden). Frontend: control visual condicional en `app.js`. |
| **RNF05** | Descuento de stock atómico y transaccional | `skills/db_repository/skill.py` ejecuta `db.commit()` y `db.rollback()` en un único bloque transaccional ACID de base de datos. |
| **RNF06** | Modelo de segmentación reentrenable sin rediseñar el sistema | `ProductSegmentationModel` en `skills/product_segmentation/model.py` cuenta con método `train_and_segment()` y endpoint `POST /api/recommendations/retrain`. |
| **RNF07** | Código de backend, frontend e IA/ML versionado y documentado | Estructura modular estandarizada, manifiestos YAML, docstrings y control de versiones Git. |
| **RNF08** | Histórico auditable de movimientos de inventario | Tabla `inventory_movements` registra cada cambio de stock con tipo (`ENTRADA`, `SALIDA`), cantidad, stock anterior, stock nuevo, motivo y usuario responsable. |

---

## 👤 Historias de Usuario (HU)

### HU01 – Inicio de sesión con control de roles
- **Admin**: Acceso concedido al menú completo, alertas, festividades y recomendaciones de compra con IA.
- **Vendedor**: Acceso concedido a catálogo y caja de ventas. Opciones de recomendaciones y gestión administrativa ocultas y protegidas.
- **Credenciales inválidas**: Rechazo de acceso con mensaje genérico de seguridad sin revelar el campo erróneo.

### HU02 – Registro de productos por el Administrador
- Registro con validación: el precio no puede ser negativo (`core/security/guardrails.py`).
- Bloqueo a usuarios con rol Vendedor (HTTP 403).

### HU03 – Registro de ventas con stock suficiente
- Venta atómica: descuenta unidades, genera el detalle de venta y crea automáticamente un movimiento de inventario de tipo `SALIDA`.
- Alerta si se intenta vender más unidades de las disponibles en tienda.

### HU05 – Alertas de inventario
- Productos con `stock_actual == 0` marcados como **Agotado** (severidad Crítica).
- Productos con `stock_actual <= stock_minimo` marcados como **Stock Bajo** (severidad Alta).

### HU06 – Gestión de festividades religiosas
- Registro de celebraciones locales (Semana Santa, Fiestas de Ibagué, Virgen del Carmen) con rango de fechas y factor de aumento de demanda (ej. 1.8x, 2.5x).

### HU07 – Recomendación de compras con IA
- Antes de una festividad o quiebre de stock, el sistema sugiere qué producto comprar, cuántas unidades pedir y la justificación clara en lenguaje natural basada en el comportamiento histórico y el inventario disponible.
- Si un producto tiene sobre-stock o nula rotación, aconseja **NO comprar** para no estancar capital.
