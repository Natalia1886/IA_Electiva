"""Religious holiday computation engine.

Supports fixed-date holidays (day/month) and date-locked (variable) feasts
such as Easter and Corpus Christi, which shift each year.
"""
from datetime import date, timedelta

from app.models.holiday import ReligiousHoliday

VARIABLE_DATE_CODES = ("easter", "corpus_christi")


def _easter(year: int) -> date:
    """Anonymous Gregorian algorithm for Easter Sunday."""
    a = year % 19
    b, c = year // 100, year % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    l_ = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_) // 451
    month = (h + l_ - 7 * m + 114) // 31
    day = ((h + l_ - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _variable_date(holiday: ReligiousHoliday, year: int) -> date | None:
    if holiday.variable_date_code == "easter":
        return _easter(year)
    if holiday.variable_date_code == "corpus_christi":
        return _easter(year) + timedelta(days=60)
    return None


def next_occurrence(holiday: ReligiousHoliday, from_date: date) -> date:
    """Next occurrence of the feast at or after ``from_date``.

    A holiday with an explicit ``start_date`` recurs on that month/day from the
    given season onward; variable feasts (Easter/Corpus) are computed; fixed
    feasts use ``day``/``month``.
    """
    if holiday.start_date is not None:
        base = holiday.start_date
        candidate = date(from_date.year, base.month, base.day)
        if candidate < from_date:
            candidate = date(from_date.year + 1, base.month, base.day)
        return candidate

    if holiday.variable_date_code in VARIABLE_DATE_CODES:
        candidate = _variable_date(holiday, from_date.year)
        if candidate is None or candidate < from_date:
            candidate = _variable_date(holiday, from_date.year + 1)
        return candidate

    candidate = date(from_date.year, holiday.month, holiday.day)
    if candidate < from_date:
        candidate = date(from_date.year + 1, holiday.month, holiday.day)
    return candidate


def occurrence_end(holiday: ReligiousHoliday, occurrence: date) -> date:
    """End of the feast season for a given occurrence.

    Uses the registered ``end_date`` when present (same month/day, aligned to
    the occurrence year), otherwise the occurrence itself.
    """
    if holiday.end_date is None:
        return occurrence
    end = date(occurrence.year, holiday.end_date.month, holiday.end_date.day)
    if end < occurrence:
        end = date(occurrence.year + 1, holiday.end_date.month, holiday.end_date.day)
    return end


def upcoming_holidays(holidays: list[ReligiousHoliday], from_date: date, window_days: int = 60) -> list[dict]:
    results = []
    for holiday in holidays:
        if not holiday.is_active:
            continue
        occurrence = next_occurrence(holiday, from_date)
        delta = (occurrence - from_date).days
        if delta <= window_days:
            results.append(
                {
                    "id": holiday.id,
                    "name": holiday.name,
                    "date": occurrence,
                    "end_date": occurrence_end(holiday, occurrence),
                    "days_until": delta,
                    "factor": float(holiday.expected_demand_factor or 1.0),
                    "products": [
                        {"id": p.id, "code": p.code, "name": p.name, "stock": p.stock, "min_stock": p.min_stock}
                        for p in holiday.products
                        if p.is_active
                    ],
                }
            )
    return sorted(results, key=lambda h: h["days_until"])


def upcoming_holidays_json(holidays, from_date: date, window_days: int = 60) -> list[dict]:
    return [
        {**h, "date": h["date"].isoformat(), "end_date": h["end_date"].isoformat(), "products": h["products"]}
        for h in upcoming_holidays(holidays, from_date, window_days)
    ]