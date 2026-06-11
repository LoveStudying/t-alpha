from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from t_alpha.constants import DEFAULT_TEST_CODE, DEFAULT_TEST_NAME
from t_alpha.storage.models import Watchlist


DEFAULT_STRATEGY = "mean_reversion_t0_v1"


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
