"""Ejecutor de pruebas para evaluaciones de agentes y skills sin requerir pytest."""

import sys
import os

# Asegurar que el directorio raíz esté en sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluations.skill_tests.test_segmentation import test_segmentation_with_festivity_factor
from evaluations.skill_tests.test_forecaster import test_forecaster_calculates_purchase_needed
from evaluations.skill_tests.test_stock_monitor import test_stock_monitor_alerts
from evaluations.agent_benchmarks.test_recommendation_agent import test_purchase_advisor_agent_execution


def run_all_tests():
    print("=" * 60)
    print(" EJECUTANDO EVALUACIONES Y PRUEBAS DEL FRAMEWORK")
    print("=" * 60)

    tests = [
        ("Skill: Monitoreo de Niveles de Stock (RF09, HU05)", test_stock_monitor_alerts),
        ("Skill: Segmentación ML RFV-Festividades (RF11, RNF06)", test_segmentation_with_festivity_factor),
        ("Skill: Pronóstico de Demanda y Compras (RF12)", test_forecaster_calculates_purchase_needed),
        ("Agente: Asesor de Compras con Lenguaje Natural (HU07, RF12, RF13)", test_purchase_advisor_agent_execution),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f" [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f" [FAIL] {name}: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f" RESULTADO FINAL: {passed} exitosas, {failed} fallidas")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    run_all_tests()
