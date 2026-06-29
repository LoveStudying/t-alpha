from __future__ import annotations

from fastapi import HTTPException

from t_alpha.constants import ASSET_FUND, ASSET_STOCK, DISCLAIMER, SUPPORTED_ADJUST, SUPPORTED_PERIODS
from t_alpha.data.adjust import forward_adjust
from t_alpha.data.calendar import normalize_date_range, parse_yyyymmdd
from t_alpha.data.market_data import fund_nav_dict_to_rows, kline_dict_to_rows, period_to_ad_value


class MarketService:
    def __init__(self, client):
        self.client = client

    def _normalize_dates(self, start_date: str | None, end_date: str | None) -> tuple[int, int]:
        try:
            return normalize_date_range(
                self.client.get_calendar(),
                self._optional_text(start_date),
                self._optional_text(end_date),
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def _resolve_fund_nav_dates(self, start_date: str | None, end_date: str | None) -> tuple[int, int]:
        if start_date is not None and end_date is not None:
            try:
                begin_date = parse_yyyymmdd(start_date)
                finish_date = parse_yyyymmdd(end_date)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            if begin_date > finish_date:
                raise HTTPException(status_code=400, detail="start_date must be before or equal to end_date")
            return begin_date, finish_date
        return self._normalize_dates(start_date, end_date)

    @staticmethod
    def _optional_text(value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    @classmethod
    def _default_text(cls, value: str | None, default: str) -> str:
        return cls._optional_text(value) or default

    @classmethod
    def _required_text(cls, value: str) -> str:
        stripped = cls._optional_text(value)
        if stripped is None:
            raise HTTPException(status_code=422, detail="code is required")
        return stripped

    def get_prices(
        self,
        asset_type: str,
        code: str,
        start_date: str | None,
        end_date: str | None,
        period: str,
        adjust: str,
    ) -> dict:
        code = self._required_text(code)
        start_date = self._optional_text(start_date)
        end_date = self._optional_text(end_date)
        period = self._default_text(period, "day")
        adjust = self._default_text(adjust, "none")

        if period not in SUPPORTED_PERIODS:
            raise HTTPException(status_code=422, detail="unsupported period")
        if adjust not in SUPPORTED_ADJUST:
            raise HTTPException(status_code=422, detail="unsupported adjust")

        begin_date, finish_date = self._normalize_dates(start_date, end_date)
        period_value = period_to_ad_value(self.client.ad, period)
        kline_dict = self.client.query_kline(code, begin_date, finish_date, period_value)

        # 对外接口默认原始价；只有 A 股显式 forward 时做前复权。
        if adjust == "forward" and asset_type == ASSET_STOCK:
            df = kline_dict.get(code)
            if df is not None:
                kline_dict[code] = forward_adjust(df, self.client.get_backward_factor(code), code)

        rows = kline_dict_to_rows(kline_dict, code)
        if not rows:
            raise HTTPException(status_code=404, detail="no market data returned")

        return {
            "code": code,
            "asset_type": asset_type,
            "period": period,
            "adjust": adjust,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "normalized_dates": {"start_date": str(begin_date), "end_date": str(finish_date)},
            "rows": rows,
            "disclaimer": DISCLAIMER,
        }

    def get_fund_nav(self, code: str, start_date: str | None, end_date: str | None) -> dict:
        code = self._required_text(code)
        start_date = self._optional_text(start_date)
        end_date = self._optional_text(end_date)

        begin_date, finish_date = self._resolve_fund_nav_dates(start_date, end_date)
        nav_dict = self.client.get_fund_nav(code, begin_date, finish_date)
        rows = fund_nav_dict_to_rows(nav_dict, code)
        if not rows:
            raise HTTPException(status_code=404, detail="no fund nav returned")

        return {
            "code": code,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "normalized_dates": {"start_date": str(begin_date), "end_date": str(finish_date)},
            "rows": rows,
            "disclaimer": DISCLAIMER,
        }
