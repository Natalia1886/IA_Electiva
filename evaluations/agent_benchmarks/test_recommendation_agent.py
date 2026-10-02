"""Benchmark y prueba de integración para el Agente Asesor de Compras (HU07, RF12, RF13)."""

import agents
import skills
from core.database.connection import init_db
from core.database.seed_data import seed_database
from agents.purchase_advisor_agent.agent import PurchaseAdvisorAgent


def test_purchase_advisor_agent_execution():
    init_db()
    seed_database()

    agent = PurchaseAdvisorAgent()
    result = agent.run({"horizon_days": 15, "window_days": 30})

    assert "recommendations" in result
    recs = result["recommendations"]
    assert len(recs) > 0

    # Cada recomendación debe tener su explicación en lenguaje natural comprensible (RF13, HU07)
    for r in recs:
        assert "product_name" in r
        assert "suggested_quantity" in r
        assert "natural_language_reason" in r
        assert len(r["natural_language_reason"]) > 20
