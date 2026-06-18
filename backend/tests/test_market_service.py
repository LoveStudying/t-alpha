import pandas as pd

from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient
from t_alpha.services_market import MarketService


class FakeNavClient:
    def __init__(self):
        self.calls = []

    def get_calendar(self):
        return [20240102, 20240103, 20240104]

    def get_fund_nav(self, code, begin_date, end_date):
        self.calls.append((code, begin_date, end_date))
        return {
            code: pd.DataFrame(
                {
                    "PRICE_DATE": ["20240104"],
                    "UNIT_NAV": [1.0],
                    "ACCUM_NAV": [1.1],
                    "ADJ_UNIT_NAV": [1.2],
                    "INNER_CODE": [""],
                    "OUTER_CODE": [code],
                }
            )
        }


class FakeInfoData:
    def __init__(self):
        self.calls = []

    def get_fund_nav(self, code_list, **kwargs):
        self.calls.append((code_list, kwargs))
        return {}


class FakePriceClient:
    ad = type(
        "Ad",
        (),
        {
            "constant": type(
                "Constant",
                (),
                {
                    "Period": type(
                        "Period",
                        (),
                        {
                            "day": type("PeriodValue", (), {"value": 1})(),
                            "min60": type("PeriodValue", (), {"value": 60})(),
                        },
                    )
                },
            )()
        },
    )()

    def __init__(self):
        self.calls = []

    def get_calendar(self):
        return [
            20240102,
            20240103,
            20240104,
            20240105,
            20240108,
            20240109,
            20240110,
            20240111,
            20240112,
            20240115,
            20240116,
        ]

    def query_kline(self, code, begin_date, end_date, period_value):
        self.calls.append((code, begin_date, end_date, period_value))
        return {
            code: pd.DataFrame(
                {
                    "kline_time": ["2024-01-08"],
                    "open": [1.0],
                    "high": [1.1],
                    "low": [0.9],
                    "close": [1.0],
                    "volume": [100.0],
                    "amount": [100.0],
                }
            )
        }


def test_market_service_uses_recent_ten_trade_days_when_price_dates_are_missing():
    client = FakePriceClient()
    service = MarketService(client)

    payload = service.get_prices("stock", "601318.SH", None, None, "day", "none")

    assert client.calls == [("601318.SH", 20240103, 20240116, 1)]
    assert payload["normalized_dates"] == {"start_date": "20240103", "end_date": "20240116"}


def test_market_service_passes_normalized_dates_to_fund_nav_client():
    client = FakeNavClient()
    service = MarketService(client)

    payload = service.get_fund_nav("000001.OF", "20240103", "20240105")

    assert client.calls == [("000001.OF", 20240103, 20240104)]
    assert payload["normalized_dates"] == {"start_date": "20240103", "end_date": "20240104"}
    assert payload["rows"][0]["price_date"] == "20240104"


def test_amazingdata_client_passes_fund_nav_date_range_to_sdk():
    info_data = FakeInfoData()
    client = AmazingDataClient(Settings())
    client._info_data = info_data

    client.get_fund_nav("000001.OF", 20240102, 20240104)

    assert info_data.calls == [
        (["000001.OF"], {"begin_date": 20240102, "end_date": 20240104})
    ]
