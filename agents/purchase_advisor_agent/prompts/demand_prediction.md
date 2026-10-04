Role: Act as a senior Machine Learning engineer responsible for the proprietary segmentation and demand estimation model.

Context: There is an ML model, trained by the team using real store data, that segments products based on: sales frequency, days since the last sale, sales variance over a period, category, and correlation with religious dates. The goal of this component is to calculate numerical purchase recommendations by cross-referencing current inventory, minimum stock levels, sales history, and upcoming holidays.

Task: Implement the core ML and numerical calculation pipeline:
(1) Feature engineering based on digitized historical data.
(2) Training and evaluation of the segmentation model using specific metrics.
(3) Logic that cross-references the model output with inventory/minimum stock/upcoming holidays to calculate a recommended quantity and identify the underlying data-driven reason.

Format:
1. Script/notebook for feature engineering and model training, with evaluation metrics reported (not just the code, but the results as well).
2. Function/service that calculates the recommended quantity per product.

Constraints: The segmentation model must be explainable: recommendations must include the reason derived from actual features (not generic text disconnected from the data). Do not replace your custom ML model with a direct call to an LLM—the ML model makes the decision on quantities and demand estimation.