## Prompt 10 — Inventory

```
Role: Act as a senior backend developer.

Context: The sales system already generates inventory movements automatically (Prompt 8). Each product
has a current stock level and a configurable minimum stock level. Three alert levels are needed: Normal Stock,
Low Stock, and Out of Stock.

Task: Implement inventory query endpoints: current stock per product, product stock-in/stock-out history,
and an alerts list (products with "Low Stock" or "Out of Stock" status),
plus an endpoint to register manual inventory entries (e.g., a received purchase).

Format: "Inventory" controller and service, with the status calculation logic (normal/low/out of stock)
implemented as a pure, reusable function.

``` Restrictions: The alert status is calculated by comparing `stock_actual` against `stock_minimo`; it is not stored
as a fixed field that could become out of sync. A manual inventory entry must also generate a
record in `movimientos_inventario`, just like sales-related stock reductions. Only the Administrator can register
manual entries; the Salesperson can only view them.
```