from fastapi import APIRouter

from t_alpha.constants import DEFAULT_TEST_CODE, DEFAULT_TEST_NAME
from t_alpha.storage.repository import DEFAULT_STRATEGY


router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


@router.get("/default-watchlist")
def default_watchlist():
    return {
        "code": DEFAULT_TEST_CODE,
        "name": DEFAULT_TEST_NAME,
        "strategy_name": DEFAULT_STRATEGY,
        "enabled": True,
    }
