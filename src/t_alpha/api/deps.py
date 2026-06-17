from collections.abc import Generator
from functools import lru_cache

from sqlalchemy.orm import Session

from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient
from t_alpha.services_market import MarketService
from t_alpha.services_strategy import T0StrategyService
from t_alpha.storage.database import build_session_factory, create_mysql_engine


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_amazingdata_client() -> AmazingDataClient:
    return AmazingDataClient(get_settings())


@lru_cache
def get_session_factory():
    engine = create_mysql_engine(get_settings())
    return build_session_factory(engine)


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_market_service() -> MarketService:
    return MarketService(get_amazingdata_client())


def get_strategy_service() -> T0StrategyService:
    return T0StrategyService(get_amazingdata_client(), settings=get_settings())
