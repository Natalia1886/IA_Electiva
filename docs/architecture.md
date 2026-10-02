# 🏛️ Arquitectura del Sistema - Tienda Religiosa MilanFramework

Arquitectura modular en **cuatro capas** orientada a agentes inteligentes, skills determinísticas y machine learning aplicado al comercio minorista de artículos religiosos.

```mermaid
flowchart TD
    subgraph CAPA_INTERFACES["1. Capa de Interfaces"]
        UI["Web UI SPA (interfaces/web_ui/)"]
        API["FastAPI REST (interfaces/api/)"]
        CLI["CLI Interactivo (interfaces/cli/)"]
    end

    subgraph CAPA_ORQUESTADOR["2. Capa del Orquestador"]
        Router["Router de Tareas (core/orchestrator/router.py)"]
        Planner["Planificador (core/orchestrator/planner.py)"]
        Executor["Ejecutor con Trazas (core/orchestrator/executor.py)"]
    end

    subgraph CAPA_AGENTES["3. Capa de Agentes y Skills"]
        subgraph AGENTES["Agentes Inteligentes"]
            Ag1["Purchase Advisor Agent"]
            Ag2["Inventory Agent"]
            Ag3["Sales Agent"]
        end

        subgraph SKILLS["Skills Reutilizables"]
            Sk1["product_segmentation (ML RFV-F)"]
            Sk2["demand_forecaster (Cálculo de Demanda)"]
            Sk3["nl_explainer (Lenguaje Natural)"]
            Sk4["stock_monitor (Alertas de Quiebre)"]
            Sk5["db_repository (Transacciones ACID)"]
        end
    end

    subgraph CAPA_INFRA["4. Infraestructura Compartida"]
        DB["Base de Datos SQLite / SQLAlchemy"]
        Sec["Seguridad, Passwords PBKDF2 y Roles"]
        Mem["Memoria Corto / Largo Plazo"]
        Obs["Observabilidad, Trazas y Logs"]
    end

    UI --> API
    CLI --> Router
    API --> Router
    Router --> Planner --> Executor
    Executor --> Ag1 & Ag2 & Ag3
    Ag1 --> Sk1 & Sk2 & Sk3 & Sk5
    Ag2 --> Sk4 & Sk5
    Ag3 --> Sk5
    Sk5 --> DB
    Executor -.-> Obs
    API -.-> Sec
    Ag1 -.-> Mem
```

---

## 🏗️ Detalle de las Cuatro Capas

### 1. Capa de Interfaces (`interfaces/`)
Puntos de entrada e interacción con los usuarios:
- **`web_ui/`**: Interfaz de usuario intuitiva pensada para personas sin formación técnica (RNF01). Permite operar caja, ver inventario, registrar festividades y consultar recomendaciones con explicaciones en lenguaje cotidiano.
- **`api/`**: Servidor REST con **FastAPI**. Implementa control de acceso basado en roles (`ADMIN` y `VENDEDOR`) mediante JWT.
- **`cli/`**: Consola interactiva para administración, pruebas rápidas y simulaciones.

### 2. Capa del Orquestador (`core/orchestrator/`)
Coordina la toma de decisiones y la delegación de tareas:
- **`router.py`**: Identifica el `intent` de la solicitud y resuelve qué agente debe atenderlo.
- **`planner.py`**: Descompone tareas complejas (ej. asesoría de compras) en secuencias ordenadas de ejecución de skills.
- **`executor.py`**: Ejecuta el plan de forma controlada, capturando excepciones y emitiendo trazas de observabilidad.

### 3. Capa de Agentes y Skills (`agents/` y `skills/`)
- **Agentes (Deciden)**:
  - `purchase_advisor_agent`: Analiza el inventario disponible, el historial de ventas y las festividades católicas para aconsejar compras al administrador.
  - `inventory_agent`: Audita el catálogo, detecta quiebres y clasifica productos en riesgo.
  - `sales_agent`: Consolida el cierre diario, cálculo de ingresos y productos estrella.
- **Skills (Ejecutan determinísticamente)**:
  - `product_segmentation`: Modelo ML de agrupamiento según Recencia, Frecuencia, Varianza y afinidad con Festividades (RF11).
  - `demand_forecaster`: Algoritmo cuantitativo que proyecta la demanda para un horizonte de 15/30 días considerando multiplicadores festivos (RF12).
  - `nl_explainer`: Transforma datos numéricos en justificaciones sencillas y claras para el tendero (RF13).
  - `stock_monitor`: Evaluador de umbrales de stock mínimo y productos agotados (RF09).
  - `db_repository`: Acceso a datos con transaccionalidad atómica (RNF05) y registro auditable de movimientos (RNF08).

### 4. Capa de Infraestructura Compartida (`core/`)
- **`core/database/`**: Modelado relacional (`Product`, `Sale`, `SaleItem`, `InventoryMovement`, `Festivity`, `User`).
- **`core/security/`**: Hashing de contraseñas con PBKDF2-HMAC-SHA256 (RNF03), matriz RBAC (RNF04) y guardrails de negocio (precios positivos, stock no negativo).
- **`core/memory/`**: Memoria de corto plazo (sesión) y largo plazo (insights y resúmenes).
- **`core/observability/`**: Tracer de eventos y logger centralizado.
