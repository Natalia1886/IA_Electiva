# 📜 Esquema de Manifiestos (`manifest.yaml`)

Cada agente y skill en **MilanFramework** declara un contrato explícito mediante un archivo `manifest.yaml` en su propio directorio.

---

## 1. Manifiesto de Agente

```yaml
name: purchase_advisor_agent
version: 1.0.0
description: Agente de recomendación de compras que analiza inventario, histórico de ventas y festividades religiosas
skills_required:
  - db_repository
  - product_segmentation
  - demand_forecaster
  - nl_explainer
permissions:
  - db_read
  - ml_inference
  - recommendations_generate
input_schema:
  horizon_days: integer
  window_days: integer
output_schema:
  total_recommendations: integer
  urgent_count: integer
  recommendations: array
```

---

## 2. Manifiesto de Skill

```yaml
name: product_segmentation
version: 1.0.0
description: Modelo ML no supervisado para segmentación de productos por Recencia, Frecuencia, Varianza y Festividades
permissions:
  - ml_train
  - ml_inference
input_schema:
  products: array
  sales_history: array
  festivities: array
  window_days: integer
output_schema:
  segmented_products: array
```
