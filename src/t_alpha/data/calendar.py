from __future__ import annotations

from bisect import bisect_right


def parse_yyyymmdd(value: str | int) -> int:
    text = str(value)
    if len(text) != 8 or not text.isdigit():
        raise ValueError("date must use YYYYMMDD format")
    return int(text)


def _sorted_calendar(calendar: list[int]) -> list[int]:
    return sorted(int(day) for day in calendar)


def previous_trade_day(calendar: list[int], date_value: int) -> int:
    cal = _sorted_calendar(calendar)
    idx = bisect_right(cal, date_value) - 1
    if idx < 0:
        raise ValueError("no trading day at or before requested date")
    return cal[idx]


def previous_n_trade_days(calendar: list[int], end_date: int, n: int) -> tuple[int, int]:
    cal = _sorted_calendar(calendar)
    normalized_end = previous_trade_day(cal, end_date)
    end_idx = cal.index(normalized_end)
    start_idx = max(0, end_idx - n + 1)
    return cal[start_idx], normalized_end


def normalize_date_range(
    calendar: list[int],
    start_date: str | int | None,
    end_date: str | int | None,
    default_count: int = 10,
) -> tuple[int, int]:
    cal = _sorted_calendar(calendar)
    if not cal:
        raise ValueError("calendar is empty")

    parsed_end = parse_yyyymmdd(end_date) if end_date is not None else cal[-1]
    normalized_end = previous_trade_day(cal, parsed_end)

    # 未传开始日期时，按交易日历倒推，避免自然日包含周末和节假日。
    if start_date is None:
        return previous_n_trade_days(cal, normalized_end, default_count)

    parsed_start = parse_yyyymmdd(start_date)
    normalized_start = previous_trade_day(cal, parsed_start)
    if normalized_start == normalized_end and parsed_start > normalized_end:
        end_idx = cal.index(normalized_end)
        if end_idx > 0:
            normalized_start = cal[end_idx - 1]
    if normalized_start > normalized_end:
        raise ValueError("start_date must be before or equal to end_date")
    return normalized_start, normalized_end
