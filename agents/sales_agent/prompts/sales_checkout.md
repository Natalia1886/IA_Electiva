# CRUD
## Prompt 9 — Sales System

```
Role: Act as a senior backend developer, paying special attention to transactional data integrity.

Context: Product CRUD is already implemented. A sale involves: sale registration → sale details
(products, quantities, prices) → automatic stock deduction → inventory movement record →
statistics update for the daily summary. Every sale is associated with the salesperson who registered it.

Task: Implement the sale registration endpoint that executes the entire flow above as a single
atomic operation, plus endpoints for querying sales and the daily summary (day's sales, total
amount sold, number of transactions, highest-moving products).

Format: "Sales" controller and service, including the use of a database transaction that
groups the creation of the sale, the details, and the inventory movement.

Constraints: If stock for any product is insufficient, the entire sale must be rejected (rollback);
the sale must not be created with inconsistent stock levels. Stock deduction and the recording of
inventory movement must occur within the same transaction as the sale, not as separate steps
that could fail independently. Do not allow a sale to be registered without at least one product in the details.
```



## Prompt 15 — Sales Module

```
Role: Act as a senior frontend developer specializing in transactional flows (checkout).

Context: POST /ventas endpoint already implemented with automatic stock deduction (Prompt 8). This module
is used by both roles.

Task: Build the "New Sale" screen featuring a product cart: product search/selection, quantity, price,
line-item subtotal, grand total, payment method selection, and final confirmation that sends the
sale to the backend.

Format: Page component featuring the cart, real-time total calculations, and a post-sale
confirmation screen/modal.

Constraints: Do not allow adding a quantity to the cart that exceeds the product's available stock
(client-side validation, reinforced by the backend in Prompt 8). The total must automatically
recalculate upon any change in quantity or product; it must never become out of sync.
```
