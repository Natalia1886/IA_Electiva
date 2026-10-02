"""Punto de entrada por línea de comandos (CLI) para la tienda religiosa (MilanFramework)."""

import sys
import agents
import skills
from core.database.connection import init_db
from core.database.seed_data import seed_database
from core.orchestrator.executor import Executor
from core.skill_base.skill_registry import SKILL_REGISTRY


def run_cli():
    init_db()
    seed_database()
    executor = Executor()

    print("\n" + "=" * 60)
    print("   TIENDA DE ARTÍCULOS RELIGIOSOS SAN CAYETANO - CLI")
    print("   Sistema Inteligente de Inventario y Recomendaciones")
    print("=" * 60)

    while True:
        print("\nOpciones disponibles:")
        print(" 1. Ver estado de inventario y alertas de stock (HU05)")
        print(" 2. Ejecutar recomendaciones de compra con IA (HU07)")
        print(" 3. Ver resumen de ventas del día (RF08)")
        print(" 4. Registrar una venta de prueba (HU03)")
        print(" 5. Salir")

        try:
            choice = input("\nSeleccione una opción (1-5): ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if choice == "1":
            print("\n--- CONSULTANDO ALERTAS DE INVENTARIO ---")
            task = {"intent": "stock_alerts"}
            res = executor.execute(task)
            alerts = res.get("result", {}).get("alerts", [])
            if not alerts:
                print("No hay alertas de stock bajo ni agotados.")
            else:
                for a in alerts:
                    print(f" [{a['alert_type']}] {a['product_name']} | Stock: {a['stock_actual']} (Mínimo: {a['stock_minimo']})")

        elif choice == "2":
            print("\n--- EJECUTANDO RECOMENDACIONES DE COMPRA CON IA (RF12, RF13) ---")
            task = {"intent": "recommend_purchases", "horizon_days": 15, "window_days": 30}
            res = executor.execute(task)
            recs = res.get("result", {}).get("recommendations", [])
            print(f"\nTotal recomendaciones generadas: {len(recs)}")
            for r in recs:
                print("\n" + "-" * 50)
                print(f"Artículo: {r['product_name']} ({r['category']})")
                print(f"Prioridad: {r['priority']} | Stock Actual: {r['stock_actual']} | Cantidad Sugerida: {r['suggested_quantity']}")
                print(f"Motivo en Lenguaje Natural:\n  \"{r['natural_language_reason']}\"")

        elif choice == "3":
            print("\n--- RESUMEN DE VENTAS DEL DÍA (RF08) ---")
            task = {"intent": "daily_summary"}
            res = executor.execute(task)
            summary = res.get("result", {})
            print(f"Fecha: {summary.get('date')}")
            print(f"Total vendido: ${summary.get('total_sales_amount', 0):,.2f}")
            print(f"Transacciones: {summary.get('transaction_count', 0)}")
            print("Top artículos más vendidos:")
            for p in summary.get("top_products", []):
                print(f"  - {p['name']}: {p['units_sold']} unid. (${p['revenue']:,.2f})")

        elif choice == "4":
            print("\n--- REGISTRAR VENTA DE PRUEBA ---")
            db_skill = SKILL_REGISTRY["db_repository"]()
            prods = db_skill.run({"action": "get_products", "filters": {"active_only": True}}).get("products", [])
            print("Productos disponibles:")
            for p in prods[:5]:
                print(f"  ID: {p['id']} | {p['name']} | Precio: ${p['price']} | Stock: {p['stock_actual']}")

            try:
                pid = int(input("\nIngrese ID del producto: ").strip())
                qty = int(input("Ingrese cantidad: ").strip())
                sale_res = db_skill.run({
                    "action": "register_sale",
                    "sale_data": {
                        "items": [{"product_id": pid, "quantity": qty}],
                        "payment_method": "EFECTIVO"
                    },
                    "user_id": 1
                })
                print(f"\n[OK] Venta exitosa #{sale_res.get('sale_number')}. Total: ${sale_res.get('total_amount'):,.2f}")
                print("El stock ha sido descontado automáticamente y se registró en la auditoría.")
            except Exception as e:
                print(f"[ERROR] No se pudo registrar la venta: {e}")

        elif choice == "5":
            print("\nSaliendo del CLI de la Tienda Religiosa. ¡Hasta pronto!")
            break
        else:
            print("Opción inválida.")


if __name__ == "__main__":
    run_cli()
