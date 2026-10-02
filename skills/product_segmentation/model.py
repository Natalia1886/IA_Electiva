"""Modelo de Machine Learning para segmentación de productos (RF11, RNF06).
Calcula variables RFV-F: Recencia, Frecuencia, Varianza y Afinidad a Festividades.
Permite reentrenamiento dinámico sin rediseñar el sistema.
"""

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from typing import List, Dict, Any
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


class ProductSegmentationModel:
    """Clase del modelo de segmentación reentrenable."""

    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.is_fitted = False
        self.last_trained_at = None

    def extract_features(
        self,
        products: List[Dict[str, Any]],
        sales_history: List[Dict[str, Any]],
        festivities: List[Dict[str, Any]],
        window_days: int = 30
    ) -> pd.DataFrame:
        """Extrae características de Recencia, Frecuencia, Varianza y Festividades por producto."""
        now = datetime.now()
        data = []

        # Mapa de ventas por producto
        prod_sales_map: Dict[int, List[Dict[str, Any]]] = {p["id"]: [] for p in products}
        for item in sales_history:
            pid = item["product_id"]
            if pid in prod_sales_map:
                prod_sales_map[pid].append(item)

        for p in products:
            pid = p["id"]
            items = prod_sales_map.get(pid, [])

            if items:
                dates = [datetime.strptime(it["date"], "%Y-%m-%d") for it in items]
                most_recent_date = max(dates)
                recency_days = (now - most_recent_date).days
                frequency = len(items)
                quantities = [it["quantity"] for it in items]
                variance = float(np.var(quantities)) if len(quantities) > 1 else 0.0
                total_units = sum(quantities)
            else:
                recency_days = window_days + 15
                frequency = 0
                variance = 0.0
                total_units = 0

            # Afinidad con próximas festividades (RF10, RF11)
            festivity_score = 1.0
            pname_lower = p["name"].lower()
            pcat_lower = p["category"].lower()

            for fest in festivities:
                aff_cats = [c.lower().strip() for c in fest.get("affected_categories", [])]
                aff_prods = [pr.lower().strip() for pr in fest.get("affected_products", [])]
                if pcat_lower in aff_cats or any(ap in pname_lower for ap in aff_prods):
                    festivity_score = max(festivity_score, float(fest.get("demand_factor", 1.5)))

            data.append({
                "product_id": pid,
                "name": p["name"],
                "category": p["category"],
                "stock_actual": p["stock_actual"],
                "stock_minimo": p["stock_minimo"],
                "recency": float(recency_days),
                "frequency": float(frequency),
                "variance": float(variance),
                "festivity_factor": float(festivity_score),
                "total_units_sold": float(total_units)
            })

        return pd.DataFrame(data)

    def train_and_segment(self, df_features: pd.DataFrame) -> List[Dict[str, Any]]:
        """Entrena el modelo de segmentación y asigna etiquetas legibles."""
        if len(df_features) == 0:
            return []

        feature_cols = ["recency", "frequency", "variance", "festivity_factor"]
        X = df_features[feature_cols].values

        if len(df_features) >= self.n_clusters:
            X_scaled = self.scaler.fit_transform(X)
            self.kmeans.fit(X_scaled)
            self.is_fitted = True
            self.last_trained_at = datetime.now()
            clusters = self.kmeans.labels_
        else:
            clusters = [0] * len(df_features)

        results = []
        for idx, row in df_features.iterrows():
            recency = row["recency"]
            freq = row["frequency"]
            fest = row["festivity_factor"]

            # Clasificación semántica del negocio para el tendero:
            if fest > 1.2 and (row["stock_actual"] <= row["stock_minimo"] * 2 or freq >= 2):
                segment = "ESTACIONAL_FESTIVO"
                description = "Producto de alta demanda por festividad religiosa cercana."
            elif freq >= 5 and recency <= 7:
                segment = "ALTA_ROTACION"
                description = "Producto de rotación continua diaria; requiere mantener stock activo."
            elif freq <= 1 and recency > 15:
                segment = "LENTA_ROTACION"
                description = "Producto acumulado con baja rotación; evitar compras excesivas."
            else:
                segment = "ROTACION_MODERADA"
                description = "Demanda estándar y comportamiento regular."

            results.append({
                "product_id": int(row["product_id"]),
                "name": row["name"],
                "category": row["category"],
                "stock_actual": int(row["stock_actual"]),
                "stock_minimo": int(row["stock_minimo"]),
                "recency_days": row["recency"],
                "frequency_sales": row["frequency"],
                "variance": round(row["variance"], 2),
                "festivity_factor": row["festivity_factor"],
                "total_units_sold": row["total_units_sold"],
                "segment": segment,
                "segment_description": description
            })

        return results
