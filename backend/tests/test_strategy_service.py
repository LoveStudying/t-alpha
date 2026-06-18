from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from t_alpha.services_strategy import T0StrategyService
from t_alpha.storage.models import Base
from t_alpha.storage.repository import get_latest_t0_report


class FakeClient:
    def get_calendar(self):
        return [20240102, 20240103, 20240104, 20240105, 20240108, 20240109]

    def query_kline(self, code, begin_date, end_date, period):
        if period == "day":
            closes = [40.0 + idx * 0.02 for idx in range(80)]
            return {
                code: pd.DataFrame(
                    {
                        "kline_time": pd.date_range("2023-10-01", periods=80, freq="B"),
                        "open": closes,
                        "high": [price + 0.3 for price in closes],
                        "low": [price - 0.3 for price in closes],
                        "close": closes,
                        "volume": [500000.0] * 80,
                        "amount": [20000000.0] * 80,
                    }
                )
            }
        closes = [40.0] * 25 + [39.0, 38.8, 38.9, 39.1, 39.3, 40.0, 41.0, 41.5]
        return {
            code: pd.DataFrame(
                {
                    "kline_time": pd.date_range("2024-01-02 10:00:00", periods=len(closes), freq="60min"),
                    "open": closes,
                    "high": [price + 0.4 for price in closes],
                    "low": [price - 0.2 for price in closes],
                    "close": closes,
                    "volume": [1000.0] * len(closes),
                    "amount": [100000.0] * len(closes),
                }
            )
        }


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    return Session()


def test_build_report_persists_latest_report():
    session = _session()
    service = T0StrategyService(FakeClient(), session=session)

    report = service.build_report("601318.SH")
    persisted = get_latest_t0_report(session, "601318.SH")

    assert report["code"] == "601318.SH"
    assert "full_metrics" in report
    assert persisted is not None


def test_enable_monitor_rejects_missing_or_ineligible_report():
    session = _session()
    service = T0StrategyService(FakeClient(), session=session)

    result = service.enable_monitor("601318.SH", True)

    assert result["enabled"] is False
    assert result["reason"]


def test_generate_sell_signal_when_target_price_reached():
    service = T0StrategyService(FakeClient(), session=object())
    position_payload = {
        "code": "601318.SH",
        "signal_time": "2024-01-02 10:00:00",
        "buy_alert_time": "2024-01-02 10:05:00",
        "reference_buy_price": 40.0,
        "suggested_shares": 300,
        "suggested_amount": 12000,
        "target_sell_price": 41.2,
        "max_holding_trade_days": 10,
        "opened_trade_date": "2024-01-02",
        "reasons": ["BOLL lower band touch"],
    }

    payload = service.generate_sell_signal(position_payload, current_price=41.25, holding_trade_days=2, now=datetime(2024, 1, 4, 10))

    assert payload is not None
    assert payload["exit_reason"] == "target"
    assert payload["sell_alert_type"] == "target"


def test_generate_sell_signal_when_timeout_reached():
    service = T0StrategyService(FakeClient(), session=object())
    position_payload = {
        "code": "601318.SH",
        "signal_time": "2024-01-02 10:00:00",
        "buy_alert_time": "2024-01-02 10:05:00",
        "reference_buy_price": 40.0,
        "suggested_shares": 300,
        "suggested_amount": 12000,
        "target_sell_price": 41.2,
        "max_holding_trade_days": 10,
        "opened_trade_date": "2024-01-02",
        "reasons": ["BOLL lower band touch"],
    }

    payload = service.generate_sell_signal(position_payload, current_price=39.5, holding_trade_days=10, now=datetime(2024, 1, 16, 14, 55))

    assert payload is not None
    assert payload["exit_reason"] == "timeout"
    assert payload["sell_alert_type"] == "timeout"
