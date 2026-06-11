from functools import lru_cache

from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient
from t_alpha.services_market import MarketService


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_amazingdata_client() -> AmazingDataClient:
    return AmazingDataClient(get_settings())


def get_market_service() -> MarketService:
    return MarketService(get_amazingdata_client())
