# Diagrama de Componentes — MilanFramework

Componentes del framework con **PostgreSQL** como motor de base de datos en la capa de
persistencia. Generated a partir del estado real del codigo en `core/`, `interfaces/`,
`agents/`, `skills/`, `config/` y `docs/`.

## Diagrama

```mermaid
flowchart TD

    subgraph IF["1 · Capa de Interfaces · interfaces/"]
        CHAT["Chat UI<br/>interfaces/chat_ui/"]
        CLI["CLI interactivo<br/>interfaces/cli/main.py"]
        API["API REST · FastAPI<br/>interfaces/api/main.py<br/>auth · products · sales · inventory<br/>festivities · recommendations · dashboard"]
    end

    subgraph ORQ["2 · Capa de Orquestacion · core/orchestrator/"]
        ROUTER["Router de tareas<br/>router.py"]
        PLANNER["Planner de pasos<br/>planner.py"]
        EXECUTOR["Executor con trazas<br/>executor.py"]
    end

    subgraph REG["Registros y Contratos · core/"]
        AREG["BaseAgent + AGENT_REGISTRY<br/>core/agent_base/"]
        SREG["BaseSkill + SKILL_REGISTRY<br/>core/skill_base/"]
    end

    subgraph AG["3a · Agentes de IA · agents/"]
        PAA["PurchaseAdvisorAgent<br/>purchase_advisor_agent<br/>RF11-RF14 · HU07"]
        INVA["InventoryAgent<br/>inventory_agent<br/>RF09 · RF15 · HU05"]
        SALESA["SalesAgent<br/>sales_agent<br/>RF08"]
    end

    subgraph SK["3b · Skills · skills/"]
        DBR["db_repository<br/>Transacciones ACID + auditoria<br/>db_read · db_write"]
        SEG["product_segmentation<br/>ML no supervisado RFV-F<br/>ml_train · ml_inference"]
        FC["demand_forecaster<br/>Pronostico cuantitativo<br/>RF12"]
        NLE["nl_explainer<br/>Lenguaje natural<br/>RF13"]
        STM["stock_monitor<br/>Umbrales de stock<br/>RF09"]
    end

    subgraph INF["4 · Infraestructura Transversal · core/"]
        DB["database<br/>Modelos SQLAlchemy 2.x<br/>User · Product · Sale<br/>SaleItem · InventoryMovement · Festivity"]
        SEC["security<br/>auth.py · JWT + PBKDF2<br/>permissions.py · RBAC Admin/Vendedor<br/>guardrails.py"]
        MEM["memory<br/>memory_manager.py<br/>short_term · long_term"]
        OBS["observability<br/>logger.py · tracer.py"]
        GW["llm_gateway<br/>provider_router.py<br/>cost_tracker.py"]
    end

    subgraph SUP["5 · Soporte"]
        CFG["config<br/>agents.yaml · skills.yaml<br/>environments/dev.yaml · prod.yaml"]
        TOOLS["tools<br/>github_client.py<br/>slack_client.py"]
        EVALS["evaluations<br/>agent_benchmarks<br/>skill_tests"]
    end

    DBMS[("PostgreSQL<br/>milan_dev · milan_prod<br/>SQLAlchemy 2.x + psycopg2")]

    CHAT --> API
    CLI --> ROUTER
    API --> ROUTER

    ROUTER --> PLANNER
    PLANNER --> EXECUTOR

    EXECUTOR --> PAA
    EXECUTOR --> INVA
    EXECUTOR --> SALESA

    PAA --> DBR
    PAA --> SEG
    PAA --> FC
    PAA --> NLE
    INVA --> DBR
    INVA --> STM
    SALESA --> DBR

    DBR --> DB
    DB --> DBMS

    EXECUTOR -.-> OBS
    API -.-> SEC
    ROUTER -.-> SEC
    PAA -.-> MEM
    INVA -.-> MEM
    SALESA -.-> MEM
    PAA -.-> GW
    NLE -.-> GW
    PAA -.-> AREG
    INVA -.-> AREG
    SALESA -.-> AREG
    DBR -.-> SREG
    SEG -.-> SREG
    CFG -.-> AREG
    CFG -.-> DBMS
    EVALS -.-> AG
    TOOLS -.-> EXECUTOR
```

**Leyenda:** `-->` dependencia directa de ejecucion · `-.->` dependencia transversal.

## Resumen de Componentes

| Capa | Componentes | Estado |
| :--- | :--- | :--- |
| **1. Interfaces** (`interfaces/`) | `api/main.py` (FastAPI; rutas `auth`, `products`, `sales`, `inventory`, `festivities`, `recommendations`, `dashboard`), `cli/main.py`, `chat_ui/` | Stubs (0-1 lineas) |
| **2. Orquestador** (`core/orchestrator/`) | `router.py` (intent -> `AGENT_REGISTRY`), `planner.py` (descomposicion en skills), `executor.py` (retries, fallbacks, trazas) | Stubs (docstrings) |
| **3a. Agentes** (`agents/`) | `purchase_advisor_agent`, `inventory_agent`, `sales_agent` — cada uno con `agent.py` + `manifest.yaml` + `prompts/` | **Implementados** |
| **3b. Skills** (`skills/`) | `db_repository`, `product_segmentation`, `demand_forecaster`, `nl_explainer`, `stock_monitor` | `stock_monitor` y `product_segmentation` implementados; resto stub |
| **4. Transversales** (`core/`) | `database/`, `security/` (JWT+PBKDF2, RBAC, guardrails), `memory/`, `observability/`, `llm_gateway/`, `agent_base/`, `skill_base/` | `security/__init__.py` y ambos registries reales; resto stub |
| **5. Soporte** | `config/`, `tools/` (github, slack), `evaluations/` | Config real |

## PostgreSQL como motor de persistencia

Confirmado en tres fuentes independientes del repositorio:

- `requirements.txt:12` — `psycopg2-binary>=2.9.0`
- `config/environments/dev.yaml:3` — `postgresql://postgres:postgres@localhost:5432/milan_dev`
- `config/environments/prod.yaml:3` — `postgresql://milan_user:milan_password@localhost:5432/milan_prod`

Acceso a traves de **SQLAlchemy 2.x** (`requirements.txt:4`). Modelo relacional declarado:
`User`, `Product`, `Sale`, `SaleItem`, `InventoryMovement`, `Festivity`.

**Regla arquitectonica:** ningun agente accede a la base de datos directamente. Toda
persistencia pasa por la skill `db_repository` (`db_read`, `db_write`,
`inventory_atomic_update`), que es el unico dueno de la conexion y garantiza atomicidad
ACID en el descuento de existencias (RF06/RF07, RNF05).

## Dependencias de skills por agente

Segun los `manifest.yaml` de cada agente:

| Agente | Skills requeridas |
| :--- | :--- |
| `purchase_advisor_agent` | `db_repository`, `product_segmentation`, `demand_forecaster`, `nl_explainer` |
| `inventory_agent` | `db_repository`, `stock_monitor` |
| `sales_agent` | `db_repository` |

## Hallazgos tecnicos pendientes

1. **Documentacion desalineada con la configuracion.** Tres archivos siguen citando
   SQLite y contradicen `dev.yaml`/`prod.yaml`: `README.md:28`,
   `docs/architecture.md:91`, `docs/skills/sistema_skills.md:6`.
2. **Import roto.** `skills/product_segmentation/skill.py:6` importa
   `ProductSegmentationModel` desde `skills/product_segmentation/model.py`, archivo que
   no existe en el repositorio.
3. **Stubs importados en caliente.** Los tres agentes importan `memory_manager` y
   `get_logger` en tiempo de import, pero `core/memory/memory_manager.py` y
   `core/observability/logger.py` solo contienen comentarios: los agentes fallan al
   importarse.
4. **Inconsistencia de nombre de UI.** Existe `interfaces/chat_ui/`, pero `README.md:51`
   y `crear_estructura_framework.py` documentan `interfaces/web_ui/`.
5. **Contrato de seguridad no implementado.** `core/security/__init__.py` exporta
   `hash_password`, `check_permission`, `validate_product_data`, entre otros, que
   provienen de modulos con una sola linea de docstring.
