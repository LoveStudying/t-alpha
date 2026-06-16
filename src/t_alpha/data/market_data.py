from __future__ import annotations

from typing import Any

import pandas as pd


def period_to_ad_value(ad_module: Any, period: str) -> int:
    if period == "day":
        return ad_module.constant.Period.day.value
    if period == "60m":
        return ad_module.constant.Period.min60.value
    raise ValueError(f"unsupported period: {period}")


def kline_dict_to_rows(kline_dict: dict[str, pd.DataFrame], code: str) -> list[dict]:
    df = kline_dict.get(code)
    if df is None or df.empty:
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(row["kline_time"])
        rows.append(
            {
                "date": dt.strftime("%Y%m%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "amount": float(row["amount"]) if "amount" in row and pd.notna(row["amount"]) else None,
            }
        )
    return rows


def fund_nav_dict_to_rows(nav_dict: dict[str, pd.DataFrame], code: str) -> list[dict]:
    df = nav_dict.get(code)
    if df is None or df.empty:
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "price_date": str(row.get("PRICE_DATE", ""))[:8],
                "ann_date": str(row.get("ANN_DATE", ""))[:8] if pd.notna(row.get("ANN_DATE")) else None,
                "unit_nav": float(row["UNIT_NAV"]) if pd.notna(row.get("UNIT_NAV")) else None,
                "accum_nav": float(row["ACCUM_NAV"]) if pd.notna(row.get("ACCUM_NAV")) else None,
                "adj_unit_nav": float(row["ADJ_UNIT_NAV"]) if pd.notna(row.get("ADJ_UNIT_NAV")) else None,
                "inner_code": str(row.get("INNER_CODE", "") or ""),
                "outer_code": str(row.get("OUTER_CODE", "") or ""),
            }
        )
    return rows
