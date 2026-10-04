## Prompt 18 — Religious holidays


Role: Act as a senior full-stack developer.

Context: The purchase recommender (Prompt 16) needs to know the religious holidays relevant
to the store, their dates, and associated products in order to anticipate demand. Examples of holidays:
Holy Week, Christmas, Day of the Virgin, All Saints' Day.

Task: Implement the holiday management module: CRUD functionality allowing the Administrator to register
a holiday, start date, end date, related products, and an expected demand factor (e.g.,
a multiplier or impact category: low/medium/high).

Format: Backend endpoints for the "holidays" resource (CRUD) and the corresponding frontend screen (table +
form), following the same pattern used in the product CRUD (Prompts 7 and 13).

Constraints: Only the Administrator can manage holidays. A holiday must be associable with
multiple products (many-to-many relationship), not just one. The expected demand factor must be
available for the recommendation model (Prompt 16) to consume directly from the database.