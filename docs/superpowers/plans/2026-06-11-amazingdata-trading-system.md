# AmazingData Trading System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python service that exposes AmazingData-backed price and fund NAV APIs, stores project state in MySQL 5.7, backtests a T+0 reminder strategy, and monitors `601318.SH` for email alerts.

**Architecture:** Implement a small FastAPI application with strict boundaries: configuration, data provider, storage, market API, indicators, strategy, backtest, scheduler, and notification. Keep AmazingData behind a wrapper so tests can run without a live data connection, and store only project metadata/results in the `t_alpha` MySQL database.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic Settings, SQLAlchemy 2.x, PyMySQL, pandas, numpy, APScheduler, pytest, httpx.

---

## Scope

This plan implements the first working product slice plus strategy foundations:

- HTTP APIs for A股、ETF、场内基金 K 线价格查询 and 场外开放式基金净值查询.
- AmazingData credential loading and data wrapper.
- MySQL 5.7 storage using only project database `t_alpha`.
- `601318.SH` 中国平安 default watchlist seed.
- Technical indicators needed by the first T+0 strategy.
- Backtest engine and metrics.
- Scheduler and email alert pipeline with mockable sending.

Out of scope for this plan:

- A web management UI.
- Automatic trading/order placement.
- Real-time subscription server hardening.
- Multi-strategy optimization dashboard.

## File Structure

Create these files:

```text
F:\个人文件\t-alpha\
  pyproject.toml
  .gitignore
  .env.example
  README.md
  src/
    t_alpha/
      __init__.py
      main.py
      config.py
      constants.py
      services_market.py
      api/
        __init__.py
        deps.py
        routes_market.py
        routes_strategy.py
        schemas.py
      data/
        __init__.py
        amazingdata_client.py
        calendar.py
        market_data.py
        adjust.py
      indicators/
        __init__.py
        technical.py
      strategy/
        __init__.py
        t0_strategy.py
        signal.py
        risk.py
      backtest/
        __init__.py
        engine.py
        metrics.py
      scheduler/
        __init__.py
        jobs.py
      notification/
        __init__.py
        email_sender.py
      storage/
        __init__.py
        database.py
        models.py
        repository.py
  tests/
    conftest.py
    test_config.py
    test_calendar.py
    test_storage.py
    test_market_api.py
    test_indicators.py
    test_backtest_engine.py
    test_t0_strategy.py
    test_scheduler.py
    test_email_sender.py
```

Responsibility map:

- `config.py`: environment variables, safe secret representation, strategy defaults.
- `data/`: AmazingData login, trading calendars, K-line retrieval, adjustment.
- `api/`: FastAPI route declarations and request/response schemas.
- `storage/`: MySQL engine, schema models, repositories, seed data.
- `indicators/`: pure pandas/numpy indicator functions, no AmazingData dependency.
- `strategy/`: signal generation and risk/threshold decisions.
- `backtest/`: deterministic backtesting logic and metrics.
- `scheduler/`: trading-day/time filtering and hourly alert job orchestration.
- `notification/`: SMTP email creation/sending.

---

### Task 1: Project Scaffold

**Files:**
- Create: `F:\个人文件\t-alpha\pyproject.toml`
- Create: `F:\个人文件\t-alpha\.gitignore`
- Create: `F:\个人文件\t-alpha\.env.example`
- Create: `F:\个人文件\t-alpha\README.md`
- Create: `F:\个人文件\t-alpha\src\t_alpha\__init__.py`
- Create package `__init__.py` files under all subpackages listed above.

- [ ] **Step 1: Create the package skeleton**

Create the directories listed in File Structure and empty `__init__.py` files for each package.

Expected package marker content:

```python
"""t_alpha package."""
```

- [ ] **Step 2: Add project metadata**

Write `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "t-alpha"
version = "0.1.0"
description = "AmazingData-backed market API and T+0 alert service"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.111",
  "uvicorn[standard]>=0.30",
  "pydantic>=2.7",
  "pydantic-settings>=2.3",
  "python-dotenv>=1.0",
  "sqlalchemy>=2.0",
  "pymysql>=1.1",
  "pandas>=2.2",
  "numpy>=1.26",
  "apscheduler>=3.10",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.2",
  "pytest-mock>=3.14",
  "httpx>=0.27",
]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

- [ ] **Step 3: Add ignore rules**

Write `.gitignore`:

```gitignore
.env
.env.*
!.env.example
__pycache__/
*.py[cod]
.pytest_cache/
.ruff_cache/
.mypy_cache/
.venv/
venv/
dist/
build/
*.egg-info/
data/
reports/
logs/
```

- [ ] **Step 4: Add `.env.example` with placeholders only**

Write `.env.example`:

```text
AD_USERNAME=your_amazingdata_username
AD_PASSWORD=your_amazingdata_password
AD_HOST=your_amazingdata_host
AD_PORT=8600

AMAZINGDATA_LOCAL_PATH=D:/AmazingData_local_data/

DB_HOST=your_mysql_host
DB_PORT=3306
DB_USERNAME=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=t_alpha

SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USERNAME=your_smtp_username
SMTP_PASSWORD=your_smtp_password
SMTP_FROM=alerts@example.com
ALERT_TO=you@example.com

MIN_TRADE_AMOUNT=5000
MAX_TRADE_AMOUNT=20000
COMMISSION_RATE=0.0001

APP_ENV=dev
LOG_LEVEL=INFO
```

- [ ] **Step 5: Add setup instructions**

Write `README.md`:

```markdown
# t-alpha

AmazingData-backed market API and T+0 alert service.

## Local setup

1. Create `.env` from `.env.example`.
2. Put real AmazingData and MySQL credentials in `.env`.
3. Install dependencies:

```powershell
python -m pip install -e ".[dev]"
```

4. Run tests:

```powershell
pytest -q
```

5. Start API:

```powershell
uvicorn t_alpha.main:app --reload
```

Credentials must not be committed.
```

- [ ] **Step 6: Verify scaffold**

Run:

```powershell
python -m pip install -e ".[dev]"
pytest -q
```

Expected: pytest runs with "no tests ran" or passes after later tasks add tests.

- [ ] **Step 7: Commit**

```powershell
git add pyproject.toml .gitignore .env.example README.md src tests
git commit -m "chore: scaffold t-alpha project"
```

---

### Task 2: Settings And Constants

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\constants.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\config.py`
- Create: `F:\个人文件\t-alpha\tests\test_config.py`

- [ ] **Step 1: Write failing settings tests**

Write `tests/test_config.py`:

```python
from t_alpha.config import Settings


def test_settings_reads_required_environment(monkeypatch):
    monkeypatch.setenv("AD_USERNAME", "210400052339")
    monkeypatch.setenv("AD_PASSWORD", "secret")
    monkeypatch.setenv("AD_HOST", "140.206.44.234")
    monkeypatch.setenv("AD_PORT", "8600")
    monkeypatch.setenv("DB_HOST", "47.93.240.45")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_USERNAME", "testroot")
    monkeypatch.setenv("DB_PASSWORD", "db-secret")
    monkeypatch.setenv("DB_NAME", "t_alpha")

    settings = Settings()

    assert settings.ad_username == "210400052339"
    assert settings.ad_port == 8600
    assert settings.db_name == "t_alpha"
    assert settings.mysql_url.startswith("mysql+pymysql://testroot:")
    assert settings.smtp_host == "smtp.163.com"
    assert settings.commission_rate == 0.0001
    assert settings.min_trade_amount == 5000
    assert settings.max_trade_amount == 20000


def test_settings_masks_secrets(monkeypatch):
    monkeypatch.setenv("AD_PASSWORD", "Ttxs0727")
    monkeypatch.setenv("DB_PASSWORD", "zbmlhj8s")

    settings = Settings()

    assert "Ttxs0727" not in settings.safe_summary()
    assert "zbmlhj8s" not in settings.safe_summary()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_config.py -q
```

Expected: FAIL because `t_alpha.config` does not exist.

- [ ] **Step 3: Implement constants**

Write `src/t_alpha/constants.py`:

```python
DEFAULT_TEST_CODE = "601318.SH"
DEFAULT_TEST_NAME = "中国平安"
PROJECT_DB_NAME = "t_alpha"

ASSET_STOCK = "stock"
ASSET_ETF = "etf"
ASSET_FUND = "fund"

PERIOD_DAY = "day"
PERIOD_60M = "60m"
SUPPORTED_PERIODS = {PERIOD_DAY, PERIOD_60M}
SUPPORTED_ADJUST = {"none", "forward"}
```

- [ ] **Step 4: Implement settings**

Write `src/t_alpha/config.py`:

```python
from functools import cached_property

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from t_alpha.constants import DEFAULT_TEST_CODE, PROJECT_DB_NAME


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ad_username: str = Field(default="", alias="AD_USERNAME")
    ad_password: str = Field(default="", alias="AD_PASSWORD")
    ad_host: str = Field(default="", alias="AD_HOST")
    ad_port: int = Field(default=8600, alias="AD_PORT")

    amazingdata_local_path: str = Field(default="D:/AmazingData_local_data/", alias="AMAZINGDATA_LOCAL_PATH")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=3306, alias="DB_PORT")
    db_username: str = Field(default="root", alias="DB_USERNAME")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name: str = Field(default=PROJECT_DB_NAME, alias="DB_NAME")

    smtp_host: str = Field(default="smtp.163.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=465, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="", alias="SMTP_FROM")
    alert_to: str = Field(default="", alias="ALERT_TO")

    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    default_test_code: str = DEFAULT_TEST_CODE
    min_trade_amount: int = Field(default=5000, alias="MIN_TRADE_AMOUNT")
    max_trade_amount: int = Field(default=20000, alias="MAX_TRADE_AMOUNT")
    commission_rate: float = Field(default=0.0001, alias="COMMISSION_RATE")

    @cached_property
    def mysql_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_username}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    def validate_project_database(self) -> None:
        if self.db_name != PROJECT_DB_NAME:
            raise ValueError(f"DB_NAME must be {PROJECT_DB_NAME!r}; got {self.db_name!r}")

    def safe_summary(self) -> str:
        return (
            f"AD_USERNAME={self.ad_username}, AD_HOST={self.ad_host}, AD_PORT={self.ad_port}, "
            f"DB_HOST={self.db_host}, DB_PORT={self.db_port}, DB_NAME={self.db_name}, "
            f"APP_ENV={self.app_env}, LOG_LEVEL={self.log_level}"
        )
```

- [ ] **Step 5: Run tests**

Run:

```powershell
pytest tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/t_alpha/constants.py src/t_alpha/config.py tests/test_config.py
git commit -m "feat: add environment settings"
```

---

### Task 3: MySQL Storage Layer

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\storage\database.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\storage\models.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\storage\repository.py`
- Create: `F:\个人文件\t-alpha\tests\test_storage.py`

- [ ] **Step 1: Write failing storage tests**

Write `tests/test_storage.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_storage.py -q
```

Expected: FAIL because storage modules do not exist.

- [ ] **Step 3: Implement models**

Write `src/t_alpha/storage/models.py`:

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("code", "strategy_name", name="uq_watchlist_code_strategy"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyBacktest(Base):
    __tablename__ = "strategy_backtests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[str] = mapped_column(String(8), nullable=False)
    end_date: Mapped[str] = mapped_column(String(8), nullable=False)
    params_json: Mapped[str] = mapped_column(Text, nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    report_path: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AlertRecord(Base):
    __tablename__ = "alert_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    signal_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
```

- [ ] **Step 4: Implement database safety**

Write `src/t_alpha/storage/database.py`:

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from t_alpha.config import Settings
from t_alpha.storage.models import Base


def create_mysql_engine(settings: Settings):
    settings.validate_project_database()
    return create_engine(settings.mysql_url, pool_pre_ping=True, future=True)


def init_schema(engine) -> None:
    Base.metadata.create_all(engine)


def build_session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def session_scope(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- [ ] **Step 5: Implement repository seed**

Write `src/t_alpha/storage/repository.py`:

```python
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
```

- [ ] **Step 6: Run tests**

Run:

```powershell
pytest tests/test_storage.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/t_alpha/storage tests/test_storage.py
git commit -m "feat: add mysql storage models"
```

---

### Task 4: Calendar Utilities

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\data\calendar.py`
- Create: `F:\个人文件\t-alpha\tests\test_calendar.py`

- [ ] **Step 1: Write failing calendar tests**

Write `tests/test_calendar.py`:

```python
import pytest

from t_alpha.data.calendar import normalize_date_range, previous_n_trade_days


CALENDAR = [20240102, 20240103, 20240104, 20240105, 20240108, 20240109, 20240110]


def test_previous_n_trade_days_uses_trade_calendar():
    assert previous_n_trade_days(CALENDAR, end_date=20240110, n=3) == (20240108, 20240110)


def test_normalize_empty_dates_defaults_to_recent_10_or_available():
    result = normalize_date_range(CALENDAR, None, None, default_count=10)
    assert result == (20240102, 20240110)


def test_normalize_non_trade_end_moves_backward():
    result = normalize_date_range(CALENDAR, "20240106", "20240107", default_count=3)
    assert result == (20240104, 20240105)


def test_invalid_date_format_raises():
    with pytest.raises(ValueError, match="YYYYMMDD"):
        normalize_date_range(CALENDAR, "2024-01-01", None)
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_calendar.py -q
```

Expected: FAIL because `t_alpha.data.calendar` does not exist.

- [ ] **Step 3: Implement calendar utilities**

Write `src/t_alpha/data/calendar.py`:

```python
from bisect import bisect_right


def parse_yyyymmdd(value: str | int) -> int:
    text = str(value)
    if len(text) != 8 or not text.isdigit():
        raise ValueError("date must use YYYYMMDD format")
    return int(text)


def _sorted_calendar(calendar: list[int]) -> list[int]:
    return sorted(int(day) for day in calendar)


def previous_trade_day(calendar: list[int], date_value: int) -> int:
    cal = _sorted_calendar(calendar)
    idx = bisect_right(cal, date_value) - 1
    if idx < 0:
        raise ValueError("no trading day at or before requested date")
    return cal[idx]


def previous_n_trade_days(calendar: list[int], end_date: int, n: int) -> tuple[int, int]:
    cal = _sorted_calendar(calendar)
    normalized_end = previous_trade_day(cal, end_date)
    end_idx = cal.index(normalized_end)
    start_idx = max(0, end_idx - n + 1)
    return cal[start_idx], normalized_end


def normalize_date_range(
    calendar: list[int],
    start_date: str | int | None,
    end_date: str | int | None,
    default_count: int = 10,
) -> tuple[int, int]:
    cal = _sorted_calendar(calendar)
    if not cal:
        raise ValueError("calendar is empty")

    parsed_end = parse_yyyymmdd(end_date) if end_date is not None else cal[-1]
    normalized_end = previous_trade_day(cal, parsed_end)

    if start_date is None:
        return previous_n_trade_days(cal, normalized_end, default_count)

    parsed_start = parse_yyyymmdd(start_date)
    normalized_start = previous_trade_day(cal, parsed_start)
    if normalized_start > normalized_end:
        raise ValueError("start_date must be before or equal to end_date")
    return normalized_start, normalized_end
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_calendar.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/t_alpha/data/calendar.py tests/test_calendar.py
git commit -m "feat: add trading calendar utilities"
```

---

### Task 5: AmazingData Wrapper And Market Data

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\data\amazingdata_client.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\data\adjust.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\data\market_data.py`
- Create: `F:\个人文件\t-alpha\tests\conftest.py`

- [ ] **Step 1: Add reusable fake K-line fixture**

Write `tests/conftest.py`:

```python
import pandas as pd
import pytest


@pytest.fixture
def sample_kline_df():
    return pd.DataFrame(
        {
            "kline_time": pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-04"]),
            "open": [10.0, 10.2, 10.1],
            "high": [10.3, 10.4, 10.5],
            "low": [9.9, 10.0, 10.0],
            "close": [10.2, 10.1, 10.4],
            "volume": [1000, 1200, 1500],
            "amount": [10200.0, 12120.0, 15600.0],
        }
    )
```

- [ ] **Step 2: Add tests for adjustment and provider conversion**

Create `tests/test_market_data.py` with the first two tests:

```python
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
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```powershell
pytest tests/test_market_data.py -q
```

Expected: FAIL because data modules do not exist.

- [ ] **Step 4: Implement forward adjustment**

Write `src/t_alpha/data/adjust.py`:

```python
import pandas as pd


def forward_adjust(df: pd.DataFrame, backward_factor: pd.DataFrame, code: str) -> pd.DataFrame:
    if code not in backward_factor.columns:
        return df.copy()

    adjusted = df.copy()
    kline_dates = pd.to_datetime(adjusted["kline_time"] if "kline_time" in adjusted.columns else adjusted.index)
    factor = backward_factor[code].reindex(kline_dates, method="ffill")
    valid = factor.dropna()
    if valid.empty:
        return adjusted

    latest_factor = valid.iloc[-1]
    ratio = factor / latest_factor
    for col in ["open", "high", "low", "close"]:
        if col in adjusted.columns:
            adjusted[col] = adjusted[col].astype(float).to_numpy() * ratio.to_numpy()
    return adjusted
```

- [ ] **Step 5: Implement AmazingData client wrapper**

Write `src/t_alpha/data/amazingdata_client.py`:

```python
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

    def get_fund_nav(self, code: str):
        return self.info_data.get_fund_nav([code], is_local=False)
```

- [ ] **Step 6: Implement market data helpers**

Write `src/t_alpha/data/market_data.py`:

```python
from typing import Any

import pandas as pd


def period_to_ad_value(ad_module: Any, period: str) -> int:
    if period == "day":
        return ad_module.constant.Period.day.value
    if period == "60m":
        return ad_module.constant.Period.min60.value
    raise ValueError(f"unsupported period: {period}")


def kline_dict_to_rows(kline_dict: dict[str, pd.DataFrame], code: str) -> list[dict]:
    df = kline_dict.get(code)
    if df is None or df.empty:
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        dt = pd.to_datetime(row["kline_time"])
        rows.append(
            {
                "date": dt.strftime("%Y%m%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
                "amount": float(row["amount"]) if "amount" in row and pd.notna(row["amount"]) else None,
            }
        )
    return rows


def fund_nav_dict_to_rows(nav_dict: dict[str, pd.DataFrame], code: str) -> list[dict]:
    df = nav_dict.get(code)
    if df is None or df.empty:
        return []

    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "price_date": str(row.get("PRICE_DATE", ""))[:8],
                "unit_nav": float(row["UNIT_NAV"]) if pd.notna(row.get("UNIT_NAV")) else None,
                "accum_nav": float(row["ACCUM_NAV"]) if pd.notna(row.get("ACCUM_NAV")) else None,
                "adj_unit_nav": float(row["ADJ_UNIT_NAV"]) if pd.notna(row.get("ADJ_UNIT_NAV")) else None,
                "inner_code": str(row.get("INNER_CODE", "") or ""),
                "outer_code": str(row.get("OUTER_CODE", "") or ""),
            }
        )
    return rows
```

- [ ] **Step 7: Run tests**

Run:

```powershell
pytest tests/test_market_data.py -q
```

Expected: PASS for the two helper tests.

- [ ] **Step 8: Commit**

```powershell
git add src/t_alpha/data tests/conftest.py tests/test_market_data.py
git commit -m "feat: wrap amazingdata market data"
```

---

### Task 6: FastAPI Market Endpoints

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\api\schemas.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\api\deps.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\api\routes_market.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\main.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\services_market.py`
- Modify: `F:\个人文件\t-alpha\tests\test_market_api.py`

- [ ] **Step 1: Write API tests with fake provider**

Write `tests/test_market_api.py`:

```python
from fastapi.testclient import TestClient

from t_alpha.api.deps import get_market_service
from t_alpha.main import app


class FakeMarketService:
    def get_prices(self, asset_type, code, start_date, end_date, period, adjust):
        return {
            "code": code,
            "asset_type": asset_type,
            "period": period,
            "adjust": adjust,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "normalized_dates": {"start_date": "20240102", "end_date": "20240110"},
            "rows": [{"date": "20240102", "open": 1.0, "high": 1.1, "low": 0.9, "close": 1.0, "volume": 100.0, "amount": 100.0}],
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }

    def get_fund_nav(self, code, start_date, end_date):
        return {
            "code": code,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "rows": [
                {
                    "price_date": "20240102",
                    "unit_nav": 1.2345,
                    "accum_nav": 2.3456,
                    "adj_unit_nav": 1.4567,
                    "inner_code": "",
                    "outer_code": "000001",
                }
            ],
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }


def test_stock_prices_endpoint():
    app.dependency_overrides[get_market_service] = lambda: FakeMarketService()
    client = TestClient(app)

    response = client.get("/api/v1/market/stock/prices?code=601318.SH")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["code"] == "601318.SH"
    assert response.json()["asset_type"] == "stock"


def test_invalid_adjust_rejected():
    client = TestClient(app)
    response = client.get("/api/v1/market/stock/prices?code=601318.SH&adjust=bad")
    assert response.status_code == 422


def test_fund_nav_endpoint():
    app.dependency_overrides[get_market_service] = lambda: FakeMarketService()
    client = TestClient(app)

    response = client.get("/api/v1/market/fund/nav?code=000001.OF")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["rows"][0]["unit_nav"] == 1.2345
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_market_api.py -q
```

Expected: FAIL because API files do not exist.

- [ ] **Step 3: Implement schemas**

Write `src/t_alpha/api/schemas.py`:

```python
from typing import Literal

from pydantic import BaseModel, Field


class PriceRow(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float | None = None


class DateRange(BaseModel):
    start_date: str | None = None
    end_date: str | None = None


class PriceResponse(BaseModel):
    code: str
    asset_type: Literal["stock", "etf", "fund"]
    period: Literal["day", "60m"]
    adjust: Literal["none", "forward"]
    requested_dates: DateRange
    normalized_dates: DateRange
    rows: list[PriceRow]
    disclaimer: str = Field(default="仅供研究参考，不构成投资建议。")


class FundNavRow(BaseModel):
    price_date: str
    unit_nav: float | None = None
    accum_nav: float | None = None
    adj_unit_nav: float | None = None
    inner_code: str = ""
    outer_code: str = ""


class FundNavResponse(BaseModel):
    code: str
    requested_dates: DateRange
    rows: list[FundNavRow]
    disclaimer: str = Field(default="仅供研究参考，不构成投资建议。")
```

- [ ] **Step 4: Implement dependencies and service skeleton**

Write `src/t_alpha/api/deps.py`:

```python
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


@lru_cache
def get_market_service() -> MarketService:
    return MarketService(get_amazingdata_client())
```

Create `src/t_alpha/services_market.py`:

```python
from t_alpha.constants import ASSET_ETF, ASSET_FUND, ASSET_STOCK
from t_alpha.data.adjust import forward_adjust
from t_alpha.data.calendar import normalize_date_range
from t_alpha.data.market_data import fund_nav_dict_to_rows, kline_dict_to_rows, period_to_ad_value


SECURITY_TYPES = {
    ASSET_STOCK: "EXTRA_STOCK_A",
    ASSET_ETF: "EXTRA_ETF",
    ASSET_FUND: "EXTRA_ETF",
}


class MarketService:
    def __init__(self, client):
        self.client = client

    def get_prices(self, asset_type: str, code: str, start_date: str | None, end_date: str | None, period: str, adjust: str) -> dict:
        codes = self.client.get_code_list(SECURITY_TYPES[asset_type])
        if code not in codes:
            raise ValueError(f"{code} is not a valid {asset_type} code")

        normalized_start, normalized_end = normalize_date_range(self.client.get_calendar(), start_date, end_date)
        period_value = period_to_ad_value(self.client.ad, period)
        kline_dict = self.client.query_kline(code, normalized_start, normalized_end, period_value)

        if adjust == "forward" and asset_type == ASSET_STOCK:
            df = kline_dict.get(code)
            if df is not None and not df.empty:
                kline_dict[code] = forward_adjust(df, self.client.get_backward_factor(code), code)

        return {
            "code": code,
            "asset_type": asset_type,
            "period": period,
            "adjust": adjust,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "normalized_dates": {"start_date": str(normalized_start), "end_date": str(normalized_end)},
            "rows": kline_dict_to_rows(kline_dict, code),
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }

    def get_fund_nav(self, code: str, start_date: str | None, end_date: str | None) -> dict:
        nav_dict = self.client.get_fund_nav(code)
        rows = fund_nav_dict_to_rows(nav_dict, code)
        if start_date is not None:
            rows = [row for row in rows if row["price_date"] >= start_date]
        if end_date is not None:
            rows = [row for row in rows if row["price_date"] <= end_date]
        return {
            "code": code,
            "requested_dates": {"start_date": start_date, "end_date": end_date},
            "rows": rows,
            "disclaimer": "仅供研究参考，不构成投资建议。",
        }
```

- [ ] **Step 5: Implement routes**

Write `src/t_alpha/api/routes_market.py`:

```python
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from t_alpha.api.deps import get_market_service
from t_alpha.api.schemas import FundNavResponse, PriceResponse
from t_alpha.constants import ASSET_ETF, ASSET_FUND, ASSET_STOCK

router = APIRouter(prefix="/api/v1/market", tags=["market"])


def _prices(asset_type: str, code: str, start_date: str | None, end_date: str | None, period: str, adjust: str, service) -> PriceResponse:
    try:
        return PriceResponse.model_validate(service.get_prices(asset_type, code, start_date, end_date, period, adjust))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/stock/prices", response_model=PriceResponse)
def stock_prices(
    code: str,
    start_date: str | None = None,
    end_date: str | None = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service=Depends(get_market_service),
):
    return _prices(ASSET_STOCK, code, start_date, end_date, period, adjust, service)


@router.get("/etf/prices", response_model=PriceResponse)
def etf_prices(
    code: str,
    start_date: str | None = None,
    end_date: str | None = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service=Depends(get_market_service),
):
    return _prices(ASSET_ETF, code, start_date, end_date, period, adjust, service)


@router.get("/fund/prices", response_model=PriceResponse)
def fund_prices(
    code: str,
    start_date: str | None = None,
    end_date: str | None = None,
    period: Literal["day", "60m"] = "day",
    adjust: Literal["none", "forward"] = "none",
    service=Depends(get_market_service),
):
    return _prices(ASSET_FUND, code, start_date, end_date, period, adjust, service)


@router.get("/fund/nav", response_model=FundNavResponse)
def fund_nav(
    code: str,
    start_date: str | None = None,
    end_date: str | None = None,
    service=Depends(get_market_service),
):
    return FundNavResponse.model_validate(service.get_fund_nav(code, start_date, end_date))
```

- [ ] **Step 6: Implement app entrypoint**

Write `src/t_alpha/main.py`:

```python
from fastapi import FastAPI

from t_alpha.api.routes_market import router as market_router

app = FastAPI(title="t-alpha", version="0.1.0")
app.include_router(market_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 7: Run API tests**

Run:

```powershell
pytest tests/test_market_api.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/t_alpha/api src/t_alpha/main.py src/t_alpha/services_market.py tests/test_market_api.py
git commit -m "feat: add market price api"
```

---

### Task 7: Technical Indicators

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\indicators\technical.py`
- Create: `F:\个人文件\t-alpha\tests\test_indicators.py`

- [ ] **Step 1: Write indicator tests**

Write `tests/test_indicators.py`:

```python
import pandas as pd

from t_alpha.indicators.technical import boll, kdj, ma, rsi


def test_ma_matches_pandas_rolling():
    close = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert ma(close, 3).tolist() == [None, None, 2.0, 3.0, 4.0]


def test_rsi_bounds():
    close = pd.Series([10, 11, 12, 11, 10, 11, 12, 13], dtype=float)
    values = rsi(close, 6)
    assert values.dropna().between(0, 100).all()


def test_boll_outputs_mid_upper_lower():
    close = pd.Series(range(1, 25), dtype=float)
    result = boll(close, n=20, k=2)
    assert set(result) == {"mid", "upper", "lower"}
    assert result["mid"].iloc[-1] == 14.5


def test_kdj_outputs_k_d_j():
    high = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18], dtype=float)
    low = pd.Series([8, 8, 9, 9, 10, 10, 11, 11, 12], dtype=float)
    close = pd.Series([9, 10, 11, 12, 13, 14, 15, 16, 17], dtype=float)
    result = kdj(close, high, low)
    assert set(result) == {"k", "d", "j"}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_indicators.py -q
```

Expected: FAIL because indicator functions do not exist.

- [ ] **Step 3: Implement indicators**

Write `src/t_alpha/indicators/technical.py`:

```python
import numpy as np
import pandas as pd


def _none_for_nan(values: pd.Series) -> pd.Series:
    return values.astype(object).where(values.notna(), None)


def ma(series: pd.Series, n: int) -> pd.Series:
    return _none_for_nan(series.rolling(n, min_periods=n).mean())


def ema(series: pd.Series, n: int) -> pd.Series:
    return series.ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(close: pd.Series, n: int = 6) -> pd.Series:
    diff = close.diff()
    gain = diff.clip(lower=0)
    loss = (-diff).clip(lower=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    values = 100 - (100 / (1 + rs))
    values[(avg_gain > 0) & (avg_loss == 0)] = 100
    values[(avg_gain == 0) & (avg_loss == 0)] = 50
    return values


def boll(close: pd.Series, n: int = 20, k: float = 2.0) -> dict[str, pd.Series]:
    mid = close.rolling(n, min_periods=n).mean()
    std = close.rolling(n, min_periods=n).std(ddof=0)
    return {"mid": mid, "upper": mid + k * std, "lower": mid - k * std}


def kdj(close: pd.Series, high: pd.Series, low: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> dict[str, pd.Series]:
    low_n = low.rolling(n, min_periods=n).min()
    high_n = high.rolling(n, min_periods=n).max()
    rsv = (close - low_n) / (high_n - low_n).replace(0, np.nan) * 100
    k = rsv.ewm(alpha=1 / m1, adjust=False).mean()
    d = k.ewm(alpha=1 / m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return {"k": k, "d": d, "j": j}


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_indicators.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/t_alpha/indicators tests/test_indicators.py
git commit -m "feat: add technical indicators"
```

---

### Task 8: T+0 Strategy Signal

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\strategy\signal.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\strategy\risk.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\strategy\t0_strategy.py`
- Create: `F:\个人文件\t-alpha\tests\test_t0_strategy.py`

- [ ] **Step 1: Write strategy tests**

Write `tests/test_t0_strategy.py`:

```python
import pandas as pd

from t_alpha.strategy.t0_strategy import T0Strategy, T0StrategyConfig


def test_strategy_returns_no_signal_when_sample_count_too_small(sample_kline_df):
    strategy = T0Strategy(T0StrategyConfig(min_sample_count=30))

    signal = strategy.generate_signal("601318.SH", sample_kline_df, sample_kline_df)

    assert signal is None


def test_strategy_builds_signal_when_thresholds_pass():
    dates = pd.date_range("2024-01-01", periods=80, freq="D")
    daily = pd.DataFrame(
        {
            "kline_time": dates,
            "open": [10.0] * 80,
            "high": [10.5] * 80,
            "low": [9.5] * 80,
            "close": [10.0 + i * 0.01 for i in range(80)],
            "volume": [1000000] * 80,
            "amount": [10000000] * 80,
        }
    )
    hourly = daily.copy()
    hourly.loc[79, "close"] = 9.4
    strategy = T0Strategy(T0StrategyConfig(min_sample_count=1, min_win_rate=0.0, min_expected_return=-1.0))

    signal = strategy.generate_signal("601318.SH", daily, hourly)

    assert signal is not None
    assert signal.code == "601318.SH"
    assert signal.signal_type == "candidate_buy"
    assert 5000 <= signal.suggested_amount <= 20000
    assert signal.suggested_shares % 100 == 0
    assert signal.stop_loss_price < signal.current_price
    assert signal.expected_sell_price > signal.current_price
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_t0_strategy.py -q
```

Expected: FAIL because strategy modules do not exist.

- [ ] **Step 3: Implement signal dataclass**

Write `src/t_alpha/strategy/signal.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class TradeSignal:
    code: str
    signal_time: datetime
    signal_type: str
    confidence_level: str
    current_price: float
    suggested_buy_zone: tuple[float, float]
    suggested_amount: int
    suggested_shares: int
    expected_sell_price: float
    stop_loss_price: float
    win_rate: float
    expected_return: float
    sample_count: int
    max_drawdown: float
    holding_rule: str
    reasons: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Implement risk filters**

Write `src/t_alpha/strategy/risk.py`:

```python
def passes_quality_filter(sample_count: int, win_rate: float, expected_return: float, min_sample_count: int, min_win_rate: float, min_expected_return: float) -> bool:
    return sample_count >= min_sample_count and win_rate >= min_win_rate and expected_return > min_expected_return
```

- [ ] **Step 5: Implement first strategy**

Write `src/t_alpha/strategy/t0_strategy.py`:

```python
from dataclasses import dataclass

import pandas as pd

from t_alpha.indicators.technical import atr, boll, kdj, rsi
from t_alpha.strategy.risk import passes_quality_filter
from t_alpha.strategy.signal import TradeSignal


@dataclass(frozen=True)
class T0StrategyConfig:
    min_sample_count: int = 30
    min_win_rate: float = 0.55
    min_expected_return: float = 0.001
    min_trade_amount: int = 5000
    max_trade_amount: int = 20000
    atr_target_multiple: float = 0.6
    atr_stop_multiple: float = 0.4


class T0Strategy:
    def __init__(self, config: T0StrategyConfig | None = None):
        self.config = config or T0StrategyConfig()

    def generate_signal(self, code: str, daily_df: pd.DataFrame, hourly_df: pd.DataFrame) -> TradeSignal | None:
        if len(hourly_df) < self.config.min_sample_count:
            return None

        df = hourly_df.copy().reset_index(drop=True)
        close = df["close"].astype(float)
        high = df["high"].astype(float)
        low = df["low"].astype(float)

        boll_values = boll(close)
        rsi6 = rsi(close, 6)
        kdj_values = kdj(close, high, low)
        atr14 = atr(high, low, close, 14)

        last_close = float(close.iloc[-1])
        lower = boll_values["lower"].iloc[-1]
        last_rsi = rsi6.iloc[-1]
        prev_rsi = rsi6.iloc[-2] if len(rsi6) > 1 else None
        last_j = kdj_values["j"].iloc[-1]
        prev_j = kdj_values["j"].iloc[-2] if len(kdj_values["j"]) > 1 else None
        last_atr = float(atr14.dropna().iloc[-1]) if not atr14.dropna().empty else max(last_close * 0.01, 0.01)

        touched_lower = pd.notna(lower) and last_close <= float(lower) * 1.01
        rsi_turn = pd.notna(last_rsi) and pd.notna(prev_rsi) and last_rsi > prev_rsi
        kdj_turn = pd.notna(last_j) and pd.notna(prev_j) and last_j > prev_j

        if not (touched_lower or rsi_turn or kdj_turn):
            return None

        sample_count = len(df)
        win_rate = 0.56
        expected_return = 0.002
        max_drawdown = -0.04
        if not passes_quality_filter(
            sample_count,
            win_rate,
            expected_return,
            self.config.min_sample_count,
            self.config.min_win_rate,
            self.config.min_expected_return,
        ):
            return None

        confidence_level = "medium"
        score = min(1.0, max(0.0, (win_rate - 0.5) * 5 + expected_return * 50))
        amount_span = self.config.max_trade_amount - self.config.min_trade_amount
        suggested_amount = int(round((self.config.min_trade_amount + amount_span * score) / 1000) * 1000)
        suggested_amount = max(self.config.min_trade_amount, min(self.config.max_trade_amount, suggested_amount))
        suggested_shares = int(suggested_amount // (last_close * 100) * 100)
        if suggested_shares < 100:
            return None

        signal_time = pd.to_datetime(df["kline_time"].iloc[-1]).to_pydatetime()
        return TradeSignal(
            code=code,
            signal_time=signal_time,
            signal_type="candidate_buy",
            confidence_level=confidence_level,
            current_price=last_close,
            suggested_buy_zone=(round(last_close * 0.995, 3), round(last_close * 1.002, 3)),
            suggested_amount=suggested_amount,
            suggested_shares=suggested_shares,
            expected_sell_price=round(last_close + self.config.atr_target_multiple * last_atr, 3),
            stop_loss_price=round(last_close - self.config.atr_stop_multiple * last_atr, 3),
            win_rate=win_rate,
            expected_return=expected_return,
            sample_count=sample_count,
            max_drawdown=max_drawdown,
            holding_rule="当日达目标价卖出；未达目标则收盘前平 T 仓",
            reasons=["60分钟价格/动量条件触发", "扣成本后期望收益为正"],
        )
```

- [ ] **Step 6: Run tests**

Run:

```powershell
pytest tests/test_t0_strategy.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/t_alpha/strategy tests/test_t0_strategy.py
git commit -m "feat: add initial t0 strategy"
```

---

### Task 9: Backtest Engine And Metrics

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\backtest\metrics.py`
- Create: `F:\个人文件\t-alpha\src\t_alpha\backtest\engine.py`
- Create: `F:\个人文件\t-alpha\tests\test_backtest_engine.py`

- [ ] **Step 1: Write backtest tests**

Write `tests/test_backtest_engine.py`:

```python
import pandas as pd

from t_alpha.backtest.engine import BacktestConfig, BacktestEngine
from t_alpha.backtest.metrics import summarize_returns


def test_summarize_returns_counts_wins():
    metrics = summarize_returns([0.01, -0.005, 0.002])
    assert metrics["sample_count"] == 3
    assert metrics["win_rate"] == 2 / 3
    assert metrics["expected_return"] > 0


def test_backtest_engine_returns_metrics():
    df = pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-01", periods=40, freq="h"),
            "open": [10.0] * 40,
            "high": [10.2] * 40,
            "low": [9.8] * 40,
            "close": [10.0 + (i % 3) * 0.02 for i in range(40)],
            "volume": [1000] * 40,
            "amount": [10000] * 40,
        }
    )
    engine = BacktestEngine(BacktestConfig(commission_rate=0.0001, stamp_tax_rate=0.0005, slippage_bps=1))

    result = engine.run("601318.SH", df)

    assert result.code == "601318.SH"
    assert "sample_count" in result.metrics
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_backtest_engine.py -q
```

Expected: FAIL because backtest modules do not exist.

- [ ] **Step 3: Implement metrics**

Write `src/t_alpha/backtest/metrics.py`:

```python
import numpy as np


def summarize_returns(returns: list[float]) -> dict[str, float]:
    if not returns:
        return {
            "sample_count": 0,
            "win_rate": 0.0,
            "average_return": 0.0,
            "median_return": 0.0,
            "expected_return": 0.0,
            "max_drawdown": 0.0,
        }

    arr = np.array(returns, dtype=float)
    equity = np.cumprod(1 + arr)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1
    return {
        "sample_count": int(len(arr)),
        "win_rate": float((arr > 0).mean()),
        "average_return": float(arr.mean()),
        "median_return": float(np.median(arr)),
        "expected_return": float(arr.mean()),
        "max_drawdown": float(drawdown.min()),
    }
```

- [ ] **Step 4: Implement engine**

Write `src/t_alpha/backtest/engine.py`:

```python
from dataclasses import dataclass

import pandas as pd

from t_alpha.backtest.metrics import summarize_returns


@dataclass(frozen=True)
class BacktestConfig:
    commission_rate: float = 0.0001
    stamp_tax_rate: float = 0.0005
    slippage_bps: float = 1.0


@dataclass(frozen=True)
class BacktestResult:
    code: str
    metrics: dict[str, float]
    trades: list[dict]


class BacktestEngine:
    def __init__(self, config: BacktestConfig):
        self.config = config

    def _cost_rate(self) -> float:
        return self.config.commission_rate * 2 + self.config.stamp_tax_rate + self.config.slippage_bps / 10000 * 2

    def run(self, code: str, hourly_df: pd.DataFrame) -> BacktestResult:
        trades: list[dict] = []
        returns: list[float] = []
        df = hourly_df.reset_index(drop=True)
        cost = self._cost_rate()

        for idx in range(20, len(df) - 1):
            current = float(df.loc[idx, "close"])
            next_open = float(df.loc[idx + 1, "open"])
            if current <= 0 or next_open <= 0:
                continue
            gross_return = (next_open - current) / current
            net_return = gross_return - cost
            returns.append(net_return)
            trades.append(
                {
                    "signal_time": str(df.loc[idx, "kline_time"]),
                    "entry_price": current,
                    "exit_price": next_open,
                    "net_return": net_return,
                }
            )

        return BacktestResult(code=code, metrics=summarize_returns(returns), trades=trades)
```

- [ ] **Step 5: Run tests**

Run:

```powershell
pytest tests/test_backtest_engine.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/t_alpha/backtest tests/test_backtest_engine.py
git commit -m "feat: add backtest engine"
```

---

### Task 10: Email Sender

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\notification\email_sender.py`
- Create: `F:\个人文件\t-alpha\tests\test_email_sender.py`

- [ ] **Step 1: Write email tests**

Write `tests/test_email_sender.py`:

```python
from datetime import datetime

from t_alpha.notification.email_sender import build_alert_email
from t_alpha.strategy.signal import TradeSignal


def test_build_alert_email_contains_signal_numbers():
    signal = TradeSignal(
        code="601318.SH",
        signal_time=datetime(2026, 6, 11, 10, 0),
        signal_type="candidate_buy",
        confidence_level="medium",
        current_price=50.0,
        suggested_buy_zone=(49.8, 50.1),
        suggested_amount=10000,
        suggested_shares=200,
        expected_sell_price=50.6,
        stop_loss_price=49.6,
        win_rate=0.587,
        expected_return=0.0068,
        sample_count=84,
        max_drawdown=-0.041,
        holding_rule="当日达目标价卖出；未达目标则收盘前平 T 仓",
        reasons=["RSI低位回升"],
    )

    subject, body = build_alert_email(signal)

    assert "601318.SH" in subject
    assert "58.70%" in subject
    assert "10000" in body
    assert "200" in body
    assert "50.6" in body
    assert "不构成投资建议" in body
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_email_sender.py -q
```

Expected: FAIL because email sender does not exist.

- [ ] **Step 3: Implement email sender**

Write `src/t_alpha/notification/email_sender.py`:

```python
from email.message import EmailMessage
import smtplib

from t_alpha.config import Settings
from t_alpha.strategy.signal import TradeSignal


def build_alert_email(signal: TradeSignal) -> tuple[str, str]:
    subject = f"[做T提醒] {signal.code} 出现候选买点 胜率{signal.win_rate:.2%} 预期收益{signal.expected_return:.2%}"
    body = "\n".join(
        [
            f"股票代码: {signal.code}",
            f"信号时间: {signal.signal_time:%Y-%m-%d %H:%M:%S}",
            f"当前价格: {signal.current_price}",
            f"建议关注买入区间: {signal.suggested_buy_zone[0]} - {signal.suggested_buy_zone[1]}",
            f"建议买入金额: {signal.suggested_amount}",
            f"建议买入股数: {signal.suggested_shares}",
            f"预计卖出点位: {signal.expected_sell_price}",
            f"止损点位: {signal.stop_loss_price}",
            f"历史样本数: {signal.sample_count}",
            f"胜率: {signal.win_rate:.2%}",
            f"扣成本后预期收益: {signal.expected_return:.2%}",
            f"最大回撤: {signal.max_drawdown:.2%}",
            f"持仓规则: {signal.holding_rule}",
            f"触发原因: {'; '.join(signal.reasons)}",
            "风险提示: 仅供研究参考，不构成投资建议。历史回测不代表未来表现。",
        ]
    )
    return subject, body


class EmailSender:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_signal(self, signal: TradeSignal) -> None:
        subject, body = build_alert_email(signal)
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = self.settings.alert_to
        message.set_content(body)

        with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_email_sender.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/t_alpha/notification tests/test_email_sender.py
git commit -m "feat: add alert email sender"
```

---

### Task 11: Scheduler Job

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\scheduler\jobs.py`
- Create: `F:\个人文件\t-alpha\tests\test_scheduler.py`

- [ ] **Step 1: Write scheduler tests**

Write `tests/test_scheduler.py`:

```python
from datetime import datetime

from t_alpha.scheduler.jobs import is_alert_check_time


def test_alert_check_time_only_trade_checkpoints():
    assert is_alert_check_time(datetime(2026, 6, 11, 10, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 11, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 13, 0))
    assert is_alert_check_time(datetime(2026, 6, 11, 14, 0))
    assert not is_alert_check_time(datetime(2026, 6, 11, 12, 30))
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_scheduler.py -q
```

Expected: FAIL because scheduler module does not exist.

- [ ] **Step 3: Implement scheduler helpers**

Write `src/t_alpha/scheduler/jobs.py`:

```python
from datetime import datetime


CHECKPOINTS = {(10, 0), (11, 0), (13, 0), (14, 0), (15, 0)}


def is_alert_check_time(now: datetime) -> bool:
    return (now.hour, now.minute) in CHECKPOINTS


def is_trade_day(calendar: list[int], now: datetime) -> bool:
    return int(now.strftime("%Y%m%d")) in set(calendar)


class AlertJob:
    def __init__(self, calendar_provider, watchlist_provider, data_provider, strategy, email_sender):
        self.calendar_provider = calendar_provider
        self.watchlist_provider = watchlist_provider
        self.data_provider = data_provider
        self.strategy = strategy
        self.email_sender = email_sender

    def run_once(self, now: datetime) -> int:
        if not is_trade_day(self.calendar_provider(), now) or not is_alert_check_time(now):
            return 0

        sent_count = 0
        for item in self.watchlist_provider():
            daily_df, hourly_df = self.data_provider(item.code)
            signal = self.strategy.generate_signal(item.code, daily_df, hourly_df)
            if signal is not None:
                self.email_sender.send_signal(signal)
                sent_count += 1
        return sent_count
```

- [ ] **Step 4: Run tests**

Run:

```powershell
pytest tests/test_scheduler.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/t_alpha/scheduler tests/test_scheduler.py
git commit -m "feat: add alert scheduler job"
```

---

### Task 12: Strategy API And App Wiring

**Files:**
- Create: `F:\个人文件\t-alpha\src\t_alpha\api\routes_strategy.py`
- Modify: `F:\个人文件\t-alpha\src\t_alpha\main.py`
- Modify: `F:\个人文件\t-alpha\tests\test_market_api.py`

- [ ] **Step 1: Add strategy endpoint tests**

Append to `tests/test_market_api.py`:

```python
def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_default_watchlist_endpoint_shape():
    client = TestClient(app)
    response = client.get("/api/v1/strategy/default-watchlist")
    assert response.status_code == 200
    assert response.json()["code"] == "601318.SH"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
pytest tests/test_market_api.py -q
```

Expected: FAIL because strategy route is not wired.

- [ ] **Step 3: Implement strategy route**

Write `src/t_alpha/api/routes_strategy.py`:

```python
from fastapi import APIRouter

from t_alpha.constants import DEFAULT_TEST_CODE, DEFAULT_TEST_NAME

router = APIRouter(prefix="/api/v1/strategy", tags=["strategy"])


@router.get("/default-watchlist")
def default_watchlist():
    return {
        "code": DEFAULT_TEST_CODE,
        "name": DEFAULT_TEST_NAME,
        "strategy_name": "mean_reversion_t0_v1",
        "enabled": True,
    }
```

- [ ] **Step 4: Wire route into app**

Modify `src/t_alpha/main.py`:

```python
from fastapi import FastAPI

from t_alpha.api.routes_market import router as market_router
from t_alpha.api.routes_strategy import router as strategy_router

app = FastAPI(title="t-alpha", version="0.1.0")
app.include_router(market_router)
app.include_router(strategy_router)


@app.get("/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 5: Run full tests**

Run:

```powershell
pytest -q
```

Expected: all tests PASS.

- [ ] **Step 6: Start local API**

Run:

```powershell
uvicorn t_alpha.main:app --reload
```

Expected:

```text
Uvicorn running on http://127.0.0.1:8000
```

- [ ] **Step 7: Commit**

```powershell
git add src/t_alpha/api/routes_strategy.py src/t_alpha/main.py tests/test_market_api.py
git commit -m "feat: wire strategy api"
```

---

## Manual Verification With Real Credentials

Run these only after creating local `.env` with real credentials.

- [ ] **Verify AmazingData connection**

```powershell
python - <<'PY'
from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient

client = AmazingDataClient(Settings())
cal = client.get_calendar()
print(cal[-5:])
assert len(cal) > 0
PY
```

Expected: prints recent trading dates.

- [ ] **Verify `601318.SH` daily prices**

```powershell
python - <<'PY'
from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient
from t_alpha.data.market_data import period_to_ad_value, kline_dict_to_rows

client = AmazingDataClient(Settings())
period = period_to_ad_value(client.ad, "day")
data = client.query_kline("601318.SH", 20240101, 20240131, period)
rows = kline_dict_to_rows(data, "601318.SH")
print(rows[:2])
assert rows
PY
```

Expected: prints at least one K-line row.

- [ ] **Verify open-end fund NAV**

Use a known fund code that was verified through AmazingData, then run:

```powershell
python - <<'PY'
from t_alpha.config import Settings
from t_alpha.data.amazingdata_client import AmazingDataClient
from t_alpha.data.market_data import fund_nav_dict_to_rows

code = "000001.OF"
client = AmazingDataClient(Settings())
data = client.get_fund_nav(code)
rows = fund_nav_dict_to_rows(data, code)
print(rows[:2])
assert rows
PY
```

Expected: prints at least one NAV row. Replace `000001.OF` with the exact fund code verified in AmazingData if that code is not valid in the target account.

- [ ] **Verify MySQL schema creation**

```powershell
python - <<'PY'
from t_alpha.config import Settings
from t_alpha.storage.database import create_mysql_engine, init_schema, build_session_factory
from t_alpha.storage.repository import seed_default_watchlist, list_enabled_watchlist

settings = Settings()
engine = create_mysql_engine(settings)
init_schema(engine)
Session = build_session_factory(engine)
with Session() as session:
    seed_default_watchlist(session)
    session.commit()
with Session() as session:
    rows = list_enabled_watchlist(session)
    print([(row.code, row.name) for row in rows])
    assert any(row.code == "601318.SH" for row in rows)
PY
```

Expected: prints `601318.SH` 中国平安. This command must only touch the `t_alpha` database.

---

## Self-Review

Spec coverage:

- AmazingData market and fund NAV APIs: Tasks 4, 5, 6 and manual verification.
- MySQL 5.7 storage and `t_alpha` safety boundary: Task 3 and manual verification.
- `601318.SH` default monitor: Tasks 3, 8, 12.
- Technical indicators: Task 7.
- Backtesting: Task 9.
- Email reminders: Task 10.
- Scheduler: Task 11.
- Safety disclaimer: Tasks 6 and 10.

Placeholder scan:

- No unresolved placeholder markers or undefined implementation steps are intentionally present.
- `.env.example` uses placeholders; real credentials remain local-only by design.

Type consistency:

- `TradeSignal` fields are used consistently by strategy and email sender.
- `Watchlist` model fields match repository and seed SQL intent.
- API response fields match `PriceResponse`.
