from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from t_alpha.constants import DEFAULT_TEST_CODE, DEFAULT_TEST_NAME
from t_alpha.storage.models import Base, Watchlist
from t_alpha.storage.repository import close_t0_position, open_t0_position, save_t0_report, seed_default_watchlist


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


def test_save_t0_report_upserts_latest_report():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        first = save_t0_report(
            session,
            code="601318.SH",
            strategy_name="mean_reversion_t0_v1",
            params_json='{"target_return": 0.03}',
            report_json='{"eligibility": {"eligible": true}}',
            eligible=True,
            eligibility_level="eligible",
        )
        second = save_t0_report(
            session,
            code="601318.SH",
            strategy_name="mean_reversion_t0_v1",
            params_json='{"target_return": 0.03}',
            report_json='{"eligibility": {"eligible": false}}',
            eligible=False,
            eligibility_level="observe",
        )

        assert first.id == second.id
        assert second.eligible is False


def test_close_t0_position_marks_position_closed():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        row = open_t0_position(
            session,
            code="601318.SH",
            strategy_name="mean_reversion_t0_v1",
            payload_json='{"buy_price": 40.0, "target_sell_price": 41.2}',
        )

        close_t0_position(session, row, payload_json='{"sell_price": 41.2, "exit_reason": "target"}')

        assert row.status == "closed"
        assert row.closed_at is not None
        assert '"exit_reason": "target"' in row.payload_json
