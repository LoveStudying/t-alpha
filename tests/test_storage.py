from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from t_alpha.constants import DEFAULT_TEST_CODE, DEFAULT_TEST_NAME
from t_alpha.storage.models import Base, Watchlist
from t_alpha.storage.repository import seed_default_watchlist


def test_seed_default_watchlist_is_idempotent():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        seed_default_watchlist(session)
        seed_default_watchlist(session)
        rows = session.query(Watchlist).all()

    assert len(rows) == 1
    assert rows[0].code == DEFAULT_TEST_CODE
    assert rows[0].name == DEFAULT_TEST_NAME


def test_watchlist_defaults_enabled():
    row = Watchlist(code="601318.SH", name="中国平安", strategy_name="mean_reversion_t0_v1")
    assert row.enabled is True
