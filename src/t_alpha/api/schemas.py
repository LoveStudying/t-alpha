from __future__ import annotations

from datetime import datetime
from typing import Any, List, Literal, Optional

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
    ann_date: Optional[str] = None
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


class T0BuildRequest(BaseModel):
    code: str = Field(min_length=1)


class T0MonitorRequest(BaseModel):
    code: str = Field(min_length=1)
    enabled: bool = True


class T0BuildResponse(BaseModel):
    code: str
    strategy_name: str
    params: dict
    full_metrics: dict
    train_metrics: dict
    validation_metrics: dict
    recent_metrics: dict
    recent_trades: list[dict]
    eligibility: dict
    generated_at: str
    disclaimer: str = Field(default=DISCLAIMER)


class T0MonitorResponse(BaseModel):
    code: str
    enabled: bool
    strategy_name: str
    reason: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AdminUser(BaseModel):
    username: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AdminUser


class PagedResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
    limit: int
    offset: int


class AdminOverview(BaseModel):
    app_env: str
    app_host: str
    app_port: int
    watchlist_count: int
    enabled_watchlist_count: int
    report_count: int
    open_position_count: int
    recent_alert_count: int


class SettingsSummary(BaseModel):
    app_env: str
    app_host: str
    app_port: int
    log_level: str
    ad_username: str
    ad_host: str
    ad_port: int
    db_host: str
    db_port: int
    db_name: str
    smtp_host: str
    smtp_port: int
    smtp_configured: bool
    alert_to_configured: bool
    admin_username: str
    admin_configured: bool
    t0_params: dict[str, Any]


class WatchlistCreate(BaseModel):
    code: str = Field(min_length=1)
    name: str = ""
    enabled: bool = True
    strategy_name: str = "mean_reversion_t0_v1"
    note: str = ""


class WatchlistUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    enabled: Optional[bool] = None
    strategy_name: Optional[str] = None
    note: Optional[str] = None


class WatchlistOut(BaseModel):
    id: int
    code: str
    name: str
    enabled: bool
    strategy_name: str
    note: str
    created_at: datetime
    updated_at: datetime


class T0ReportOut(BaseModel):
    id: int
    code: str
    strategy_name: str
    params: dict[str, Any] | str
    report: dict[str, Any] | str
    eligible: bool
    eligibility_level: str
    generated_at: datetime
    updated_at: datetime
    parse_error: Optional[str] = None


class T0PositionOut(BaseModel):
    id: int
    code: str
    strategy_name: str
    status: str
    payload: dict[str, Any] | str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    parse_error: Optional[str] = None


class AlertRecordOut(BaseModel):
    id: int
    code: str
    signal_time: datetime
    signal_type: str
    payload: dict[str, Any] | str
    sent: bool
    error_message: str
    created_at: datetime
    parse_error: Optional[str] = None
