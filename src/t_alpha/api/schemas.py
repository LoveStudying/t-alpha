from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from t_alpha.constants import DISCLAIMER


class DateRange(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class PriceRow(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None


class PriceResponse(BaseModel):
    code: str
    asset_type: Literal["stock", "etf", "fund"]
    period: Literal["day", "60m"]
    adjust: Literal["none", "forward"]
    requested_dates: DateRange
    normalized_dates: DateRange
    rows: List[PriceRow]
    disclaimer: str = Field(default=DISCLAIMER)


class FundNavRow(BaseModel):
    price_date: str
    unit_nav: Optional[float] = None
    accum_nav: Optional[float] = None
    adj_unit_nav: Optional[float] = None
    inner_code: str = ""
    outer_code: str = ""


class FundNavResponse(BaseModel):
    code: str
    requested_dates: DateRange
    normalized_dates: DateRange
    rows: List[FundNavRow]
    disclaimer: str = Field(default=DISCLAIMER)
