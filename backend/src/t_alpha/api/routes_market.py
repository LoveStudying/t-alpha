from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from t_alpha.api.deps import get_market_service
from t_alpha.api.schemas import FundNavResponse, PriceResponse
from t_alpha.constants import ASSET_ETF, ASSET_FUND, ASSET_STOCK, SUPPORTED_ADJUST, SUPPORTED_PERIODS
from t_alpha.services_market import MarketService


router = APIRouter(prefix="/api/v1/market", tags=["market"])


def _prices(
    asset_type: str,
    code: str,
    start_date: Optional[str],
    end_date: Optional[str],
    period: str,
    adjust: str,
    service: MarketService,
) -> PriceResponse:
    return PriceResponse.model_validate(
        service.get_prices(
            asset_type,
            _required_query_value(code, "code"),
            _optional_query_value(start_date),
            _optional_query_value(end_date),
            _choice_query_value(period, "day", SUPPORTED_PERIODS, "period"),
            _choice_query_value(adjust, "none", SUPPORTED_ADJUST, "adjust"),
        )
    )


def _optional_query_value(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _default_query_value(value: Optional[str], default: str) -> str:
    stripped = _optional_query_value(value)
    return stripped or default


def _choice_query_value(value: Optional[str], default: str, supported: set[str], name: str) -> str:
    resolved = _default_query_value(value, default)
    if resolved not in supported:
        raise HTTPException(status_code=422, detail=f"unsupported {name}")
    return resolved


def _required_query_value(value: str, name: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise HTTPException(status_code=422, detail=f"{name} is required")
    return stripped


@router.get("/stock/prices", response_model=PriceResponse)
def stock_prices(
    code: str = Query(..., min_length=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "day",
    adjust: Optional[str] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_STOCK, code, start_date, end_date, period, adjust, service)


@router.get("/etf/prices", response_model=PriceResponse)
def etf_prices(
    code: str = Query(..., min_length=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "day",
    adjust: Optional[str] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_ETF, code, start_date, end_date, period, adjust, service)


@router.get("/fund/prices", response_model=PriceResponse)
def fund_prices(
    code: str = Query(..., min_length=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Optional[str] = "day",
    adjust: Optional[str] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_FUND, code, start_date, end_date, period, adjust, service)


@router.get("/fund/nav", response_model=FundNavResponse)
def fund_nav(
    code: str = Query(..., min_length=1),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: MarketService = Depends(get_market_service),
):
    return FundNavResponse.model_validate(
        service.get_fund_nav(
            _required_query_value(code, "code"),
            _optional_query_value(start_date),
            _optional_query_value(end_date),
        )
    )
