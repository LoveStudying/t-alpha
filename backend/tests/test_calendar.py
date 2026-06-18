import pytest

from t_alpha.data.calendar import normalize_date_range, previous_n_trade_days


CALENDAR = [20240102, 20240103, 20240104, 20240105, 20240108, 20240109, 20240110]


def test_previous_n_trade_days_uses_trade_calendar():
    assert previous_n_trade_days(CALENDAR, end_date=20240110, n=3) == (20240108, 20240110)


def test_normalize_empty_dates_defaults_to_recent_10_or_available():
    result = normalize_date_range(CALENDAR, None, None, default_count=10)
    assert result == (20240102, 20240110)


def test_normalize_non_trade_end_moves_backward():
    result = normalize_date_range(CALENDAR, "20240106", "20240107", default_count=3)
    assert result == (20240104, 20240105)


def test_invalid_date_format_raises():
    with pytest.raises(ValueError, match="YYYYMMDD"):
        normalize_date_range(CALENDAR, "2024-01-01", None)
