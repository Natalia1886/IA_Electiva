"""Exportador utilitario de reportes de ventas e inventario a formatos legibles."""

import csv
import io
from typing import List, Dict, Any


class ReportExporter:
    """Exporta información de ventas y alertas a texto/CSV para consulta o impresión."""

    @staticmethod
    def export_sales_csv(sales_items: List[Dict[str, Any]]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Fecha", "Producto", "Categoría", "Cantidad", "Subtotal"])
        for item in sales_items:
            writer.writerow([
                item.get("date", ""),
                item.get("product_name", ""),
                item.get("category", ""),
                item.get("quantity", 0),
                item.get("subtotal", 0.0)
            ])
        return output.getvalue()
