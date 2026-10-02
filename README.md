# 🕊️ Sistema Inteligente de Ventas, Inventario y Recomendaciones con IA
### Tienda de Artículos Religiosos "San Cayetano" — Electiva IA (8º Semestre)

Sistema integral de gestión de ventas, control de inventario y asesoría inteligente de compras basado en una **arquitectura por capas orientada a agentes y skills de Inteligencia Artificial**.

---

## 🎯 Contexto del Negocio y Hallazgos Clave

A partir de las entrevistas con los responsables de la tienda de imaginería y artículos religiosos (vírgenes, santos, velas, pesebres y crucifijos en Ibagué):

1. **Dependencia de cuadernos físicos**: El negocio no contaba con inventario sistematizado y registraba ventas manualmente.
2. **Mercancía estancada**: Productos comprados por hábito o promociones que se acumulaban en bodega sin rotación.
3. **Quiebres de stock en festividades**: Velas y figuras devocionales agotadas repentinamente en celebraciones clave (Semana Santa, Fiestas de Ibagué, Virgen del Carmen).
4. **Baja familiaridad técnica**: El tendero necesita una interfaz simple, amigable y explicaciones en **lenguaje natural**, sin jerga técnica ni fórmulas complejas.
5. **Decisiones de compra guiadas por IA**: El sistema recomienda activamente **qué comprar, cuánto comprar y por qué motivo**.

---

## 🏗️ Arquitectura en Cuatro Capas

```text
MilanFramework/
├── core/                                # Infraestructura compartida y base
│   ├── orchestrator/                    # router, planner, executor
│   ├── agent_base/                      # BaseAgent y AGENT_REGISTRY
│   ├── skill_base/                      # BaseSkill y SKILL_REGISTRY
│   ├── database/                        # SQLAlchemy, SQLite y modelos relacionales
│   ├── security/                        # Hash PBKDF2, JWT y control RBAC (Admin/Vendedor)
│   ├── memory/                          # Memoria a corto y largo plazo
│   ├── llm_gateway/                     # Generador en lenguaje natural y control de costos
│   └── observability/                   # Trazas de ejecución y logs
├── agents/                              # Agentes de IA especializados
│   ├── purchase_advisor_agent/          # Recomendador de compras con IA (RF11-RF14, HU07)
│   ├── inventory_agent/                 # Auditor de stock y alertas de quiebre (RF09, HU05)
│   └── sales_agent/                     # Analista de ventas y cierre diario (RF08)
├── skills/                              # Capacidades modulares y determinísticas
│   ├── product_segmentation/            # Segmentación ML por Recencia, Frecuencia, Varianza y Festividades
│   ├── demand_forecaster/               # Cálculo cuantitativo de compras y horizonte de días
│   ├── nl_explainer/                    # Generador de explicaciones claras para no técnicos
│   ├── stock_monitor/                   # Monitoreo de umbrales (Agotado, Stock Bajo, Normal)
│   └── db_repository/                   # Transacciones atómicas ACID y auditoría de inventario
├── tools/                               # Integraciones utilitarias (db_client, report_exporter)
├── config/                              # Declaración de agentes/skills activos y entornos
├── evaluations/                         # Pruebas automatizadas y benchmarks
│   ├── agent_benchmarks/
│   ├── skill_tests/
│   └── run_tests.py
├── interfaces/                          # Puntos de contacto con el usuario
│   ├── api/                             # API REST completa con FastAPI
│   ├── web_ui/                          # Interfaz Web SPA clara e intuitiva
│   └── cli/                             # Consola interactiva para pruebas rápidas
├── docs/                                # Documentación de arquitectura y requerimientos
│   ├── architecture.md
│   ├── requerimientos_y_mapeo.md
│   └── manifest_schema.md
├── crear_estructura_framework.py        # Generador de estructura del framework
└── requirements.txt                     # Dependencias del proyecto
```

---

## 🚀 Cómo Ejecutar el Proyecto

### 1. Iniciar el Servidor API y la Interfaz Web
Ejecute el siguiente comando en la raíz del proyecto:

```bash
uvicorn interfaces.api.main:app --reload
```

Abra su navegador en: **`http://localhost:8000`**

La interfaz web cargará automáticamente el dashboard, el catálogo de ventas, el inventario y las recomendaciones de IA.

#### Credenciales de Prueba (RF01, RF02):
- **Administrador**: Usuario `admin` | Contraseña `admin123`
- **Vendedor**: Usuario `vendedor1` | Contraseña `vendedor123`

---

### 2. Ejecutar la Consola Interactiva (CLI)
Si prefiere interactuar por terminal:

```bash
python -m interfaces.cli.main
```

Permite consultar alertas, registrar ventas de prueba con descuento atómico y correr las recomendaciones de compra en lenguaje natural.

---

### 3. Ejecutar las Pruebas y Evaluaciones
Para comprobar el correcto funcionamiento de los modelos de Machine Learning, el cálculo de demanda y el agente de compras:

```bash
python evaluations/run_tests.py
```

---

## 📊 Cobertura de Requerimientos del Sistema

- **RF01 & RF02**: Autenticación con contraseña cifrada y separación estricta de roles (**Admin** vs **Vendedor**).
- **RF03, RF04 & RF05**: Gestión de productos con validación de precios no negativos, stock de seguridad y filtros por categoría.
- **RF06 & RF07**: Registro de ventas multi-producto con **descuento atómico de existencias** (RNF05).
- **RF08**: Balance diario de ventas, total recaudado, transacciones y artículos más vendidos.
- **RF09 & RNF08**: Histórico auditable de movimientos de inventario (`ENTRADA`, `SALIDA`, `AJUSTE`) y visualización de stock.
- **RF10**: Calendario de festividades religiosas (Semana Santa, Fiestas de Ibagué, Virgen del Carmen) con factor de demanda.
- **RF11 & RNF06**: Modelo de Machine Learning para segmentación de artículos basado en **Recencia, Frecuencia, Varianza y Festividades**, con capacidad de reentrenamiento continuo.
- **RF12 & RF13**: Generación de recomendaciones de compra en **lenguaje natural comprensible para tenderos sin formación técnica**.
- **RF14**: Privacidad y seguridad: solo el Administrador tiene acceso a las recomendaciones de compra y al reentrenamiento.
- **RF15**: Dashboard integral con ventas del día, alertas tempranas de productos agotados y métricas clave.
