"""Stock status rule — pure, dependency-free domain logic.

The alert status is always *computed* from the current stock versus the
configured minimum; it is never persisted (a stored flag would go stale the
moment a sale or manual entry changes stock).

Levels:
    * ``normal``       -> stock above the minimum
    * ``low``          -> between 1 and the minimum
    * ``out_of_stock`` -> zero (or negative) units
"""
from typing import Literal

StockStatus = Literal["normal", "low", "out_of_stock"]


def compute_stock_status(stock: int, min_stock: int) -> StockStatus:
    if stock <= 0:
        return "out_of_stock"
    if stock <= min_stock:
        return "low"
    return "normal"