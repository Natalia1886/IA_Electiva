## Prompt 8 — Product CRUD

```
Role: Act as a senior backend developer.

Context: Backend with authentication and roles already implemented (Prompt 6). Product and category
data models defined in [paste Prompt 3]. Only the Administrator can create, edit, and delete products;
both roles can view them.

Task: Implement the full CRUD for products: create, list (with category filtering and name search),
get by ID, update, and deactivate (do not physically delete the record).

Format: Controller, service/repository, and routes for the "products" resource, connected to the
actual database, adhering to the project's folder structure.