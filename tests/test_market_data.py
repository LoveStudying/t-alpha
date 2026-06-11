import pandas as pd

from t_alpha.data.adjust import forward_adjust
from t_alpha.data.market_data import fund_nav_dict_to_rows, kline_dict_to_rows


def test_forward_adjust_changes_ohlc_only(sample_kline_df):
    factor = pd.DataFrame(
        {"601318.SH": [1.0, 2.0, 2.0]},
        index=pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
    )

    adjusted = forward_adjust(sample_kline_df, factor, "601318.SH")

    assert adjusted["open"].round(2).tolist() == [5.0, 10.2, 10.1]
    assert adjusted["volume"].tolist() == [1000, 1200, 1500]


def test_kline_dict_to_rows_serializes_dates(sample_kline_df):
    rows = kline_dict_to_rows({"601318.SH": sample_kline_df}, "601318.SH")

    assert rows[0]["date"] == "20240102"
    assert rows[0]["close"] == 10.2


def test_fund_nav_dict_to_rows_serializes_nav_fields():
    nav_df = pd.DataFrame(
        {
            "PRICE_DATE": ["20240102"],
            "UNIT_NAV": [1.2345],
            "ACCUM_NAV": [2.3456],
            "ADJ_UNIT_NAV": [1.4567],
            "INNER_CODE": [""],
            "OUTER_CODE": ["000001"],
        }
    )

    rows = fund_nav_dict_to_rows({"000001.OF": nav_df}, "000001.OF")

    assert rows == [
        {
            "price_date": "20240102",
            "unit_nav": 1.2345,
            "accum_nav": 2.3456,
            "adj_unit_nav": 1.4567,
            "inner_code": "",
            "outer_code": "000001",
        }
    ]
