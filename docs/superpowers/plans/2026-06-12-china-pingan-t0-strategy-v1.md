# China Ping An T0 Strategy v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the China Ping An low-buy T0 strategy v1 flow: parameterized signals, 3-year backtest and tuning, recent 3-month trade report, build/monitor APIs, and email-ready monitoring.

**Architecture:** Keep the current FastAPI and service-layer shape. Add focused strategy, backtest, optimizer, report, and service modules instead of expanding the existing simplified `t0_strategy.py` into a large file. The build endpoint fetches forward-adjusted day and 60m data, creates a stock-specific strategy report, persists the result, and the monitor endpoint enables alert scanning for passing strategies.

**Tech Stack:** Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2.x, pandas, numpy, pytest, httpx TestClient, AmazingData client wrapper.

---

## Scope Check

The spec touches strategy generation, backtesting, reporting, API, persistence, and monitoring. This is still one vertical product slice because each subsystem supports the same externally visible workflow:

1. Build strategy for one A-share code.
2. Return 3-year metrics and recent 3-month trades.
3. Enable monitoring only when the strategy passes gates.
4. Send email when a new buy point appears.

Do not add automatic order execution, account integration, overlapping T positions, high-sell/low-buy-back strategy, stop-loss, or portfolio allocation in this plan.

## File Structure

Create:

- `src/t_alpha/strategy/t0_models.py`: Dataclasses for strategy parameters, signal candidates, simulated trades, reports, eligibility, and monitor state payloads.
- `src/t_alpha/strategy/t0_rules.py`: Parameterized low-buy signal generation from day and 60m K-line data.
- `src/t_alpha/backtest/t0_engine.py`: Non-overlapping low-buy T0 simulation with next-60m-open entry, 3% target exit, 10-trading-day timeout, and configurable cost.
- `src/t_alpha/backtest/t0_optimizer.py`: Parameter grid search, train/validation/recent split, eligibility evaluation, and best-parameter selection.
- `src/t_alpha/services_strategy.py`: Application service for fetching 3-year market data, running optimizer, producing reports, persisting report JSON, and enabling monitors.
- `tests/test_t0_models.py`: Model serialization and amount/share behavior tests.
- `tests/test_t0_rules.py`: Signal rule tests without market/network dependencies.
- `tests/test_t0_engine_v1.py`: Backtest execution, target exit, timeout exit, non-overlap, and cost tests.
- `tests/test_t0_optimizer.py`: Split, best parameter, and eligibility tests.
- `tests/test_strategy_service.py`: Service orchestration tests with fake market client and monkeypatched persistence functions.
- `tests/test_strategy_api.py`: Build and monitor endpoint tests.

Modify:

- `src/t_alpha/config.py`: Add configurable T0 defaults.
- `src/t_alpha/constants.py`: Add strategy name constants used by reports, APIs, storage, and monitor jobs.
- `src/t_alpha/storage/models.py`: Add persisted strategy report and active T0 position models.
- `src/t_alpha/storage/repository.py`: Add report persistence and monitor helpers.
- `src/t_alpha/api/schemas.py`: Add request/response schemas for T0 build and monitor APIs.
- `src/t_alpha/api/deps.py`: Add `get_strategy_service`.
- `src/t_alpha/api/routes_strategy.py`: Add `/api/v1/strategy/t0/build` and `/api/v1/strategy/t0/monitor`.
- `src/t_alpha/scheduler/jobs.py`: Add monitor-aware buy-alert flow and no-overlap position handling.
- `src/t_alpha/notification/email_sender.py`: Include recent 3-month summary and v1 target/timeout fields.
- `docs/api_integration.md`: Document new endpoints and response shape.

---

### Task 1: T0 Domain Models

**Files:**
- Create: `src/t_alpha/strategy/t0_models.py`
- Create: `tests/test_t0_models.py`

- [ ] **Step 1: Write failing model tests**

Write `tests/test_t0_models.py`:

```python
from datetime import datetime

from t_alpha.strategy.t0_models import (
    T0Eligibility,
    T0StrategyParams,
    T0Trade,
    amount_to_board_lot_shares,
)


def test_amount_to_board_lot_shares_rounds_down_to_100_shares():
    assert amount_to_board_lot_shares(11000, 42.12) == 200
    assert amount_to_board_lot_shares(5000, 80.00) == 0


def test_trade_net_return_and_success_fields():
    trade = T0Trade(
        code="601318.SH",
        signal_time=datetime(2024, 1, 2, 10),
        buy_time=datetime(2024, 1, 2, 11),
        buy_price=40.0,
        buy_amount=12000,
        buy_shares=300,
        sell_time=datetime(2024, 1, 5, 15),
        sell_price=41.2,
        holding_trade_days=3,
        gross_return=0.03,
        net_return=0.0299,
        profit_amount=358.8,
        success=True,
        exit_reason="target",
        reasons=["BOLL lower touch", "RSI turn up"],
    )

    payload = trade.to_dict()

    assert payload["success"] is True
    assert payload["exit_reason"] == "target"
    assert payload["buy_time"] == "2024-01-02 11:00:00"


def test_eligibility_explains_failure_reason():
    eligibility = T0Eligibility(
        eligible=False,
        level="invalid",
        reasons=["3年有效交易数不足30笔"],
    )

    assert eligibility.to_dict()["reasons"] == ["3年有效交易数不足30笔"]


def test_strategy_params_default_values_match_design():
    params = T0StrategyParams()

    assert params.target_return == 0.03
    assert params.max_holding_trade_days == 10
    assert params.trade_cost_rate == 0.0001
    assert params.min_trade_amount == 5000
    assert params.max_trade_amount == 20000
```

- [ ] **Step 2: Run model tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_t0_models.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't_alpha.strategy.t0_models'`.

- [ ] **Step 3: Implement domain models**

Create `src/t_alpha/strategy/t0_models.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Literal


EligibilityLevel = Literal["eligible", "observe", "invalid"]
ExitReason = Literal["target", "timeout"]


@dataclass(frozen=True)
class T0StrategyParams:
    target_return: float = 0.03
    max_holding_trade_days: int = 10
    trade_cost_rate: float = 0.0001
    min_trade_amount: int = 5000
    max_trade_amount: int = 20000
    min_3y_trades: int = 60
    observe_min_3y_trades: int = 30
    min_success_rate: float = 0.50
    boll_n: int = 20
    boll_k: float = 2.0
    boll_lower_buffer: float = 1.01
    rsi_n: int = 6
    kdj_n: int = 9
    ma_short: int = 20
    ma_long: int = 60


@dataclass(frozen=True)
class T0SignalCandidate:
    code: str
    signal_time: datetime
    signal_price: float
    score: float
    reasons: list[str]

    def to_dict(self) -> dict:
        data = asdict(self)
        data["signal_time"] = self.signal_time.strftime("%Y-%m-%d %H:%M:%S")
        return data


@dataclass(frozen=True)
class T0Trade:
    code: str
    signal_time: datetime
    buy_time: datetime
    buy_price: float
    buy_amount: int
    buy_shares: int
    sell_time: datetime
    sell_price: float
    holding_trade_days: int
    gross_return: float
    net_return: float
    profit_amount: float
    success: bool
    exit_reason: ExitReason
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        data = asdict(self)
        for key in ("signal_time", "buy_time", "sell_time"):
            data[key] = getattr(self, key).strftime("%Y-%m-%d %H:%M:%S")
        return data


@dataclass(frozen=True)
class T0Metrics:
    trade_count: int
    success_count: int
    failure_count: int
    success_rate: float
    average_return: float
    median_return: float
    average_profit_amount: float
    max_single_loss: float
    max_consecutive_failures: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T0Eligibility:
    eligible: bool
    level: EligibilityLevel
    reasons: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class T0StrategyReport:
    code: str
    strategy_name: str
    params: T0StrategyParams
    full_metrics: T0Metrics
    train_metrics: T0Metrics
    validation_metrics: T0Metrics
    recent_metrics: T0Metrics
    recent_trades: list[T0Trade]
    eligibility: T0Eligibility
    generated_at: datetime
    disclaimer: str

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "strategy_name": self.strategy_name,
            "params": asdict(self.params),
            "full_metrics": self.full_metrics.to_dict(),
            "train_metrics": self.train_metrics.to_dict(),
            "validation_metrics": self.validation_metrics.to_dict(),
            "recent_metrics": self.recent_metrics.to_dict(),
            "recent_trades": [trade.to_dict() for trade in self.recent_trades],
            "eligibility": self.eligibility.to_dict(),
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "disclaimer": self.disclaimer,
        }


def amount_to_board_lot_shares(amount: int, price: float) -> int:
    if amount <= 0 or price <= 0:
        return 0
    return int(amount // (price * 100) * 100)
```

- [ ] **Step 4: Run model tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_t0_models.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/t_alpha/strategy/t0_models.py tests/test_t0_models.py
git commit -m "feat: add t0 strategy domain models"
```

---

### Task 2: Parameterized Low-Buy Signal Rules

**Files:**
- Create: `src/t_alpha/strategy/t0_rules.py`
- Create: `tests/test_t0_rules.py`
- Modify: `src/t_alpha/indicators/technical.py` only if an existing indicator bug blocks deterministic tests.

- [ ] **Step 1: Write failing signal rule tests**

Write `tests/test_t0_rules.py`:

```python
import pandas as pd

from t_alpha.strategy.t0_models import T0StrategyParams
from t_alpha.strategy.t0_rules import generate_low_buy_candidates


def _hourly_frame(closes: list[float]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-02 10:00:00", periods=len(closes), freq="60min"),
            "open": closes,
            "high": [price + 0.2 for price in closes],
            "low": [price - 0.2 for price in closes],
            "close": closes,
            "volume": [1000.0] * len(closes),
            "amount": [100000.0] * len(closes),
        }
    )


def _daily_frame(length: int = 80) -> pd.DataFrame:
    closes = [40.0 + idx * 0.02 for idx in range(length)]
    return pd.DataFrame(
        {
            "kline_time": pd.date_range("2023-10-01", periods=length, freq="B"),
            "open": closes,
            "high": [price + 0.3 for price in closes],
            "low": [price - 0.3 for price in closes],
            "close": closes,
            "volume": [500000.0] * length,
            "amount": [20000000.0] * length,
        }
    )


def test_generate_candidate_when_lower_band_and_momentum_turn():
    hourly = _hourly_frame([40.0] * 25 + [39.0, 38.8, 38.9, 39.1, 39.3])
    daily = _daily_frame()
    params = T0StrategyParams()

    candidates = generate_low_buy_candidates("601318.SH", daily, hourly, params)

    assert candidates
    assert candidates[-1].code == "601318.SH"
    assert candidates[-1].score > 0
    assert any("RSI" in reason or "KDJ" in reason or "BOLL" in reason for reason in candidates[-1].reasons)


def test_no_candidate_when_daily_trend_filter_fails():
    hourly = _hourly_frame([40.0] * 25 + [39.0, 38.8, 38.9, 39.1, 39.3])
    daily = _daily_frame()
    daily["close"] = list(reversed(daily["close"].tolist()))

    candidates = generate_low_buy_candidates("601318.SH", daily, hourly, T0StrategyParams())

    assert candidates == []
```

- [ ] **Step 2: Run signal rule tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_t0_rules.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't_alpha.strategy.t0_rules'`.

- [ ] **Step 3: Implement signal rules**

Create `src/t_alpha/strategy/t0_rules.py`:

```python
from __future__ import annotations

import pandas as pd

from t_alpha.indicators.technical import boll, kdj, ma, rsi
from t_alpha.strategy.t0_models import T0SignalCandidate, T0StrategyParams


REQUIRED_COLUMNS = {"kline_time", "open", "high", "low", "close", "volume", "amount"}


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"missing kline columns: {sorted(missing)}")
    prepared = df.copy().sort_values("kline_time").reset_index(drop=True)
    prepared["kline_time"] = pd.to_datetime(prepared["kline_time"])
    for column in ("open", "high", "low", "close", "volume", "amount"):
        prepared[column] = prepared[column].astype(float)
    return prepared


def _daily_trend_passes(daily_df: pd.DataFrame, params: T0StrategyParams) -> bool:
    if len(daily_df) < params.ma_long:
        return False
    close = daily_df["close"].astype(float)
    ma_short_value = ma(close, params.ma_short).iloc[-1]
    ma_long_value = ma(close, params.ma_long).iloc[-1]
    last_close = close.iloc[-1]
    if pd.isna(ma_short_value) or pd.isna(ma_long_value):
        return False
    return bool(ma_short_value > ma_long_value or last_close > ma_long_value)


def generate_low_buy_candidates(
    code: str,
    daily_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    params: T0StrategyParams,
) -> list[T0SignalCandidate]:
    daily = _prepare(daily_df)
    hourly = _prepare(hourly_df)
    if not _daily_trend_passes(daily, params):
        return []
    if len(hourly) < max(params.boll_n, params.kdj_n, params.rsi_n) + 2:
        return []

    close = hourly["close"].astype(float)
    high = hourly["high"].astype(float)
    low = hourly["low"].astype(float)
    boll_values = boll(close, params.boll_n, params.boll_k)
    rsi_values = rsi(close, params.rsi_n)
    kdj_values = kdj(close, high, low, params.kdj_n)

    candidates: list[T0SignalCandidate] = []
    for idx in range(max(params.boll_n, params.kdj_n, params.rsi_n) + 1, len(hourly)):
        reasons: list[str] = []
        last_close = float(close.iloc[idx])
        lower = boll_values["lower"].iloc[idx]
        current_rsi = rsi_values.iloc[idx]
        previous_rsi = rsi_values.iloc[idx - 1]
        current_j = kdj_values["j"].iloc[idx]
        previous_j = kdj_values["j"].iloc[idx - 1]

        touched_lower = pd.notna(lower) and last_close <= float(lower) * params.boll_lower_buffer
        rsi_turn = pd.notna(current_rsi) and pd.notna(previous_rsi) and current_rsi > previous_rsi
        kdj_turn = pd.notna(current_j) and pd.notna(previous_j) and current_j > previous_j

        if touched_lower:
            reasons.append("BOLL lower band touch")
        if rsi_turn:
            reasons.append("RSI turns up")
        if kdj_turn:
            reasons.append("KDJ J turns up")
        if not reasons:
            continue

        score = min(1.0, 0.2 * len(reasons) + max(0.0, (float(lower) - last_close) / last_close if pd.notna(lower) else 0.0))
        candidates.append(
            T0SignalCandidate(
                code=code,
                signal_time=pd.to_datetime(hourly.loc[idx, "kline_time"]).to_pydatetime(),
                signal_price=last_close,
                score=score,
                reasons=reasons,
            )
        )
    return candidates
```

- [ ] **Step 4: Run signal rule tests**

Run:

```powershell
py -3 -m pytest tests/test_t0_rules.py -q
```

Expected: PASS.

- [ ] **Step 5: Run existing indicator and strategy tests**

Run:

```powershell
py -3 -m pytest tests/test_indicators.py tests/test_t0_strategy.py tests/test_t0_rules.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/t_alpha/strategy/t0_rules.py tests/test_t0_rules.py
git commit -m "feat: add parameterized t0 low-buy rules"
```

---

### Task 3: V1 Backtest Engine

**Files:**
- Create: `src/t_alpha/backtest/t0_engine.py`
- Create: `tests/test_t0_engine_v1.py`

- [ ] **Step 1: Write failing backtest tests**

Write `tests/test_t0_engine_v1.py`:

```python
from datetime import datetime

import pandas as pd

from t_alpha.backtest.t0_engine import T0BacktestEngine
from t_alpha.strategy.t0_models import T0SignalCandidate, T0StrategyParams


def _hourly_for_trade() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "kline_time": pd.to_datetime(
                [
                    "2024-01-02 10:00",
                    "2024-01-02 11:00",
                    "2024-01-02 14:00",
                    "2024-01-03 10:00",
                    "2024-01-04 10:00",
                ]
            ),
            "open": [40.0, 40.0, 40.5, 41.1, 40.2],
            "high": [40.2, 41.3, 41.4, 41.5, 40.4],
            "low": [39.8, 39.9, 40.4, 40.9, 39.9],
            "close": [40.0, 40.6, 41.0, 41.2, 40.1],
            "volume": [1000.0] * 5,
            "amount": [40000.0] * 5,
        }
    )


def test_backtest_buys_next_bar_open_and_exits_at_target():
    hourly = _hourly_for_trade()
    candidate = T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 10), 40.0, 1.0, ["test"])
    engine = T0BacktestEngine(T0StrategyParams(target_return=0.03, trade_cost_rate=0.0001))

    trades = engine.run("601318.SH", hourly, [candidate])

    assert len(trades) == 1
    assert trades[0].buy_time == datetime(2024, 1, 2, 11)
    assert trades[0].buy_price == 40.0
    assert trades[0].sell_price == 41.2
    assert trades[0].success is True
    assert trades[0].exit_reason == "target"
    assert round(trades[0].net_return, 4) == 0.0299


def test_backtest_blocks_overlapping_positions():
    hourly = _hourly_for_trade()
    candidates = [
        T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 10), 40.0, 1.0, ["first"]),
        T0SignalCandidate("601318.SH", datetime(2024, 1, 2, 11), 40.6, 1.0, ["overlap"]),
    ]
    engine = T0BacktestEngine(T0StrategyParams())

    trades = engine.run("601318.SH", hourly, candidates)

    assert len(trades) == 1
    assert trades[0].reasons == ["first"]


def test_backtest_times_out_after_max_holding_trade_days():
    hourly = pd.DataFrame(
        {
            "kline_time": pd.date_range("2024-01-02 10:00", periods=20, freq="60min"),
            "open": [40.0] * 20,
            "high": [40.5] * 20,
            "low": [39.5] * 20,
            "close": [40.1] * 20,
            "volume": [1000.0] * 20,
            "amount": [40000.0] * 20,
        }
    )
    candidate = T0SignalCandidate("601318.SH", hourly.loc[0, "kline_time"].to_pydatetime(), 40.0, 1.0, ["test"])
    engine = T0BacktestEngine(T0StrategyParams(max_holding_trade_days=3))

    trades = engine.run("601318.SH", hourly, [candidate])

    assert trades[0].success is False
    assert trades[0].exit_reason == "timeout"
    assert trades[0].holding_trade_days == 3
```

- [ ] **Step 2: Run backtest tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_t0_engine_v1.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't_alpha.backtest.t0_engine'`.

- [ ] **Step 3: Implement V1 backtest engine**

Create `src/t_alpha/backtest/t0_engine.py`:

```python
from __future__ import annotations

import pandas as pd

from t_alpha.strategy.t0_models import (
    T0SignalCandidate,
    T0StrategyParams,
    T0Trade,
    amount_to_board_lot_shares,
)


class T0BacktestEngine:
    def __init__(self, params: T0StrategyParams):
        self.params = params

    def _prepare(self, hourly_df: pd.DataFrame) -> pd.DataFrame:
        df = hourly_df.copy().sort_values("kline_time").reset_index(drop=True)
        df["kline_time"] = pd.to_datetime(df["kline_time"])
        for column in ("open", "high", "low", "close", "volume", "amount"):
            df[column] = df[column].astype(float)
        df["trade_date"] = df["kline_time"].dt.strftime("%Y%m%d").astype(int)
        return df

    def _buy_amount(self, score: float) -> int:
        score = min(1.0, max(0.0, score))
        amount = self.params.min_trade_amount + (self.params.max_trade_amount - self.params.min_trade_amount) * score
        return int(round(amount / 1000) * 1000)

    def run(self, code: str, hourly_df: pd.DataFrame, candidates: list[T0SignalCandidate]) -> list[T0Trade]:
        df = self._prepare(hourly_df)
        if df.empty:
            return []

        index_by_time = {row.kline_time.to_pydatetime(): idx for idx, row in df.iterrows()}
        sorted_candidates = sorted(candidates, key=lambda item: item.signal_time)
        trades: list[T0Trade] = []
        blocked_until_idx = -1

        for candidate in sorted_candidates:
            signal_idx = index_by_time.get(candidate.signal_time)
            if signal_idx is None:
                continue
            buy_idx = signal_idx + 1
            if buy_idx >= len(df) or buy_idx <= blocked_until_idx:
                continue

            buy_row = df.loc[buy_idx]
            buy_price = float(buy_row["open"])
            buy_amount = self._buy_amount(candidate.score)
            buy_shares = amount_to_board_lot_shares(buy_amount, buy_price)
            if buy_shares < 100:
                continue

            target_price = buy_price * (1 + self.params.target_return)
            buy_trade_date = int(buy_row["trade_date"])
            unique_dates = sorted(df.loc[buy_idx:, "trade_date"].unique().tolist())
            max_idx_in_dates = min(self.params.max_holding_trade_days - 1, len(unique_dates) - 1)
            timeout_trade_date = unique_dates[max_idx_in_dates]

            exit_idx = None
            exit_price = None
            success = False
            exit_reason = "timeout"
            holding_trade_days = 1

            for idx in range(buy_idx, len(df)):
                row = df.loc[idx]
                current_date = int(row["trade_date"])
                holding_trade_days = unique_dates.index(current_date) + 1 if current_date in unique_dates else holding_trade_days
                if float(row["high"]) >= target_price:
                    exit_idx = idx
                    exit_price = target_price
                    success = True
                    exit_reason = "target"
                    break
                if current_date >= timeout_trade_date:
                    exit_idx = idx
                    exit_price = float(row["close"])
                    success = False
                    exit_reason = "timeout"
                    break

            if exit_idx is None or exit_price is None:
                continue

            gross_return = exit_price / buy_price - 1
            net_return = gross_return - self.params.trade_cost_rate
            profit_amount = buy_shares * buy_price * net_return
            trades.append(
                T0Trade(
                    code=code,
                    signal_time=candidate.signal_time,
                    buy_time=buy_row["kline_time"].to_pydatetime(),
                    buy_price=round(buy_price, 4),
                    buy_amount=buy_amount,
                    buy_shares=buy_shares,
                    sell_time=df.loc[exit_idx, "kline_time"].to_pydatetime(),
                    sell_price=round(exit_price, 4),
                    holding_trade_days=holding_trade_days,
                    gross_return=gross_return,
                    net_return=net_return,
                    profit_amount=profit_amount,
                    success=success,
                    exit_reason=exit_reason,
                    reasons=candidate.reasons,
                )
            )
            blocked_until_idx = exit_idx

        return trades
```

- [ ] **Step 4: Run backtest tests**

Run:

```powershell
py -3 -m pytest tests/test_t0_engine_v1.py -q
```

Expected: PASS.

- [ ] **Step 5: Run existing backtest tests**

Run:

```powershell
py -3 -m pytest tests/test_backtest_engine.py tests/test_t0_engine_v1.py -q
```

Expected: PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/t_alpha/backtest/t0_engine.py tests/test_t0_engine_v1.py
git commit -m "feat: add v1 t0 backtest engine"
```

---

### Task 4: T0 Metrics, Eligibility, and Optimizer

**Files:**
- Create: `src/t_alpha/backtest/t0_optimizer.py`
- Create: `tests/test_t0_optimizer.py`
- Modify: `src/t_alpha/backtest/metrics.py` only if shared helper extraction is cleaner after tests pass.

- [ ] **Step 1: Write failing optimizer tests**

Write `tests/test_t0_optimizer.py`:

```python
from datetime import datetime, timedelta

from t_alpha.backtest.t0_optimizer import evaluate_eligibility, summarize_t0_trades
from t_alpha.strategy.t0_models import T0StrategyParams, T0Trade


def _trade(idx: int, success: bool, net_return: float) -> T0Trade:
    base = datetime(2024, 1, 2) + timedelta(days=idx)
    return T0Trade(
        code="601318.SH",
        signal_time=base,
        buy_time=base,
        buy_price=40.0,
        buy_amount=10000,
        buy_shares=200,
        sell_time=base + timedelta(days=1),
        sell_price=41.2 if success else 39.8,
        holding_trade_days=2,
        gross_return=0.03 if success else -0.005,
        net_return=net_return,
        profit_amount=80.0 if success else -40.0,
        success=success,
        exit_reason="target" if success else "timeout",
        reasons=["test"],
    )


def test_summarize_t0_trades_counts_success_and_failure_streak():
    trades = [_trade(0, True, 0.03), _trade(1, False, -0.01), _trade(2, False, -0.02)]

    metrics = summarize_t0_trades(trades)

    assert metrics.trade_count == 3
    assert metrics.success_count == 1
    assert metrics.failure_count == 2
    assert metrics.max_consecutive_failures == 2
    assert metrics.max_single_loss == -0.02


def test_eligibility_requires_sixty_trades_and_positive_average_return():
    params = T0StrategyParams()
    full_metrics = summarize_t0_trades([_trade(i, True, 0.03) for i in range(60)])
    validation_metrics = summarize_t0_trades([_trade(i, True, 0.03) for i in range(20)])
    recent_metrics = summarize_t0_trades([_trade(i, True, 0.03) for i in range(3)])

    eligibility = evaluate_eligibility(full_metrics, validation_metrics, recent_metrics, params)

    assert eligibility.eligible is True
    assert eligibility.level == "eligible"


def test_eligibility_marks_observe_when_trade_count_between_30_and_59():
    params = T0StrategyParams()
    full_metrics = summarize_t0_trades([_trade(i, True, 0.03) for i in range(40)])
    validation_metrics = summarize_t0_trades([_trade(i, True, 0.03) for i in range(15)])
    recent_metrics = summarize_t0_trades([])

    eligibility = evaluate_eligibility(full_metrics, validation_metrics, recent_metrics, params)

    assert eligibility.eligible is False
    assert eligibility.level == "observe"
    assert "仅作为观察策略" in eligibility.reasons[0]
```

- [ ] **Step 2: Run optimizer tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_t0_optimizer.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't_alpha.backtest.t0_optimizer'`.

- [ ] **Step 3: Implement metrics and eligibility helpers**

Create `src/t_alpha/backtest/t0_optimizer.py` with the metrics and eligibility portion first:

```python
from __future__ import annotations

from dataclasses import replace
from datetime import datetime

import numpy as np
import pandas as pd

from t_alpha.backtest.t0_engine import T0BacktestEngine
from t_alpha.strategy.t0_models import T0Eligibility, T0Metrics, T0StrategyParams, T0StrategyReport, T0Trade
from t_alpha.strategy.t0_rules import generate_low_buy_candidates
from t_alpha.constants import DISCLAIMER
from t_alpha.storage.repository import DEFAULT_STRATEGY


def summarize_t0_trades(trades: list[T0Trade]) -> T0Metrics:
    if not trades:
        return T0Metrics(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0)

    returns = np.array([trade.net_return for trade in trades], dtype=float)
    profits = np.array([trade.profit_amount for trade in trades], dtype=float)
    successes = np.array([trade.success for trade in trades], dtype=bool)
    max_failure_streak = 0
    current_failure_streak = 0
    for success in successes:
        if success:
            current_failure_streak = 0
        else:
            current_failure_streak += 1
            max_failure_streak = max(max_failure_streak, current_failure_streak)

    success_count = int(successes.sum())
    failure_count = int(len(trades) - success_count)
    return T0Metrics(
        trade_count=len(trades),
        success_count=success_count,
        failure_count=failure_count,
        success_rate=float(success_count / len(trades)),
        average_return=float(returns.mean()),
        median_return=float(np.median(returns)),
        average_profit_amount=float(profits.mean()),
        max_single_loss=float(returns.min()),
        max_consecutive_failures=max_failure_streak,
    )


def evaluate_eligibility(
    full_metrics: T0Metrics,
    validation_metrics: T0Metrics,
    recent_metrics: T0Metrics,
    params: T0StrategyParams,
) -> T0Eligibility:
    reasons: list[str] = []
    if full_metrics.trade_count < params.observe_min_3y_trades:
        return T0Eligibility(False, "invalid", ["3年有效交易数不足30笔，策略无效"])
    if full_metrics.trade_count < params.min_3y_trades:
        return T0Eligibility(False, "observe", ["3年有效交易数为30到59笔，仅作为观察策略"])
    if full_metrics.success_rate <= params.min_success_rate:
        reasons.append("3年做T成功率未超过50%")
    if validation_metrics.success_rate <= params.min_success_rate:
        reasons.append("验证集成功率未超过50%")
    if full_metrics.average_return <= 0:
        reasons.append("扣成本后平均单笔收益不为正")
    if recent_metrics.trade_count and recent_metrics.success_rate <= params.min_success_rate:
        reasons.append("最近3个月成功率未超过50%")
    if recent_metrics.trade_count < 3:
        reasons.append("最近3个月样本不足，只能观察近期健康度")

    if reasons and any(reason != "最近3个月样本不足，只能观察近期健康度" for reason in reasons):
        return T0Eligibility(False, "invalid", reasons)
    return T0Eligibility(True, "eligible", reasons)
```

- [ ] **Step 4: Run optimizer helper tests**

Run:

```powershell
py -3 -m pytest tests/test_t0_optimizer.py -q
```

Expected: PASS.

- [ ] **Step 5: Add optimizer report test**

Append to `tests/test_t0_optimizer.py`:

```python
def test_optimizer_selects_best_params_by_success_rate(monkeypatch):
    import t_alpha.backtest.t0_optimizer as optimizer

    params_grid = [
        T0StrategyParams(target_return=0.03, boll_lower_buffer=1.00),
        T0StrategyParams(target_return=0.03, boll_lower_buffer=1.02),
    ]

    def fake_candidates(code, daily_df, hourly_df, params):
        return []

    class FakeEngine:
        def __init__(self, params):
            self.params = params

        def run(self, code, hourly_df, candidates):
            count = 65
            success = self.params.boll_lower_buffer == 1.02
            return [_trade(i, success, 0.03 if success else -0.01) for i in range(count)]

    monkeypatch.setattr(optimizer, "generate_low_buy_candidates", fake_candidates)
    monkeypatch.setattr(optimizer, "T0BacktestEngine", FakeEngine)

    daily = __import__("pandas").DataFrame({"kline_time": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "amount": []})
    hourly = daily.copy()
    report = optimizer.optimize_t0_strategy("601318.SH", daily, hourly, params_grid)

    assert report.params.boll_lower_buffer == 1.02
    assert report.full_metrics.success_rate == 1.0
```

- [ ] **Step 6: Implement optimizer report selection**

Append to `src/t_alpha/backtest/t0_optimizer.py`:

```python
def _split_by_recent_months(df: pd.DataFrame, recent_months: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()
    prepared = df.copy().sort_values("kline_time").reset_index(drop=True)
    prepared["kline_time"] = pd.to_datetime(prepared["kline_time"])
    cutoff = prepared["kline_time"].max() - pd.DateOffset(months=recent_months)
    history = prepared[prepared["kline_time"] < cutoff].reset_index(drop=True)
    recent = prepared[prepared["kline_time"] >= cutoff].reset_index(drop=True)
    return history, recent


def _split_train_validation(df: pd.DataFrame, train_ratio: float = 0.70) -> tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()
    split_idx = max(1, int(len(df) * train_ratio))
    return df.iloc[:split_idx].reset_index(drop=True), df.iloc[split_idx:].reset_index(drop=True)


def _score_report(full_metrics: T0Metrics, validation_metrics: T0Metrics) -> tuple[float, float, float, int]:
    return (
        full_metrics.success_rate,
        full_metrics.average_return,
        validation_metrics.success_rate,
        -full_metrics.max_consecutive_failures,
    )


def _run_with_params(code: str, daily_df: pd.DataFrame, hourly_df: pd.DataFrame, params: T0StrategyParams) -> list[T0Trade]:
    candidates = generate_low_buy_candidates(code, daily_df, hourly_df, params)
    return T0BacktestEngine(params).run(code, hourly_df, candidates)


def default_param_grid(base: T0StrategyParams | None = None) -> list[T0StrategyParams]:
    base_params = base or T0StrategyParams()
    grid: list[T0StrategyParams] = []
    for boll_lower_buffer in (1.00, 1.01, 1.02):
        for target_return in (0.03,):
            grid.append(replace(base_params, boll_lower_buffer=boll_lower_buffer, target_return=target_return))
    return grid


def optimize_t0_strategy(
    code: str,
    daily_df: pd.DataFrame,
    hourly_df: pd.DataFrame,
    params_grid: list[T0StrategyParams] | None = None,
) -> T0StrategyReport:
    candidates_grid = params_grid or default_param_grid()
    history_hourly, recent_hourly = _split_by_recent_months(hourly_df)
    train_hourly, validation_hourly = _split_train_validation(history_hourly)

    best: tuple[tuple[float, float, float, int], T0StrategyParams, list[T0Trade], list[T0Trade]] | None = None
    for params in candidates_grid:
        train_trades = _run_with_params(code, daily_df, train_hourly, params)
        validation_trades = _run_with_params(code, daily_df, validation_hourly, params)
        train_metrics = summarize_t0_trades(train_trades)
        validation_metrics = summarize_t0_trades(validation_trades)
        score = _score_report(train_metrics, validation_metrics)
        if best is None or score > best[0]:
            best = (score, params, train_trades, validation_trades)

    if best is None:
        best_params = T0StrategyParams()
        train_trades = []
        validation_trades = []
    else:
        best_params = best[1]
        train_trades = best[2]
        validation_trades = best[3]

    full_trades = _run_with_params(code, daily_df, hourly_df, best_params)
    recent_trades = _run_with_params(code, daily_df, recent_hourly, best_params)
    full_metrics = summarize_t0_trades(full_trades)
    train_metrics = summarize_t0_trades(train_trades)
    validation_metrics = summarize_t0_trades(validation_trades)
    recent_metrics = summarize_t0_trades(recent_trades)
    eligibility = evaluate_eligibility(full_metrics, validation_metrics, recent_metrics, best_params)

    return T0StrategyReport(
        code=code,
        strategy_name=DEFAULT_STRATEGY,
        params=best_params,
        full_metrics=full_metrics,
        train_metrics=train_metrics,
        validation_metrics=validation_metrics,
        recent_metrics=recent_metrics,
        recent_trades=recent_trades,
        eligibility=eligibility,
        generated_at=datetime.utcnow(),
        disclaimer=DISCLAIMER,
    )
```

- [ ] **Step 7: Run optimizer tests**

Run:

```powershell
py -3 -m pytest tests/test_t0_optimizer.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/t_alpha/backtest/t0_optimizer.py tests/test_t0_optimizer.py
git commit -m "feat: add t0 optimizer and eligibility gates"
```

---

### Task 5: Strategy Service and Market Data Fetching

**Files:**
- Modify: `src/t_alpha/storage/repository.py`
- Modify: `tests/test_storage.py`
- Create: `src/t_alpha/services_strategy.py`
- Create: `tests/test_strategy_service.py`
- Modify: `src/t_alpha/config.py`

- [ ] **Step 1: Add failing storage tests for report and monitor persistence**

Append to `tests/test_storage.py`:

```python
from t_alpha.storage.models import StrategyBacktest
from t_alpha.storage.repository import enable_t0_monitor, save_strategy_report


def test_save_strategy_report_persists_backtest(session):
    save_strategy_report(
        session,
        code="601318.SH",
        strategy_name="mean_reversion_t0_v1",
        start_date="20230101",
        end_date="20260101",
        params_json='{"target_return": 0.03}',
        metrics_json='{"eligible": true}',
        report_path="",
    )

    row = session.query(StrategyBacktest).filter_by(code="601318.SH").one()

    assert row.metrics_json == '{"eligible": true}'


def test_enable_t0_monitor_seeds_enabled_watchlist(session):
    row = enable_t0_monitor(session, "601318.SH", "mean_reversion_t0_v1")

    assert row.enabled is True
    assert row.code == "601318.SH"
```

- [ ] **Step 2: Run storage tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_storage.py -q
```

Expected: FAIL because `save_strategy_report` and `enable_t0_monitor` are not defined.

- [ ] **Step 3: Implement repository helpers**

Modify `src/t_alpha/storage/repository.py`:

```python
from t_alpha.storage.models import StrategyBacktest, Watchlist
```

Add:

```python
def save_strategy_report(
    session: Session,
    code: str,
    strategy_name: str,
    start_date: str,
    end_date: str,
    params_json: str,
    metrics_json: str,
    report_path: str = "",
) -> StrategyBacktest:
    row = StrategyBacktest(
        code=code,
        strategy_name=strategy_name,
        start_date=start_date,
        end_date=end_date,
        params_json=params_json,
        metrics_json=metrics_json,
        report_path=report_path,
    )
    session.add(row)
    session.flush()
    return row


def enable_t0_monitor(session: Session, code: str, strategy_name: str) -> Watchlist:
    stmt = select(Watchlist).where(Watchlist.code == code, Watchlist.strategy_name == strategy_name)
    existing = session.execute(stmt).scalar_one_or_none()
    if existing is not None:
        existing.enabled = True
        session.flush()
        return existing

    row = Watchlist(code=code, name="", enabled=True, strategy_name=strategy_name, note="T0 v1 monitor enabled")
    session.add(row)
    session.flush()
    return row
```

- [ ] **Step 4: Run storage tests**

Run:

```powershell
py -3 -m pytest tests/test_storage.py -q
```

Expected: PASS.

- [ ] **Step 5: Write failing service tests**

Write `tests/test_strategy_service.py`:

```python
import pandas as pd

from t_alpha.services_strategy import T0StrategyService


class FakeClient:
    class FakeAd:
        class constant:
            class Period:
                class day:
                    value = 1
                class min60:
                    value = 2

    ad = FakeAd()

    def get_calendar(self):
        return [20240102, 20240103, 20240104, 20240105]

    def query_kline(self, code, begin_date, end_date, period_value):
        frame = pd.DataFrame(
            {
                "kline_time": pd.date_range("2024-01-02", periods=80, freq="60min"),
                "open": [40.0] * 80,
                "high": [41.5] * 80,
                "low": [39.5] * 80,
                "close": [40.0] * 80,
                "volume": [1000.0] * 80,
                "amount": [40000.0] * 80,
            }
        )
        return {code: frame}

    def get_backward_factor(self, code):
        return {}


def test_build_report_persists_report(monkeypatch):
    import t_alpha.services_strategy as module

    saved = {}
    service = T0StrategyService(FakeClient(), session=object())

    def fake_optimize(code, daily_df, hourly_df):
        from datetime import datetime
        from t_alpha.strategy.t0_models import T0Eligibility, T0Metrics, T0StrategyParams, T0StrategyReport
        metrics = T0Metrics(60, 31, 29, 31 / 60, 0.01, 0.01, 100.0, -0.02, 3)
        return T0StrategyReport(
            code=code,
            strategy_name="mean_reversion_t0_v1",
            params=T0StrategyParams(),
            full_metrics=metrics,
            train_metrics=metrics,
            validation_metrics=metrics,
            recent_metrics=metrics,
            recent_trades=[],
            eligibility=T0Eligibility(True, "eligible", []),
            generated_at=datetime(2024, 1, 1),
            disclaimer="仅供研究参考，不构成投资建议。",
        )

    monkeypatch.setattr(module, "optimize_t0_strategy", fake_optimize)

    def fake_save_strategy_report(session, code, strategy_name, start_date, end_date, params_json, metrics_json, report_path):
        saved["code"] = code
        saved["strategy_name"] = strategy_name
        saved["start_date"] = start_date
        saved["end_date"] = end_date
        saved["params_json"] = params_json
        saved["metrics_json"] = metrics_json

    monkeypatch.setattr(module, "save_strategy_report", fake_save_strategy_report)

    report = service.build_report("601318.SH")

    assert report.code == "601318.SH"
    assert saved["code"] == "601318.SH"
    assert saved["start_date"] == "20240102"


def test_enable_monitor_requires_eligible_report(monkeypatch):
    import t_alpha.services_strategy as module

    monitored = []
    service = T0StrategyService(FakeClient(), session=object())

    def fake_enable_t0_monitor(session, code, strategy_name):
        monitored.append((code, strategy_name))

    monkeypatch.setattr(module, "enable_t0_monitor", fake_enable_t0_monitor)

    service.enable_monitor("601318.SH", eligible=True)

    assert monitored == [("601318.SH", "mean_reversion_t0_v1")]
```

- [ ] **Step 6: Run service tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_strategy_service.py -q
```

Expected: FAIL with `ModuleNotFoundError: No module named 't_alpha.services_strategy'`.

- [ ] **Step 7: Add configurable settings**

Modify `src/t_alpha/config.py` inside `Settings`:

```python
    t0_target_return: float = Field(default=0.03, alias="T0_TARGET_RETURN")
    t0_max_holding_trade_days: int = Field(default=10, alias="T0_MAX_HOLDING_TRADE_DAYS")
    t0_trade_cost_rate: float = Field(default=0.0001, alias="T0_TRADE_COST_RATE")
    t0_min_3y_trades: int = Field(default=60, alias="T0_MIN_3Y_TRADES")
    t0_observe_min_3y_trades: int = Field(default=30, alias="T0_OBSERVE_MIN_3Y_TRADES")
```

- [ ] **Step 8: Implement strategy service**

Create `src/t_alpha/services_strategy.py`:

```python
from __future__ import annotations

import json
from datetime import datetime

from fastapi import HTTPException

from t_alpha.backtest.t0_optimizer import optimize_t0_strategy
from t_alpha.constants import ASSET_STOCK
from t_alpha.data.adjust import forward_adjust
from t_alpha.data.calendar import previous_n_trade_days
from t_alpha.data.market_data import period_to_ad_value
from t_alpha.storage.repository import DEFAULT_STRATEGY, enable_t0_monitor, save_strategy_report


class T0StrategyService:
    def __init__(self, client, session):
        self.client = client
        self.session = session

    def _date_window(self) -> tuple[int, int]:
        calendar = self.client.get_calendar()
        if not calendar:
            raise HTTPException(status_code=400, detail="calendar is empty")
        return previous_n_trade_days(calendar, calendar[-1], 756)

    def _query_forward_kline(self, code: str, begin_date: int, end_date: int, period: str):
        period_value = period_to_ad_value(self.client.ad, period)
        kline_dict = self.client.query_kline(code, begin_date, end_date, period_value)
        df = kline_dict.get(code)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"no {period} data returned for {code}")
        if period == "day":
            return forward_adjust(df, self.client.get_backward_factor(code), code)
        return df

    def build_report(self, code: str):
        begin_date, end_date = self._date_window()
        daily_df = self._query_forward_kline(code, begin_date, end_date, "day")
        hourly_df = self._query_forward_kline(code, begin_date, end_date, "60m")
        report = optimize_t0_strategy(code, daily_df, hourly_df)
        payload = report.to_dict()
        save_strategy_report(
            self.session,
            code=code,
            strategy_name=DEFAULT_STRATEGY,
            start_date=str(begin_date),
            end_date=str(end_date),
            params_json=json.dumps(payload["params"], ensure_ascii=False),
            metrics_json=json.dumps(payload, ensure_ascii=False),
            report_path="",
        )
        return report

    def enable_monitor(self, code: str, eligible: bool):
        if not eligible:
            raise HTTPException(status_code=400, detail="strategy is not eligible for monitoring")
        enable_t0_monitor(self.session, code, DEFAULT_STRATEGY)
        return {"code": code, "strategy_name": DEFAULT_STRATEGY, "enabled": True, "enabled_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")}
```

- [ ] **Step 9: Run service tests**

Run:

```powershell
py -3 -m pytest tests/test_strategy_service.py tests/test_config.py -q
```

Expected: PASS.

- [ ] **Step 10: Commit**

```powershell
git add src/t_alpha/storage/repository.py tests/test_storage.py src/t_alpha/services_strategy.py src/t_alpha/config.py tests/test_strategy_service.py
git commit -m "feat: add t0 strategy service"
```

---

### Task 6: Build and Monitor API Endpoints

**Files:**
- Modify: `src/t_alpha/api/schemas.py`
- Modify: `src/t_alpha/api/deps.py`
- Modify: `src/t_alpha/api/routes_strategy.py`
- Create: `tests/test_strategy_api.py`

- [ ] **Step 1: Write failing API tests**

Write `tests/test_strategy_api.py`:

```python
from datetime import datetime

from fastapi.testclient import TestClient

from t_alpha.api.deps import get_strategy_service
from t_alpha.main import app
from t_alpha.strategy.t0_models import T0Eligibility, T0Metrics, T0StrategyParams, T0StrategyReport


class FakeStrategyService:
    def build_report(self, code):
        metrics = T0Metrics(60, 31, 29, 31 / 60, 0.01, 0.01, 100.0, -0.02, 3)
        return T0StrategyReport(
            code=code,
            strategy_name="mean_reversion_t0_v1",
            params=T0StrategyParams(),
            full_metrics=metrics,
            train_metrics=metrics,
            validation_metrics=metrics,
            recent_metrics=metrics,
            recent_trades=[],
            eligibility=T0Eligibility(True, "eligible", []),
            generated_at=datetime(2024, 1, 1),
            disclaimer="仅供研究参考，不构成投资建议。",
        )

    def enable_monitor(self, code, eligible):
        return {"code": code, "strategy_name": "mean_reversion_t0_v1", "enabled": True, "enabled_at": "2024-01-01 00:00:00"}


def setup_module():
    app.dependency_overrides[get_strategy_service] = lambda: FakeStrategyService()


def teardown_module():
    app.dependency_overrides.clear()


def test_t0_build_endpoint_returns_report():
    client = TestClient(app)
    response = client.post("/api/v1/strategy/t0/build", json={"code": "601318.SH"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == "601318.SH"
    assert payload["eligibility"]["eligible"] is True
    assert payload["full_metrics"]["trade_count"] == 60


def test_t0_monitor_endpoint_enables_monitor():
    client = TestClient(app)
    response = client.post("/api/v1/strategy/t0/monitor", json={"code": "601318.SH", "eligible": True})

    assert response.status_code == 200
    assert response.json()["enabled"] is True
```

- [ ] **Step 2: Run API tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_strategy_api.py -q
```

Expected: FAIL because `get_strategy_service` and endpoints do not exist.

- [ ] **Step 3: Add schemas**

Append to `src/t_alpha/api/schemas.py`:

```python
from typing import Any


class T0BuildRequest(BaseModel):
    code: str


class T0MonitorRequest(BaseModel):
    code: str
    eligible: bool = True


class T0MonitorResponse(BaseModel):
    code: str
    strategy_name: str
    enabled: bool
    enabled_at: str


class T0BuildResponse(BaseModel):
    code: str
    strategy_name: str
    params: dict[str, Any]
    full_metrics: dict[str, Any]
    train_metrics: dict[str, Any]
    validation_metrics: dict[str, Any]
    recent_metrics: dict[str, Any]
    recent_trades: list[dict[str, Any]]
    eligibility: dict[str, Any]
    generated_at: str
    disclaimer: str = Field(default=DISCLAIMER)
```

- [ ] **Step 4: Add service dependency**

Modify `src/t_alpha/api/deps.py`:

```python
from sqlalchemy.orm import Session

from t_alpha.services_strategy import T0StrategyService
from t_alpha.storage.database import get_session
```

Add:

```python
def get_strategy_service(session: Session = Depends(get_session)) -> T0StrategyService:
    return T0StrategyService(get_amazingdata_client(), session)
```

If `Depends` is not imported in `deps.py`, import it:

```python
from fastapi import Depends
```

- [ ] **Step 5: Add routes**

Modify `src/t_alpha/api/routes_strategy.py`:

```python
from fastapi import APIRouter, Depends

from t_alpha.api.deps import get_strategy_service
from t_alpha.api.schemas import T0BuildRequest, T0BuildResponse, T0MonitorRequest, T0MonitorResponse
from t_alpha.services_strategy import T0StrategyService
```

Add:

```python
@router.post("/t0/build", response_model=T0BuildResponse)
def build_t0_strategy(request: T0BuildRequest, service: T0StrategyService = Depends(get_strategy_service)):
    report = service.build_report(request.code)
    return T0BuildResponse.model_validate(report.to_dict())


@router.post("/t0/monitor", response_model=T0MonitorResponse)
def monitor_t0_strategy(request: T0MonitorRequest, service: T0StrategyService = Depends(get_strategy_service)):
    return T0MonitorResponse.model_validate(service.enable_monitor(request.code, request.eligible))
```

- [ ] **Step 6: Run API tests**

Run:

```powershell
py -3 -m pytest tests/test_strategy_api.py tests/test_market_api.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit**

```powershell
git add src/t_alpha/api/schemas.py src/t_alpha/api/deps.py src/t_alpha/api/routes_strategy.py tests/test_strategy_api.py
git commit -m "feat: expose t0 build and monitor endpoints"
```

---

### Task 7: Monitoring and Email Content

**Files:**
- Modify: `src/t_alpha/storage/models.py`
- Modify: `src/t_alpha/storage/repository.py`
- Modify: `src/t_alpha/services_strategy.py`
- Modify: `src/t_alpha/scheduler/jobs.py`
- Modify: `src/t_alpha/notification/email_sender.py`
- Modify: `tests/test_storage.py`
- Modify: `tests/test_strategy_service.py`
- Modify: `tests/test_scheduler.py`
- Modify: `tests/test_email_sender.py`

- [ ] **Step 1: Add failing storage tests for open T0 position**

Append to `tests/test_storage.py`:

```python
from t_alpha.storage.repository import get_open_t0_position, open_t0_position


def test_open_t0_position_blocks_duplicate_buy_alerts(session):
    open_t0_position(
        session,
        code="601318.SH",
        strategy_name="mean_reversion_t0_v1",
        payload_json='{"buy_price": 40.0}',
    )

    row = get_open_t0_position(session, "601318.SH", "mean_reversion_t0_v1")

    assert row is not None
    assert row.code == "601318.SH"
    assert row.status == "open"
```

- [ ] **Step 2: Implement open-position model and repository helpers**

Append to `src/t_alpha/storage/models.py`:

```python
class T0Position(Base):
    __tablename__ = "t0_positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    strategy_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="open")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

Modify `src/t_alpha/storage/repository.py` imports:

```python
from t_alpha.storage.models import StrategyBacktest, T0Position, Watchlist
```

Append:

```python
def get_open_t0_position(session: Session, code: str, strategy_name: str) -> T0Position | None:
    stmt = select(T0Position).where(
        T0Position.code == code,
        T0Position.strategy_name == strategy_name,
        T0Position.status == "open",
    )
    return session.execute(stmt).scalar_one_or_none()


def open_t0_position(session: Session, code: str, strategy_name: str, payload_json: str) -> T0Position:
    existing = get_open_t0_position(session, code, strategy_name)
    if existing is not None:
        return existing
    row = T0Position(code=code, strategy_name=strategy_name, status="open", payload_json=payload_json)
    session.add(row)
    session.flush()
    return row
```

- [ ] **Step 3: Run storage open-position test**

Run:

```powershell
py -3 -m pytest tests/test_storage.py::test_open_t0_position_blocks_duplicate_buy_alerts -q
```

Expected: PASS.

- [ ] **Step 4: Add failing service test for monitor contract**

Append to `tests/test_strategy_service.py`:

```python
def test_monitor_contract_methods_exist():
    service = T0StrategyService(FakeClient(), session=object())

    assert hasattr(service, "list_enabled_t0_codes")
    assert hasattr(service, "has_open_t0_position")
    assert hasattr(service, "generate_realtime_signal")
    assert hasattr(service, "mark_position_open")
```

- [ ] **Step 5: Implement monitor contract methods**

Append to `T0StrategyService` in `src/t_alpha/services_strategy.py`:

```python
    def list_enabled_t0_codes(self) -> list[str]:
        from t_alpha.storage.repository import list_enabled_watchlist

        return [item.code for item in list_enabled_watchlist(self.session) if item.strategy_name == DEFAULT_STRATEGY]

    def has_open_t0_position(self, code: str) -> bool:
        from t_alpha.storage.repository import get_open_t0_position

        return get_open_t0_position(self.session, code, DEFAULT_STRATEGY) is not None

    def generate_realtime_signal(self, code: str, now: datetime) -> dict | None:
        report = self.build_report(code)
        if not report.eligibility.eligible:
            return None
        begin_date, end_date = self._date_window()
        daily_df = self._query_forward_kline(code, begin_date, end_date, "day")
        hourly_df = self._query_forward_kline(code, begin_date, end_date, "60m")
        from t_alpha.strategy.t0_models import amount_to_board_lot_shares
        from t_alpha.strategy.t0_rules import generate_low_buy_candidates

        candidates = generate_low_buy_candidates(code, daily_df, hourly_df, report.params)
        if not candidates:
            return None
        latest_candidate = candidates[-1]
        if latest_candidate.signal_time.date() != now.date():
            return None
        suggested_amount = int(round((report.params.min_trade_amount + (report.params.max_trade_amount - report.params.min_trade_amount) * latest_candidate.score) / 1000) * 1000)
        suggested_shares = amount_to_board_lot_shares(suggested_amount, latest_candidate.signal_price)
        if suggested_shares < 100:
            return None
        return {
            "code": code,
            "signal_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": latest_candidate.signal_price,
            "suggested_buy_zone": [round(latest_candidate.signal_price * 0.995, 3), round(latest_candidate.signal_price * 1.002, 3)],
            "suggested_amount": suggested_amount,
            "suggested_shares": suggested_shares,
            "target_sell_price": round(latest_candidate.signal_price * (1 + report.params.target_return), 3),
            "max_holding_trade_days": report.params.max_holding_trade_days,
            "full_success_rate": report.full_metrics.success_rate,
            "full_trade_count": report.full_metrics.trade_count,
            "recent_success_rate": report.recent_metrics.success_rate,
            "recent_trade_count": report.recent_metrics.trade_count,
            "reasons": latest_candidate.reasons,
        }

    def mark_position_open(self, code: str, payload: dict) -> None:
        import json
        from t_alpha.storage.repository import open_t0_position

        open_t0_position(self.session, code, DEFAULT_STRATEGY, json.dumps(payload, ensure_ascii=False))
```

- [ ] **Step 6: Run service monitor contract test**

Run:

```powershell
py -3 -m pytest tests/test_strategy_service.py::test_monitor_contract_methods_exist -q
```

Expected: PASS.

- [ ] **Step 7: Add failing scheduler test for no-overlap monitor behavior**

Append to `tests/test_scheduler.py`:

```python
from datetime import datetime

from t_alpha.scheduler.jobs import T0MonitorJob


class FakeMonitorService:
    def __init__(self):
        self.sent = []

    def list_enabled_t0_codes(self):
        return ["601318.SH"]

    def has_open_t0_position(self, code):
        return False

    def generate_realtime_signal(self, code, now):
        return {"code": code, "signal_time": "2024-01-02 10:00:00", "target_return": 0.03}

    def mark_position_open(self, code, payload):
        self.sent.append((code, payload))


class FakeEmailSender:
    def __init__(self):
        self.messages = []

    def send_t0_signal(self, payload):
        self.messages.append(payload)


def test_t0_monitor_job_sends_signal_and_marks_open_position():
    service = FakeMonitorService()
    sender = FakeEmailSender()
    job = T0MonitorJob(lambda: [20240102], service, sender)

    sent_count = job.run_once(datetime(2024, 1, 2, 10, 0))

    assert sent_count == 1
    assert sender.messages[0]["code"] == "601318.SH"
    assert service.sent[0][0] == "601318.SH"
```

- [ ] **Step 8: Run scheduler test to verify it fails**

Run:

```powershell
py -3 -m pytest tests/test_scheduler.py -q
```

Expected: FAIL because `T0MonitorJob` does not exist.

- [ ] **Step 9: Implement monitor job**

Append to `src/t_alpha/scheduler/jobs.py`:

```python
class T0MonitorJob:
    def __init__(self, calendar_provider, monitor_service, email_sender):
        self.calendar_provider = calendar_provider
        self.monitor_service = monitor_service
        self.email_sender = email_sender

    def run_once(self, now: datetime) -> int:
        if not is_trade_day(self.calendar_provider(), now) or not is_alert_check_time(now):
            return 0

        sent_count = 0
        for code in self.monitor_service.list_enabled_t0_codes():
            if self.monitor_service.has_open_t0_position(code):
                continue
            payload = self.monitor_service.generate_realtime_signal(code, now)
            if payload is None:
                continue
            self.email_sender.send_t0_signal(payload)
            self.monitor_service.mark_position_open(code, payload)
            sent_count += 1
        return sent_count
```

- [ ] **Step 10: Add failing email content test**

Append to `tests/test_email_sender.py`:

```python
from t_alpha.notification.email_sender import build_t0_alert_email


def test_build_t0_alert_email_contains_recent_summary():
    payload = {
        "code": "601318.SH",
        "signal_time": "2024-01-02 10:00:00",
        "current_price": 40.0,
        "suggested_buy_zone": [39.8, 40.1],
        "suggested_amount": 12000,
        "suggested_shares": 300,
        "target_sell_price": 41.2,
        "max_holding_trade_days": 10,
        "full_success_rate": 0.55,
        "full_trade_count": 60,
        "recent_success_rate": 0.60,
        "recent_trade_count": 5,
        "reasons": ["BOLL lower band touch"],
    }

    subject, body = build_t0_alert_email(payload)

    assert "[做T提醒]" in subject
    assert "目标卖出价: 41.2" in body
    assert "最近3个月成功率: 60.00%" in body
```

- [ ] **Step 11: Implement email builder**

Append to `src/t_alpha/notification/email_sender.py`:

```python
def build_t0_alert_email(payload: dict) -> tuple[str, str]:
    subject = (
        f"[做T提醒] {payload['code']} 出现候选买点 "
        f"3年成功率{payload['full_success_rate']:.2%} 目标收益3%"
    )
    body = "\n".join(
        [
            f"股票代码: {payload['code']}",
            f"信号时间: {payload['signal_time']}",
            f"当前价格: {payload['current_price']}",
            f"建议关注买入区间: {payload['suggested_buy_zone'][0]} - {payload['suggested_buy_zone'][1]}",
            f"建议买入金额: {payload['suggested_amount']}",
            f"建议买入股数: {payload['suggested_shares']}",
            f"目标卖出价: {payload['target_sell_price']}",
            f"最长持仓交易日: {payload['max_holding_trade_days']}",
            f"3年有效交易数: {payload['full_trade_count']}",
            f"3年成功率: {payload['full_success_rate']:.2%}",
            f"最近3个月交易数: {payload['recent_trade_count']}",
            f"最近3个月成功率: {payload['recent_success_rate']:.2%}",
            f"触发原因: {'; '.join(payload['reasons'])}",
            "风险提示: 仅供研究参考，不构成投资建议。历史回测不代表未来表现。",
        ]
    )
    return subject, body
```

Add method to `EmailSender`:

```python
    def send_t0_signal(self, payload: dict) -> None:
        subject, body = build_t0_alert_email(payload)
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = self.settings.smtp_from
        message["To"] = self.settings.alert_to
        message.set_content(body)

        with smtplib.SMTP_SSL(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(message)
```

- [ ] **Step 12: Run scheduler and email tests**

Run:

```powershell
py -3 -m pytest tests/test_scheduler.py tests/test_email_sender.py -q
```

Expected: PASS.

- [ ] **Step 13: Commit**

```powershell
git add src/t_alpha/storage/models.py src/t_alpha/storage/repository.py src/t_alpha/services_strategy.py src/t_alpha/scheduler/jobs.py src/t_alpha/notification/email_sender.py tests/test_storage.py tests/test_strategy_service.py tests/test_scheduler.py tests/test_email_sender.py
git commit -m "feat: add t0 monitor job and email content"
```

---

### Task 8: API Documentation and End-to-End Test Run

**Files:**
- Modify: `docs/api_integration.md`
- Modify: `.env.example`

- [ ] **Step 1: Update API docs**

Add this section to `docs/api_integration.md` after the default watchlist section:

```markdown
## 9. T0 策略接口

### `POST /api/v1/strategy/t0/build`

传入 A 股代码，生成该股低吸型做T策略，运行最近 3 年回测和参数微调，并返回最近 3 个月样本外交易明细。

请求：

```json
{
  "code": "601318.SH"
}
```

关键口径：

- 只支持先买后卖底仓。
- 单次金额 5000 到 20000 元。
- 买入价为信号确认后下一根 60 分钟 K 线开盘价。
- 目标收益为 3%。
- 最长持仓 10 个交易日。
- v1 不设置中途止损。
- 默认交易成本为万 1，可通过环境变量配置。
- 3 年有效交易数不少于 60 笔且成功率大于 50% 才可进入监控候选。

### `POST /api/v1/strategy/t0/monitor`

将通过门槛的股票加入 T0 监控列表。

请求：

```json
{
  "code": "601318.SH",
  "eligible": true
}
```
```

- [ ] **Step 2: Update environment template**

Append to `.env.example`:

```env
T0_TARGET_RETURN=0.03
T0_MAX_HOLDING_TRADE_DAYS=10
T0_TRADE_COST_RATE=0.0001
T0_MIN_3Y_TRADES=60
T0_OBSERVE_MIN_3Y_TRADES=30
```

- [ ] **Step 3: Run full test suite**

Run:

```powershell
py -3 -m pytest -q
```

Expected: PASS.

- [ ] **Step 4: Run API smoke test locally**

Start API:

```powershell
py -3 -m uvicorn t_alpha.main:app --host 127.0.0.1 --port 8867
```

In a second terminal, check OpenAPI:

```powershell
Invoke-RestMethod http://127.0.0.1:8867/openapi.json | Select-Object -ExpandProperty paths
```

Expected: response includes `/api/v1/strategy/t0/build` and `/api/v1/strategy/t0/monitor`.

- [ ] **Step 5: Commit**

```powershell
git add docs/api_integration.md .env.example
git commit -m "docs: document t0 strategy endpoints"
```

---

## Final Verification

Run:

```powershell
py -3 -m pytest -q
```

Expected: PASS.

Run:

```powershell
git status --short
```

Expected: no output.

Review the final behavior:

- `POST /api/v1/strategy/t0/build` returns a report with params, full metrics, train metrics, validation metrics, recent metrics, recent trades, and eligibility.
- `POST /api/v1/strategy/t0/monitor` rejects ineligible reports and enables eligible ones.
- Backtest uses next 60m open as entry.
- Exit occurs at 3% target or 10th trading day close.
- Same stock does not open overlapping T positions.
- Strategy is marked eligible only when the 3-year gate, success-rate gate, validation gate, and positive-return gate pass.
