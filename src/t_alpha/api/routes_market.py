from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Depends

from t_alpha.api.deps import get_market_service
from t_alpha.api.schemas import FundNavResponse, PriceResponse
from t_alpha.constants import ASSET_ETF, ASSET_FUND, ASSET_STOCK
from t_alpha.services_market import MarketService


router = APIRouter(prefix="/api/v1/market", tags=["market"])


def _prices(
    asset_type: str,
    code: str,
    start_date: Optional[str],
    end_date: Optional[str],
    period: Literal["day", "60m"],
    adjust: Literal["none", "forward"],
    service: MarketService,
) -> PriceResponse:
    return PriceResponse.model_validate(service.get_prices(asset_type, code, start_date, end_date, period, adjust))


@router.get("/stock/prices", response_model=PriceResponse)
def stock_prices(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_STOCK, code, start_date, end_date, period, adjust, service)


@router.get("/etf/prices", response_model=PriceResponse)
def etf_prices(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_ETF, code, start_date, end_date, period, adjust, service)


@router.get("/fund/prices", response_model=PriceResponse)
def fund_prices(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service: MarketService = Depends(get_market_service),
):
    return _prices(ASSET_FUND, code, start_date, end_date, period, adjust, service)


@router.get("/fund/nav", response_model=FundNavResponse)
def fund_nav(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    service: MarketService = Depends(get_market_service),
):
    return FundNavResponse.model_validate(service.get_fund_nav(code, start_date, end_date))
