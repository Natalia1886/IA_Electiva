#!/usr/bin/env python3
"""
Genera el árbol de carpetas y archivos base del Framework de Inteligencia Artificial
adaptado para el Sistema Inteligente de Ventas, Inventario y Recomendaciones de la
Tienda de Artículos Religiosos (Electiva IA).

Uso:
    python crear_estructura_framework.py [ruta_destino]
"""

import sys
from pathlib import Path

CARPETAS = [
    "core/orchestrator",
    "core/agent_base",
    "core/skill_base",
    "core/memory",
    "core/llm_gateway",
    "core/security",
    "core/database",
    "core/observability",
    "agents/purchase_advisor_agent/prompts",
    "agents/inventory_agent/prompts",
    "agents/sales_agent/prompts",
    "skills/db_repository",
    "skills/product_segmentation",
    "skills/demand_forecaster",
    "skills/nl_explainer",
    "skills/stock_monitor",
    "tools",
    "config/environments",
    "evaluations/agent_benchmarks",
    "evaluations/skill_tests",
    "interfaces/api",
    "interfaces/cli",
    "interfaces/web_ui",
    "docs",
]

ARCHIVOS_MINIMOS = {
    "config/agents.yaml": "active_agents:\n  - purchase_advisor_agent\n  - inventory_agent\n  - sales_agent\n",
    "config/skills.yaml": "active_skills:\n  - db_repository\n  - product_segmentation\n  - demand_forecaster\n  - nl_explainer\n  - stock_monitor\n",
    "config/environments/dev.yaml": "environment: dev\nllm_provider: local_heuristic\nlog_level: debug\n",
    "config/environments/prod.yaml": "environment: prod\nllm_provider: local_heuristic\nlog_level: info\n",
    "evaluations/agent_benchmarks/README.md": "# Benchmarks de Agentes\nPruebas para los agentes de compras, inventario y ventas.\n",
    "evaluations/skill_tests/README.md": "# Tests de Skills\nPruebas unitarias de segmentación ML, cálculo de demanda y monitoreo de stock.\n",
    ".gitignore": "__pycache__/\n*.pyc\n.env\n.venv/\n*.db\n",
}


def crear_estructura(base: Path) -> None:
    base.mkdir(parents=True, exist_ok=True)

    for carpeta in CARPETAS:
        (base / carpeta).mkdir(parents=True, exist_ok=True)

    for ruta_relativa, contenido in ARCHIVOS_MINIMOS.items():
        ruta = base / ruta_relativa
        ruta.parent.mkdir(parents=True, exist_ok=True)
        if not ruta.exists():
            ruta.write_text(contenido, encoding="utf-8")
            print(f"  creado: {ruta_relativa}")

    # __init__.py en paquetes importables
    paquetes = [
        "core", "agents", "skills", "tools",
        "core/orchestrator", "core/agent_base", "core/skill_base",
        "core/memory", "core/llm_gateway", "core/security",
        "core/database", "core/observability",
        "evaluations"
    ]
    for paquete in paquetes:
        init_file = base / paquete / "__init__.py"
        if not init_file.exists():
            init_file.write_text("", encoding="utf-8")


def main() -> None:
    destino = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    print(f"Creando/ajustando estructura en: {destino.resolve()}\n")
    crear_estructura(destino)
    print(f"\n[OK] Estructura ajustada en: {destino.resolve()}")


if __name__ == "__main__":
    main()
