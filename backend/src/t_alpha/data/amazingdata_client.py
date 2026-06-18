from __future__ import annotations

from typing import Any

from t_alpha.config import Settings


class AmazingDataClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._ad: Any | None = None
        self._base_data: Any | None = None
        self._market_data: Any | None = None
        self._info_data: Any | None = None
        self._calendar: list[int] | None = None

    def _module(self):
        if self._ad is None:
            import AmazingData as ad

            ad.login(
                username=self.settings.ad_username,
                password=self.settings.ad_password,
                host=self.settings.ad_host,
                port=self.settings.ad_port,
            )
            self._ad = ad
        return self._ad

    @property
    def ad(self):
        return self._module()

    @property
    def base_data(self):
        if self._base_data is None:
            self._base_data = self.ad.BaseData()
        return self._base_data

    @property
    def info_data(self):
        if self._info_data is None:
            self._info_data = self.ad.InfoData()
        return self._info_data

    def get_calendar(self) -> list[int]:
        if self._calendar is None:
            values = self.base_data.get_calendar()
            self._calendar = sorted(int(str(day)[:8]) for day in values)
        return self._calendar

    @property
    def market_data(self):
        if self._market_data is None:
            self._market_data = self.ad.MarketData(self.get_calendar())
        return self._market_data

    def get_code_list(self, security_type: str) -> list[str]:
        return list(self.base_data.get_code_list(security_type=security_type))

    def query_kline(self, code: str, begin_date: int, end_date: int, period_value: int):
        return self.market_data.query_kline([code], begin_date=begin_date, end_date=end_date, period=period_value)

    def get_backward_factor(self, code: str):
        return self.base_data.get_backward_factor([code], is_local=False)

    def get_fund_nav(self, code: str, begin_date: int | None = None, end_date: int | None = None):
        if begin_date is not None and end_date is not None:
            return self.info_data.get_fund_nav([code], begin_date=begin_date, end_date=end_date)
        return self.info_data.get_fund_nav([code], is_local=False)
