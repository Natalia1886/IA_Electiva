#!/usr/bin/env python3
"""Genera los archivos .drawio (DER y Diagrama de Clases) de MilanFramework."""

from xml.sax.saxutils import escape as _escape


def escape(s, _entities=None):
    """Escapa tambien las comillas dobles: los valores van en atributos XML delimitados por ".
    Las comillas simples se dejan intactas porque el HTML embebido las usa como delimitador.
    """
    return _escape(s, {'"': "&quot;"})

# ---------------------------------------------------------------- DER

ER_ENTITIES = [
    ("ROLES", "Identidad", ["int id PK", "string name UK \"ADMIN, VENDEDOR\"", "string description", "boolean is_active"]),
    ("USERS", "Identidad", ["uuid id PK", "int role_id FK", "string username UK", "string email UK", "string password_hash \"PBKDF2, RNF03\"", "string full_name", "boolean is_active", "datetime last_login_at", "datetime created_at"]),
    ("SESSIONS", "Identidad", ["uuid id PK", "uuid user_id FK", "string refresh_token_hash", "string ip_address", "string user_agent", "boolean is_revoked", "datetime expires_at"]),
    ("CHAT_SESSIONS", "Identidad", ["uuid id PK", "uuid user_id FK", "string title", "string channel \"chat_ui, cli, api\"", "string context_summary", "int message_count", "datetime started_at", "datetime last_activity_at", "datetime ended_at"]),
    ("CHAT_MESSAGES", "Identidad", ["uuid id PK", "uuid chat_session_id FK", "string role \"user, assistant, system, tool\"", "text content", "jsonb tool_calls", "int prompt_tokens", "int completion_tokens", "datetime created_at"]),

    ("CATEGORIES", "Catalogo", ["int id PK", "string name UK", "string description", "boolean is_active"]),
    ("PRODUCTS", "Catalogo", ["int id PK", "int category_id FK", "string code UK", "string name", "string description", "numeric price \"no negativo\"", "int stock_actual", "int stock_minimo", "boolean is_active \"filtro active_only\"", "datetime created_at", "datetime updated_at"]),
    ("INVENTORY_MOVEMENTS", "Catalogo", ["bigint id PK", "int product_id FK", "int sale_id FK", "int user_id FK", "string movement_type \"ENTRADA, SALIDA, AJUSTE\"", "int quantity", "int stock_before", "int stock_after", "string reason \"RNF08\"", "datetime created_at"]),
    ("INVENTORY_ALERTS", "Catalogo", ["bigint id PK", "int product_id FK", "int trace_id FK", "string alert_type \"AGOTADO, STOCK_BAJO\"", "string severity \"CRITICA, ALTA\"", "string message", "string status \"OPEN, ACK, RESOLVED\"", "int acknowledged_by FK", "datetime detected_at", "datetime resolved_at"]),

    ("SALES", "Ventas", ["int id PK", "uuid user_id FK", "string document_number UK", "decimal total_amount", "int transaction_count \"RF08\"", "string payment_method", "datetime sold_at", "datetime created_at"]),
    ("SALE_ITEMS", "Ventas", ["bigint id PK", "int sale_id FK", "int product_id FK", "int quantity", "decimal unit_price", "decimal subtotal"]),

    ("FESTIVITIES", "Festividades", ["int id PK", "string name", "string description", "date start_date", "date end_date", "numeric demand_factor \"RF10\"", "boolean is_active"]),
    ("FESTIVITY_PRODUCTS", "Festividades", ["int festivity_id PK,FK", "int product_id PK,FK", "numeric demand_factor \"por producto\""]),

    ("AGENTS", "ML y Recomendaciones", ["int id PK", "string name UK", "string version", "string manifest_path", "boolean is_active \"config/agents.yaml\"", "jsonb required_skills", "jsonb permissions"]),
    ("SKILLS", "ML y Recomendaciones", ["int id PK", "string name UK", "string version", "string manifest_path", "boolean is_active \"config/skills.yaml\"", "jsonb permissions"]),
    ("ML_MODELS", "ML y Recomendaciones", ["int id PK", "string name \"product_segmentation\"", "string algorithm \"KMeans RFV-F\"", "string version", "boolean is_active \"RNF06\"", "jsonb hyperparameters", "datetime trained_at"]),
    ("MODEL_TRAINING_RUNS", "ML y Recomendaciones", ["bigint id PK", "int ml_model_id FK", "uuid triggered_by FK \"RF14 admin\"", "string status", "int sample_size", "jsonb metrics", "text log", "datetime started_at", "datetime finished_at"]),
    ("PRODUCT_SEGMENTS", "ML y Recomendaciones", ["bigint id PK", "int ml_model_id FK", "int product_id FK", "int segment_label", "string segment_name", "numeric recency \"RF11\"", "numeric frequency \"RF11\"", "numeric variance \"RF11\"", "numeric festivity_affinity", "datetime computed_at"]),
    ("PURCHASE_RECOMMENDATIONS", "ML y Recomendaciones", ["bigint id PK", "int product_id FK", "int festivity_id FK", "uuid requested_by FK \"RF14 admin\"", "int suggested_quantity", "numeric estimated_cost", "string priority \"URGENTE, ALTA, MEDIA\"", "text natural_language_reason \"RF13\"", "jsonb raw_forecast", "string status", "datetime created_at"]),

    ("MEMORY_ENTRIES", "Runtime IA", ["bigint id PK", "uuid user_id FK", "uuid chat_session_id FK", "int agent_id FK", "string memory_scope \"SHORT_TERM, LONG_TERM\"", "string memory_key \"sales_summary_2026-01-15\"", "jsonb content", "float importance_score", "int access_count", "datetime expires_at \"TTL corto plazo\"", "datetime created_at"]),
    ("TRACES", "Runtime IA", ["uuid id PK", "uuid parent_trace_id FK", "uuid chat_session_id FK", "uuid user_id FK", "int agent_id FK", "int skill_id FK", "string traceable_type \"ORCHESTRATOR, AGENT, SKILL, LLM\"", "string operation", "string status \"OK, ERROR, FALLBACK\"", "jsonb input_payload", "jsonb output_payload", "text error_trace", "int duration_ms", "datetime started_at", "datetime finished_at"]),
    ("LLM_CALLS", "Runtime IA", ["bigint id PK", "uuid trace_id FK", "int agent_id FK", "uuid chat_session_id FK", "string provider", "string model \"local_heuristic\"", "int prompt_tokens", "int completion_tokens", "int total_tokens", "decimal cost_usd", "int latency_ms", "boolean cache_hit", "datetime created_at"]),
    ("COST_LEDGER", "Runtime IA", ["bigint id PK", "uuid user_id FK", "int agent_id FK", "date period_date", "int total_calls", "int total_tokens", "decimal total_cost_usd", "decimal budget_limit_usd", "string alert_status \"WITHIN, WARNING, EXCEEDED\""]),
]

# (source, target, cardinality_source, cardinality_target, label)
ER_RELATIONS = [
    ("ROLES", "USERS", "||", "o{", "asigna rol"),
    ("USERS", "SESSIONS", "||", "o{", "autentica mediante"),
    ("USERS", "CHAT_SESSIONS", "||", "o{", "inicia"),
    ("CHAT_SESSIONS", "CHAT_MESSAGES", "||", "|{", "contiene"),
    ("USERS", "SALES", "||", "o{", "registra venta"),
    ("USERS", "INVENTORY_MOVEMENTS", "||", "o{", "ejecuta movimiento"),
    ("USERS", "MODEL_TRAINING_RUNS", "||", "o{", "dispara reentrenamiento"),
    ("USERS", "PURCHASE_RECOMMENDATIONS", "||", "o{", "solicita"),
    ("USERS", "TRACES", "||", "o{", "origina"),
    ("USERS", "COST_LEDGER", "||", "o{", "consume"),
    ("USERS", "MEMORY_ENTRIES", "||", "o{", "posee"),
    ("CATEGORIES", "PRODUCTS", "||", "o{", "clasifica"),
    ("PRODUCTS", "SALE_ITEMS", "||", "o{", "vendido en"),
    ("PRODUCTS", "INVENTORY_MOVEMENTS", "||", "o{", "genera"),
    ("PRODUCTS", "INVENTORY_ALERTS", "||", "o{", "produce"),
    ("PRODUCTS", "PRODUCT_SEGMENTS", "||", "o{", "clasificado en"),
    ("PRODUCTS", "FESTIVITY_PRODUCTS", "||", "o{", "asociado a"),
    ("PRODUCTS", "PURCHASE_RECOMMENDATIONS", "||", "o{", "recomendado"),
    ("SALES", "SALE_ITEMS", "||", "|{", "contiene minimo uno"),
    ("SALES", "INVENTORY_MOVEMENTS", "||", "o{", "descuenta stock atomico RNF05"),
    ("INVENTORY_ALERTS", "TRACES", "o|", "o{", "detectada por"),
    ("FESTIVITIES", "FESTIVITY_PRODUCTS", "||", "o{", "incluye"),
    ("FESTIVITIES", "PURCHASE_RECOMMENDATIONS", "||", "o{", "motiva"),
    ("FESTIVITY_PRODUCTS", "PRODUCTS", "||", "||", "referencia"),
    ("AGENTS", "TRACES", "||", "o{", "ejecuta"),
    ("AGENTS", "MEMORY_ENTRIES", "||", "o{", "escribe"),
    ("AGENTS", "LLM_CALLS", "||", "o{", "consume"),
    ("AGENTS", "COST_LEDGER", "||", "o{", "agregado en"),
    ("AGENTS", "SKILLS", "}o", "o{", "declara skills_required"),
    ("SKILLS", "TRACES", "||", "o{", "invocada en"),
    ("ML_MODELS", "MODEL_TRAINING_RUNS", "||", "o{", "se entrena con"),
    ("ML_MODELS", "PRODUCT_SEGMENTS", "||", "o{", "produce"),
    ("CHAT_SESSIONS", "MEMORY_ENTRIES", "||", "o{", "contexto de"),
    ("CHAT_SESSIONS", "TRACES", "||", "o{", "agrupa"),
    ("CHAT_SESSIONS", "LLM_CALLS", "||", "o{", "consume"),
    ("TRACES", "LLM_CALLS", "||", "o{", "detalla costo de"),
    ("TRACES", "TRACES", "o|", "o{", "contiene subspan"),
]

CARD = {
    "||": "ERmandOne",
    "o|": "ERzeroToOne",
    "|{": "ERone",
    "o{": "ERzeroToMany",
    "}o": "ERzeroToMany",
    "}|": "ERmandMany",
}

ER_COLORS = {
    "Identidad": ("#e8f4f8", "#6c8ebf"),
    "Catalogo": ("#d5e8d4", "#82b366"),
    "Ventas": ("#dae8fc", "#6c8ebf"),
    "Festividades": ("#fff2cc", "#d6b656"),
    "ML y Recomendaciones": ("#e1d5e7", "#9673a6"),
    "Runtime IA": ("#ffe6cc", "#d79b00"),
}

EW, EGAP, ATTR_H = 240, 50, 15
BAND_TITLE_H = 30
ATTR_LINES = 16


def build_er():
    out = []
    a = out.append
    a('<mxfile host="app.diagrams.net" type="device">')
    a('  <diagram id="milan-er" name="DER">')
    a('    <mxGraphModel dx="1600" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1900" pageHeight="1400" math="0" shadow="0" adaptiveColors="auto">')
    a('      <root>')
    a('        <mxCell id="0" />')
    a('        <mxCell id="1" parent="0" />')

    y = 30
    positions = {}
    band_ids = {}
    for domain in ER_COLORS:
        ents = [e for e in ER_ENTITIES if e[1] == domain]
        if not ents:
            continue
        bw = len(ents) * (EW + EGAP) - EGAP + 40
        maxlines = max(len(e[2]) for e in ents)
        bh = BAND_TITLE_H + maxlines * ATTR_LINES + 30
        bid = f"band_{domain.replace(' ', '_')}"
        band_ids[domain] = bid
        fill, stroke = ER_COLORS[domain]
        a(f'        <mxCell id="{bid}" value="{escape(domain)}" style="swimlane;startSize={BAND_TITLE_H};html=1;fillColor={fill};strokeColor={stroke};fontStyle=1;align=left;spacingLeft=10;swimlaneFillColor=#ffffff;verticalAlign=top;" vertex="1" parent="1">')
        a(f'          <mxGeometry x="30" y="{y}" width="{bw}" height="{bh}" as="geometry" />')
        a('        </mxCell>')
        for i, (name, _d, attrs) in enumerate(ents):
            eh = 26 + len(attrs) * ATTR_LINES + 10
            ex = 20 + i * (EW + EGAP)
            ey = BAND_TITLE_H + 8
            cell = f"e_{name}"
            positions[name] = cell
            rows = "".join(
                f"<div style='text-align:left;padding-left:6'>{at}</div>" for at in attrs
            )
            label = (
                f"<div style='font-weight:bold;background-color:{stroke};color:#ffffff;"
                f"margin:-6px -6px 4px -6px;padding:4px 6px'>{name}</div>"
                f"<div style='font-family:monospace;font-size:10px'>{rows}</div>"
            )
            a(f'        <mxCell id="{cell}" value="{escape(label)}" style="rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fillColor=#ffffff;strokeColor={stroke};strokeWidth=2;spacing=0;" vertex="1" parent="{bid}">')
            a(f'          <mxGeometry x="{ex}" y="{ey}" width="{EW}" height="{eh}" as="geometry" />')
            a('        </mxCell>')
        y += bh + 30

    for n, (src, tgt, cs, ct, label) in enumerate(ER_RELATIONS, start=1):
        style = (
            "edgeStyle=entityRelationEdgeStyle;html=1;rounded=0;"
            f"startArrow={CARD[cs]};startFill=0;"
            f"endArrow={CARD[ct]};endFill=0;"
            "strokeColor=#555555;fontSize=10;labelBackgroundColor=#ffffff;"
        )
        a(f'        <mxCell id="er{n}" value="{escape(label)}" style="{style}" edge="1" parent="1" source="{positions[src]}" target="{positions[tgt]}">')
        a('          <mxGeometry relative="1" as="geometry" />')
        a('        </mxCell>')

    nb = "\u00a0"
    legend = (
        "<b>Cardinalidades (notacion pata de cuervo)</b><br>"
        "<font style='font-size:10px'>"
        f"ERmandOne = exactamente 1 {nb}·{nb} ERone = 1 o muchos<br>"
        f"ERzeroToOne = 0 o 1 {nb}·{nb} ERzeroToMany = 0 o muchos<br><br>"
        "<b>PostgreSQL</b> &lt;·&gt; SQLAlchemy 2.x + psycopg2 &lt;·&gt; uuid, jsonb, timestamptz"
        "</font>"
    )
    a(f'        <mxCell id="legend" value="{escape(legend)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;align=left;verticalAlign=middle;spacingLeft=12;fontSize=11;" vertex="1" parent="1">')
    a(f'          <mxGeometry x="30" y="{y}" width="420" height="100" as="geometry" />')
    a('        </mxCell>')

    a('      </root>')
    a('    </mxGraphModel>')
    a('  </diagram>')
    a('</mxfile>')
    return "\n".join(out)


# ------------------------------------------------------- DIAGRAMA DE CLASES

CL_DOMAINS = [
    ("Contratos Base", "#f5f5f5", "#999999", [
        ("BaseAgent", ["<<abstract>>", "+str name", "+run(task) Dict"], []),
        ("BaseSkill", ["<<abstract>>", "+str name", "+run(params) Dict"], []),
        ("AgentRegistry", ["<<singleton>>", "+dict AGENT_REGISTRY", "+register_agent(agent_cls)", "+get_agent(name) BaseAgent", "+list_active() List"], []),
        ("SkillRegistry", ["<<singleton>>", "+dict SKILL_REGISTRY", "+register_skill(skill_cls)", "+get_skill(name) BaseSkill", "+list_active() List"], []),
    ]),
    ("Orquestacion", "#dae8fc", "#6c8ebf", [
        ("Orchestrator", ["+str environment", "+handle_request(intent) Dict", "+shutdown()"], []),
        ("Router", ["+route(intent) str", "-dict AGENT_REGISTRY"], []),
        ("Planner", ["+build_plan(task) List", "+estimate_steps(task) int"], []),
        ("Executor", ["+int max_retries", "+execute(plan) Dict", "+fallback(plan) Dict"], []),
    ]),
    ("Memoria", "#d5e8d4", "#82b366", [
        ("MemoryManager", ["+remember(key, value, persistent) int", "+recall(key) Dict", "+recall_recent(scope, limit) List", "+forget(key) bool", "+summarize() Dict"], []),
        ("ShortTermMemory", ["<<volatile>>", "+int ttl_seconds", "+put(key, value) None", "+get(key) Dict", "+purge_expired() int"], []),
        ("LongTermMemory", ["+put(key, value, importance) int", "+search(query, top_k) List", "+consolidate() int"], []),
        ("MemoryEntry", [], ["+bigint id", "+uuid user_id", "+uuid chat_session_id", "+int agent_id", "+str memory_scope", "+str memory_key", "+dict content", "+datetime expires_at"]),
        ("MemoryScope", ["<<enumeration>>", "SHORT_TERM", "LONG_TERM"], []),
    ]),
    ("LLM Gateway", "#fff2cc", "#d6b656", [
        ("LLMGateway", ["+generate(prompt, context) Dict", "+complete(task) Dict"], []),
        ("ProviderRouter", ["+str active_provider", "+route_prompt(prompt) str", "+available_providers() List"], []),
        ("CostTracker", ["+record_call(tokens_in, tokens_out, model) Decimal", "+get_summary(period) Dict", "+check_budget(limit) str"], []),
        ("LLMCall", [], ["+bigint id", "+uuid trace_id", "+str provider", "+str model", "+int prompt_tokens", "+int completion_tokens", "+decimal cost_usd"]),
    ]),
    ("Observabilidad", "#e1d5e7", "#9673a6", [
        ("Tracer", ["+uuid start_span(traceable_type, operation) str", "+end_span(trace_id, status) None", "+get_trace(trace_id) Dict"], []),
        ("LogManager", ["+get_logger(name) Logger", "+set_level(level) None"], []),
        ("Trace", [], ["+uuid id", "+uuid parent_trace_id", "+str traceable_type", "+str operation", "+str status", "+int duration_ms", "+datetime started_at"]),
        ("TraceableType", ["<<enumeration>>", "ORCHESTRATOR", "AGENT", "SKILL", "LLM"], []),
    ]),
    ("Seguridad", "#f8cecc", "#b85450", [
        ("AuthService", ["+hash_password(pwd) str", "+verify_password(pwd, hashed) bool", "+create_access_token(user) str", "+decode_token(token) Dict"], []),
        ("PermissionChecker", ["+dict ROLE_PERMISSIONS", "+check_permission(role, permission) bool", "+is_admin(role) bool"], []),
        ("Guardrails", ["+validate_product_data(data) Dict", "+validate_sale_items(items) List"], []),
        ("BusinessValidationError", ["<<exception>>", "+str message", "+str field"], []),
    ]),
    ("Persistencia", "#ffe6cc", "#d79b00", [
        ("DatabaseManager", ["+str engine_url", "+get_session() Session", "+transaction() UnitOfWork", "+health_check() bool"], []),
        ("UnitOfWork", ["+commit() None", "+rollback() None"], []),
        ("User", [], ["+uuid id", "+str username", "+str password_hash", "+str role", "+bool is_active"]),
        ("Product", [], ["+int id", "+str code", "+str name", "+decimal price", "+int stock_actual", "+int stock_minimo", "+bool is_active"]),
        ("Sale", [], ["+int id", "+uuid user_id", "+decimal total_amount", "+datetime sold_at"]),
        ("SaleItem", [], ["+bigint id", "+int sale_id", "+int product_id", "+int quantity", "+decimal unit_price"]),
        ("InventoryMovement", [], ["+bigint id", "+int product_id", "+int sale_id", "+str movement_type", "+int quantity", "+int stock_before", "+int stock_after"]),
        ("MovementType", ["<<enumeration>>", "ENTRADA", "SALIDA", "AJUSTE"], []),
        ("Festivity", [], ["+int id", "+str name", "+date start_date", "+date end_date", "+decimal demand_factor"]),
    ]),
    ("Agentes", "#d5e8d4", "#82b366", [
        ("PurchaseAdvisorAgent", ["+str name", "+int horizon_days", "+int window_days", "+run(task) Dict"], []),
        ("InventoryAgent", ["+str name", "+run(task) Dict"], []),
        ("SalesAgent", ["+str name", "+run(task) Dict"], []),
    ]),
    ("Skills", "#fff2cc", "#d6b656", [
        ("DbRepositorySkill", ["+str name", "+run(params) Dict"], []),
        ("ProductSegmentationSkill", ["+str name", "+run(params) Dict", "+retrain() Dict"], []),
        ("ProductSegmentationModel", ["+int n_clusters", "+bool is_fitted", "+extract_features(products, sales, festivities, window) DataFrame", "+train_and_segment(df) List"], []),
        ("DemandForecasterSkill", ["+str name", "+run(params) Dict"], []),
        ("NlExplainerSkill", ["+str name", "+run(params) Dict"], []),
        ("StockMonitorSkill", ["+str name", "+run(params) Dict"], []),
    ]),
]

# (origen, destino, tipo, etiqueta, cardinalidad_src, cardinalidad_dst)
CL_RELATIONS = [
    ("BaseAgent", "PurchaseAdvisorAgent", "<|--", "", None, None),
    ("BaseAgent", "InventoryAgent", "<|--", "", None, None),
    ("BaseAgent", "SalesAgent", "<|--", "", None, None),
    ("BaseSkill", "DbRepositorySkill", "<|--", "", None, None),
    ("BaseSkill", "ProductSegmentationSkill", "<|--", "", None, None),
    ("BaseSkill", "DemandForecasterSkill", "<|--", "", None, None),
    ("BaseSkill", "NlExplainerSkill", "<|--", "", None, None),
    ("BaseSkill", "StockMonitorSkill", "<|--", "", None, None),
    ("AgentRegistry", "BaseAgent", "..>", "registra", None, None),
    ("SkillRegistry", "BaseSkill", "..>", "registra", None, None),
    ("Orchestrator", "Router", "*--", "", "1", "*"),
    ("Orchestrator", "Planner", "*--", "", "1", "*"),
    ("Orchestrator", "Executor", "*--", "", "1", "*"),
    ("Router", "AgentRegistry", "..>", "consulta", None, None),
    ("Executor", "AgentRegistry", "..>", "instancia agente", None, None),
    ("Executor", "SkillRegistry", "..>", "instancia skill", None, None),
    ("Executor", "Tracer", "..>", "emite spans", None, None),
    ("Executor", "Guardrails", "..>", "valida entradas", None, None),
    ("Executor", "PermissionChecker", "..>", "verifica rol", None, None),
    ("PurchaseAdvisorAgent", "SkillRegistry", "..>", "resuelve 4 skills", None, None),
    ("PurchaseAdvisorAgent", "MemoryManager", "-->", "persiste recomendaciones", "1", "*"),
    ("PurchaseAdvisorAgent", "LogManager", "..>", "logs", None, None),
    ("InventoryAgent", "MemoryManager", "-->", "persiste alertas", "1", "*"),
    ("InventoryAgent", "LogManager", "..>", "logs", None, None),
    ("SalesAgent", "MemoryManager", "-->", "persiste resumen diario", "1", "*"),
    ("SalesAgent", "LogManager", "..>", "logs", None, None),
    ("PurchaseAdvisorAgent", "ProductSegmentationModel", "*--", "", "1", "1"),
    ("ProductSegmentationSkill", "ProductSegmentationModel", "*--", "", "1", "1"),
    ("DbRepositorySkill", "DatabaseManager", "*--", "", "1", "1"),
    ("MemoryManager", "ShortTermMemory", "*--", "", "1", "1"),
    ("MemoryManager", "LongTermMemory", "*--", "", "1", "1"),
    ("MemoryManager", "Tracer", "..>", "traza escrituras", None, None),
    ("ShortTermMemory", "MemoryEntry", "..>", "persiste", None, None),
    ("LongTermMemory", "MemoryEntry", "..>", "persiste", None, None),
    ("LLMGateway", "ProviderRouter", "*--", "", "1", "*"),
    ("LLMGateway", "CostTracker", "*--", "", "1", "1"),
    ("ProviderRouter", "Tracer", "..>", "traza decision", None, None),
    ("CostTracker", "LLMCall", "*--", "registra", None, None),
    ("Tracer", "Trace", "..>", "persiste", None, None),
    ("DatabaseManager", "UnitOfWork", "*--", "", None, "1"),
    ("DatabaseManager", "Product", "..>", "mapea ORM", None, None),
    ("DatabaseManager", "Sale", "..>", "mapea ORM", None, None),
    ("DatabaseManager", "SaleItem", "..>", "mapea ORM", None, None),
    ("DatabaseManager", "InventoryMovement", "..>", "mapea ORM", None, None),
    ("DatabaseManager", "Festivity", "..>", "mapea ORM", None, None),
    ("DatabaseManager", "User", "..>", "mapea ORM", None, None),
    ("AuthService", "User", "..>", "verifica credenciales", None, None),
    ("AuthService", "PermissionChecker", "..>", "delega rol", None, None),
    ("Guardrails", "BusinessValidationError", "..>", "lanza", None, None),
    ("Guardrails", "Product", "..>", "valida", None, None),
    ("Guardrails", "SaleItem", "..>", "valida", None, None),
    ("MemoryScope", "MemoryEntry", "..>", "tipa", None, None),
    ("TraceableType", "Trace", "..>", "tipa", None, None),
    ("MovementType", "InventoryMovement", "..>", "tipa", None, None),
    ("Sale", "SaleItem", "*--", "", "1", "1..*"),
    ("Product", "SaleItem", "*--", "", "1", "1..*"),
    ("SaleItem", "InventoryMovement", "..>", "origina", "0..1", "*"),
    ("Festivity", "Product", "-->", "factor demanda", "*", "*"),
]

CW, CGAP, CH = 230, 40, 130


def build_classes():
    out = []
    a = out.append
    a('<mxfile host="app.diagrams.net" type="device">')
    a('  <diagram id="milan-classes" name="Diagrama de Clases">')
    a('    <mxGraphModel dx="1600" dy="1200" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1900" pageHeight="1400" math="0" shadow="0" adaptiveColors="auto">')
    a('      <root>')
    a('        <mxCell id="0" />')
    a('        <mxCell id="1" parent="0" />')

    y = 30
    pos = {}
    for domain, fill, stroke, classes in CL_DOMAINS:
        per_row = min(len(classes), 4)
        rows = (len(classes) + per_row - 1) // per_row
        bw = per_row * (CW + CGAP) - CGAP + 40
        bh = BAND_TITLE_H + rows * (CH + 30) + 20
        bid = f"cl_{domain.replace(' ', '_')}"
        a(f'        <mxCell id="{bid}" value="{escape(domain)}" style="swimlane;startSize={BAND_TITLE_H};html=1;fillColor={fill};strokeColor={stroke};fontStyle=1;align=left;spacingLeft=10;swimlaneFillColor=#ffffff;verticalAlign=top;" vertex="1" parent="1">')
        a(f'          <mxGeometry x="30" y="{y}" width="{bw}" height="{bh}" as="geometry" />')
        a('        </mxCell>')
        for i, (name, methods, attrs) in enumerate(classes):
            r, c = divmod(i, per_row)
            cx = 20 + c * (CW + CGAP)
            cy = BAND_TITLE_H + 10 + r * (CH + 30)
            pos[name] = (bid, cx, cy)
            stereotype = ""
            body = ""
            if methods:
                mcolor = "#eef4fb" if methods[0].startswith("<<") else "#f7f7f7"
                rows_m = "".join(
                    f"<div style='text-align:left;padding-left:4'>{x}</div>" for x in methods
                )
                stereotype = (
                    f"<div style='background-color:{mcolor};font-style:italic;padding:2px 4px;"
                    f"margin:-6px -6px 2px -6px;text-align:center;font-size:10px'>{methods[0]}</div>"
                )
                body += (
                    f"<div style='font-family:monospace;font-size:10px;background-color:#ffffff;"
                    f"padding:3px 0;margin:0 -6px 3px -6px'>{rows_m}</div>"
                )
            if attrs:
                rows_a = "".join(
                    f"<div style='text-align:left;padding-left:4'>{x}</div>" for x in attrs
                )
                body += (
                    f"<div style='font-family:monospace;font-size:10px;background-color:#fbfbfb;"
                    f"padding:3px 0;margin:0 -6px -6px -6px;border-top:1px solid #dddddd'>{rows_a}</div>"
                )
            label = (
                f"<div style='font-weight:bold;background-color:{stroke};color:#ffffff;"
                f"margin:-6px -6px 4px -6px;padding:4px 6px;font-size:11px'>{name}</div>"
                f"{stereotype}{body}"
            )
            a(f'        <mxCell id="c_{name}" value="{escape(label)}" style="rounded=0;whiteSpace=wrap;html=1;align=left;verticalAlign=top;fillColor=#ffffff;strokeColor={stroke};strokeWidth=2;spacing=0;" vertex="1" parent="{bid}">')
            a(f'          <mxGeometry x="{cx}" y="{cy}" width="{CW}" height="{CH}" as="geometry" />')
            a('        </mxCell>')
        y += bh + 30

    for n, (src, tgt, kind, label, cs, ct) in enumerate(CL_RELATIONS, start=1):
        style = "edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor=#666666;fontSize=9;labelBackgroundColor=#ffffff;"
        if kind == "*--":
            style += "endArrow=ERmany;startArrow=ERone;endFill=0;startFill=0;"
        elif kind == "<|--":
            style += "endArrow=block;endFill=0;"
        elif kind == "..>":
            style += "endArrow=open;dashed=1;"
        else:
            style += "endArrow=open;"
        if label:
            style += f"edgeLabel='{escape(label)}';"
        a(f'        <mxCell id="cr{n}" style="{style}" edge="1" parent="1" source="c_{src}" target="c_{tgt}">')
        a(f'          <mxGeometry relative="1" as="geometry" />')
        a('        </mxCell>')

    nb = "\u00a0"
    legend = (
        "<b>Relaciones</b><br>"
        "<font style='font-size:10px'>"
        f"&lt;|-- hereda (extends) {nb}·{nb} *-- composicion<br>"
        f"..&gt; dependencia (uso puntual) {nb}·{nb} --&gt; asociacion<br><br>"
        "<b>Convención de campos</b><br>"
        "<font style='font-size:10px'>"
        "Los agentes leen stock_actual / stock_minimo en español<br>"
        "(stock_monitor.py); los manifests usan inglés."
        "</font>"
    )
    a(f'        <mxCell id="cllegend" value="{escape(legend)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;align=left;verticalAlign=middle;spacingLeft=12;fontSize=11;" vertex="1" parent="1">')
    a(f'          <mxGeometry x="30" y="{y}" width="460" height="110" as="geometry" />')
    a('        </mxCell>')

    a('      </root>')
    a('    </mxGraphModel>')
    a('  </diagram>')
    a('</mxfile>')
    return "\n".join(out)


if __name__ == "__main__":
    with open("docs/diagrams/diagrama_entidades.drawio", "w", encoding="utf-8") as f:
        f.write(build_er())
    print("OK diagrama_entidades.drawio")
    with open("docs/diagrams/diagrama_clases.drawio", "w", encoding="utf-8") as f:
        f.write(build_classes())
    print("OK diagrama_clases.drawio")
