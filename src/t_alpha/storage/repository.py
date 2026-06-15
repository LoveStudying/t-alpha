from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from t_alpha.constants import DEFAULT_T0_STRATEGY, DEFAULT_TEST_CODE, DEFAULT_TEST_NAME
from t_alpha.storage.models import T0Position, T0StrategyReportRow, Watchlist


DEFAULT_STRATEGY = DEFAULT_T0_STRATEGY


def seed_default_watchlist(session: Session) -> Watchlist:
    stmt = select(Watchlist).where(
        Watchlist.code == DEFAULT_TEST_CODE,
        Watchlist.strategy_name == DEFAULT_STRATEGY,
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing is not None:
        return existing

    row = Watchlist(
        code=DEFAULT_TEST_CODE,
        name=DEFAULT_TEST_NAME,
        enabled=True,
        strategy_name=DEFAULT_STRATEGY,
        note="用户指定的首个测试与监控股票",
    )
    session.add(row)
    session.flush()
    return row


def list_enabled_watchlist(session: Session) -> list[Watchlist]:
    stmt = select(Watchlist).where(Watchlist.enabled.is_(True)).order_by(Watchlist.code)
    return list(session.execute(stmt).scalars())


def save_t0_report(
    session: Session,
    code: str,
    strategy_name: str,
    params_json: str,
    report_json: str,
    eligible: bool,
    eligibility_level: str,
) -> T0StrategyReportRow:
    stmt = select(T0StrategyReportRow).where(
        T0StrategyReportRow.code == code,
        T0StrategyReportRow.strategy_name == strategy_name,
    )
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        row = T0StrategyReportRow(code=code, strategy_name=strategy_name)
        session.add(row)
    row.params_json = params_json
    row.report_json = report_json
    row.eligible = eligible
    row.eligibility_level = eligibility_level
    row.generated_at = datetime.utcnow()
    session.flush()
    return row


def get_latest_t0_report(session: Session, code: str, strategy_name: str = DEFAULT_STRATEGY) -> T0StrategyReportRow | None:
    stmt = select(T0StrategyReportRow).where(
        T0StrategyReportRow.code == code,
        T0StrategyReportRow.strategy_name == strategy_name,
    )
    return session.execute(stmt).scalar_one_or_none()


def set_t0_monitor_enabled(session: Session, code: str, enabled: bool, strategy_name: str = DEFAULT_STRATEGY) -> Watchlist:
    stmt = select(Watchlist).where(Watchlist.code == code, Watchlist.strategy_name == strategy_name)
    row = session.execute(stmt).scalar_one_or_none()
    if row is None:
        row = Watchlist(code=code, name="", strategy_name=strategy_name, enabled=enabled, note="t0 monitor")
        session.add(row)
    row.enabled = enabled
    session.flush()
    return row


def open_t0_position(session: Session, code: str, strategy_name: str, payload_json: str) -> T0Position:
    row = T0Position(code=code, strategy_name=strategy_name, status="open", payload_json=payload_json)
    session.add(row)
    session.flush()
    return row


def get_open_t0_position(session: Session, code: str, strategy_name: str = DEFAULT_STRATEGY) -> T0Position | None:
    stmt = (
        select(T0Position)
        .where(T0Position.code == code, T0Position.strategy_name == strategy_name, T0Position.status == "open")
        .order_by(T0Position.opened_at.desc())
    )
    return session.execute(stmt).scalars().first()


def close_t0_position(session: Session, position: T0Position, payload_json: str) -> T0Position:
    position.status = "closed"
    position.payload_json = payload_json
    position.closed_at = datetime.utcnow()
    session.flush()
    return position
