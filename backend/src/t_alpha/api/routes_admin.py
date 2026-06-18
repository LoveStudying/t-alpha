from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from t_alpha.api.auth import get_current_admin_user
from t_alpha.api.deps import get_db_session, get_settings
from t_alpha.api.schemas import (
    AdminOverview,
    AlertRecordOut,
    PagedResponse,
    SettingsSummary,
    T0PositionOut,
    T0ReportOut,
    WatchlistCreate,
    WatchlistOut,
    WatchlistUpdate,
)
from t_alpha.config import Settings
from t_alpha.storage.models import AlertRecord, T0Position, T0StrategyReportRow, Watchlist


router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(get_current_admin_user)])


def _count(session: Session, stmt) -> int:
    return int(session.execute(stmt).scalar_one())


def _paging(limit: int, offset: int) -> tuple[int, int]:
    return min(max(limit, 1), 200), max(offset, 0)


def _parse_json_field(raw: str) -> tuple[dict[str, Any] | str, str | None]:
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return raw, str(exc)


def _watchlist_out(row: Watchlist) -> WatchlistOut:
    return WatchlistOut(
        id=row.id,
        code=row.code,
        name=row.name,
        enabled=row.enabled,
        strategy_name=row.strategy_name,
        note=row.note,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _report_out(row: T0StrategyReportRow) -> T0ReportOut:
    params, params_error = _parse_json_field(row.params_json)
    report, report_error = _parse_json_field(row.report_json)
    parse_error = params_error or report_error
    return T0ReportOut(
        id=row.id,
        code=row.code,
        strategy_name=row.strategy_name,
        params=params,
        report=report,
        eligible=row.eligible,
        eligibility_level=row.eligibility_level,
        generated_at=row.generated_at,
        updated_at=row.updated_at,
        parse_error=parse_error,
    )


def _position_out(row: T0Position) -> T0PositionOut:
    payload, parse_error = _parse_json_field(row.payload_json)
    return T0PositionOut(
        id=row.id,
        code=row.code,
        strategy_name=row.strategy_name,
        status=row.status,
        payload=payload,
        opened_at=row.opened_at,
        closed_at=row.closed_at,
        parse_error=parse_error,
    )


def _alert_out(row: AlertRecord) -> AlertRecordOut:
    payload, parse_error = _parse_json_field(row.payload_json)
    return AlertRecordOut(
        id=row.id,
        code=row.code,
        signal_time=row.signal_time,
        signal_type=row.signal_type,
        payload=payload,
        sent=row.sent,
        error_message=row.error_message,
        created_at=row.created_at,
        parse_error=parse_error,
    )


@router.get("/overview", response_model=AdminOverview)
def overview(session: Session = Depends(get_db_session), settings: Settings = Depends(get_settings)):
    recent_cutoff = datetime.utcnow() - timedelta(days=7)
    return AdminOverview(
        app_env=settings.app_env,
        app_host=settings.app_host,
        app_port=settings.app_port,
        watchlist_count=_count(session, select(func.count()).select_from(Watchlist)),
        enabled_watchlist_count=_count(session, select(func.count()).select_from(Watchlist).where(Watchlist.enabled.is_(True))),
        report_count=_count(session, select(func.count()).select_from(T0StrategyReportRow)),
        open_position_count=_count(session, select(func.count()).select_from(T0Position).where(T0Position.status == "open")),
        recent_alert_count=_count(session, select(func.count()).select_from(AlertRecord).where(AlertRecord.created_at >= recent_cutoff)),
    )


@router.get("/settings/summary", response_model=SettingsSummary)
def settings_summary(settings: Settings = Depends(get_settings)):
    return SettingsSummary(
        app_env=settings.app_env,
        app_host=settings.app_host,
        app_port=settings.app_port,
        log_level=settings.log_level,
        ad_username=settings.ad_username,
        ad_host=settings.ad_host,
        ad_port=settings.ad_port,
        db_host=settings.db_host,
        db_port=settings.db_port,
        db_name=settings.db_name,
        smtp_host=settings.smtp_host,
        smtp_port=settings.smtp_port,
        smtp_configured=bool(settings.smtp_username and settings.smtp_password),
        alert_to_configured=bool(settings.alert_to),
        admin_username=settings.admin_username,
        admin_configured=bool(settings.admin_username and settings.admin_password and settings.admin_token_secret),
        t0_params={
            "target_return": settings.t0_target_return,
            "max_holding_trade_days": settings.t0_max_holding_trade_days,
            "trade_cost_rate": settings.t0_trade_cost_rate,
            "min_3y_trades": settings.t0_min_3y_trades,
            "observe_min_3y_trades": settings.t0_observe_min_3y_trades,
            "min_success_rate": settings.t0_min_success_rate,
            "min_trade_amount": settings.min_trade_amount,
            "max_trade_amount": settings.max_trade_amount,
        },
    )


@router.get("/watchlist", response_model=PagedResponse)
def list_watchlist(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
):
    limit, offset = _paging(limit, offset)
    total = _count(session, select(func.count()).select_from(Watchlist))
    stmt = select(Watchlist).order_by(Watchlist.updated_at.desc(), Watchlist.id.desc()).limit(limit).offset(offset)
    rows = [_watchlist_out(row).model_dump(mode="json") for row in session.execute(stmt).scalars()]
    return PagedResponse(items=rows, total=total, limit=limit, offset=offset)


@router.post("/watchlist", response_model=WatchlistOut)
def create_watchlist(request: WatchlistCreate, session: Session = Depends(get_db_session)):
    row = Watchlist(
        code=request.code.strip(),
        name=request.name.strip(),
        enabled=request.enabled,
        strategy_name=request.strategy_name.strip(),
        note=request.note.strip(),
    )
    session.add(row)
    session.flush()
    return _watchlist_out(row)


@router.patch("/watchlist/{row_id}", response_model=WatchlistOut)
def update_watchlist(row_id: int, request: WatchlistUpdate, session: Session = Depends(get_db_session)):
    row = session.get(Watchlist, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="watchlist row not found")

    updates = request.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(row, key, value)
    session.flush()
    return _watchlist_out(row)


@router.delete("/watchlist/{row_id}")
def delete_watchlist(row_id: int, session: Session = Depends(get_db_session)):
    result = session.execute(delete(Watchlist).where(Watchlist.id == row_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="watchlist row not found")
    return {"deleted": True, "id": row_id}


@router.get("/t0/reports", response_model=PagedResponse)
def list_t0_reports(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
):
    limit, offset = _paging(limit, offset)
    total = _count(session, select(func.count()).select_from(T0StrategyReportRow))
    stmt = select(T0StrategyReportRow).order_by(T0StrategyReportRow.updated_at.desc(), T0StrategyReportRow.id.desc()).limit(limit).offset(offset)
    rows = [_report_out(row).model_dump(mode="json") for row in session.execute(stmt).scalars()]
    return PagedResponse(items=rows, total=total, limit=limit, offset=offset)


@router.get("/t0/reports/{row_id}", response_model=T0ReportOut)
def get_t0_report(row_id: int, session: Session = Depends(get_db_session)):
    row = session.get(T0StrategyReportRow, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="report not found")
    return _report_out(row)


@router.get("/t0/positions", response_model=PagedResponse)
def list_t0_positions(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
):
    limit, offset = _paging(limit, offset)
    total = _count(session, select(func.count()).select_from(T0Position))
    stmt = select(T0Position).order_by(T0Position.opened_at.desc(), T0Position.id.desc()).limit(limit).offset(offset)
    rows = [_position_out(row).model_dump(mode="json") for row in session.execute(stmt).scalars()]
    return PagedResponse(items=rows, total=total, limit=limit, offset=offset)


@router.get("/t0/positions/{row_id}", response_model=T0PositionOut)
def get_t0_position(row_id: int, session: Session = Depends(get_db_session)):
    row = session.get(T0Position, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="position not found")
    return _position_out(row)


@router.get("/alerts", response_model=PagedResponse)
def list_alerts(
    limit: int = Query(default=50, ge=1),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_db_session),
):
    limit, offset = _paging(limit, offset)
    total = _count(session, select(func.count()).select_from(AlertRecord))
    stmt = select(AlertRecord).order_by(AlertRecord.created_at.desc(), AlertRecord.id.desc()).limit(limit).offset(offset)
    rows = [_alert_out(row).model_dump(mode="json") for row in session.execute(stmt).scalars()]
    return PagedResponse(items=rows, total=total, limit=limit, offset=offset)


@router.get("/alerts/{row_id}", response_model=AlertRecordOut)
def get_alert(row_id: int, session: Session = Depends(get_db_session)):
    row = session.get(AlertRecord, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return _alert_out(row)
