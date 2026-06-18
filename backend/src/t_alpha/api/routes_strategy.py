from fastapi import APIRouter, Depends, HTTPException

from t_alpha.api.deps import get_strategy_service
from t_alpha.api.schemas import T0BuildRequest, T0BuildResponse, T0MonitorRequest, T0MonitorResponse
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


@router.post("/t0/build", response_model=T0BuildResponse)
def build_t0_strategy(request: T0BuildRequest, service=Depends(get_strategy_service)):
    return T0BuildResponse.model_validate(service.build_report(request.code.strip()))


@router.post("/t0/monitor", response_model=T0MonitorResponse)
def monitor_t0_strategy(request: T0MonitorRequest, service=Depends(get_strategy_service)):
    result = service.enable_monitor(request.code.strip(), request.enabled)
    if request.enabled and not result.get("enabled", False):
        raise HTTPException(status_code=400, detail=result.get("reason", "strategy is not eligible"))
    return T0MonitorResponse.model_validate(result)
