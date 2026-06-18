from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timedelta

import pandas as pd
from fastapi import HTTPException

from t_alpha.backtest.t0_engine import T0BacktestEngine
from t_alpha.backtest.t0_optimizer import evaluate_eligibility, summarize_trades
from t_alpha.config import Settings
from t_alpha.constants import DEFAULT_T0_STRATEGY, DISCLAIMER
from t_alpha.data.market_data import period_to_ad_value
from t_alpha.strategy.t0_models import T0StrategyParams, T0StrategyReport, amount_to_board_lot_shares
from t_alpha.strategy.t0_rules import generate_low_buy_candidates
from t_alpha.storage.repository import (
    close_t0_position,
    get_latest_t0_report,
    get_open_t0_position,
    list_enabled_watchlist,
    open_t0_position,
    save_t0_report,
    set_t0_monitor_enabled,
)


class T0StrategyService:
    def __init__(self, client, session=None, settings: Settings | None = None):
        self.client = client
        self.session = session
        self.settings = settings or Settings()

    def build_report(self, code: str) -> dict:
        params = self._params()
        begin_date, end_date = self._date_window()
        daily_df = self._query_forward_kline(code, begin_date, end_date, "day")
        hourly_df = self._query_forward_kline(code, begin_date, end_date, "60m")

        candidates = generate_low_buy_candidates(code, daily_df, hourly_df, params)
        trades = T0BacktestEngine(params).run(code, hourly_df, candidates)
        train, validation, recent = self._split_trades(trades)
        full_metrics = summarize_trades(trades)
        train_metrics = summarize_trades(train)
        validation_metrics = summarize_trades(validation)
        recent_metrics = summarize_trades(recent)
        eligibility = evaluate_eligibility(full_metrics, validation_metrics, params)

        report = T0StrategyReport(
            code=code,
            strategy_name=DEFAULT_T0_STRATEGY,
            params=params,
            full_metrics=full_metrics,
            train_metrics=train_metrics,
            validation_metrics=validation_metrics,
            recent_metrics=recent_metrics,
            recent_trades=recent,
            eligibility=eligibility,
            generated_at=datetime.utcnow(),
            disclaimer=DISCLAIMER,
        )
        payload = report.to_dict()
        if self.session is not None:
            save_t0_report(
                self.session,
                code=code,
                strategy_name=DEFAULT_T0_STRATEGY,
                params_json=json.dumps(asdict(params), ensure_ascii=False),
                report_json=json.dumps(payload, ensure_ascii=False),
                eligible=eligibility.eligible,
                eligibility_level=eligibility.level,
            )
        return payload

    def enable_monitor(self, code: str, enabled: bool) -> dict:
        if self.session is None:
            return {"code": code, "enabled": enabled, "strategy_name": DEFAULT_T0_STRATEGY}
        report = get_latest_t0_report(self.session, code, DEFAULT_T0_STRATEGY)
        if report is None:
            return {"code": code, "enabled": False, "strategy_name": DEFAULT_T0_STRATEGY, "reason": "no frozen report"}
        if enabled and not report.eligible:
            return {"code": code, "enabled": False, "strategy_name": DEFAULT_T0_STRATEGY, "reason": "report is not eligible"}
        row = set_t0_monitor_enabled(self.session, code, enabled, DEFAULT_T0_STRATEGY)
        return {"code": row.code, "enabled": row.enabled, "strategy_name": row.strategy_name}

    def list_enabled_t0_codes(self) -> list[str]:
        if self.session is None:
            return []
        return [row.code for row in list_enabled_watchlist(self.session) if row.strategy_name == DEFAULT_T0_STRATEGY]

    def generate_realtime_signal(self, code: str, now: datetime) -> dict | None:
        report = self._load_report(code)
        if report is None or not report.get("eligibility", {}).get("eligible", False):
            return None
        params = T0StrategyParams(**report["params"])
        begin_date, end_date = self._date_window()
        daily_df = self._query_forward_kline(code, begin_date, end_date, "day")
        hourly_df = self._query_forward_kline(code, begin_date, end_date, "60m")
        candidates = generate_low_buy_candidates(code, daily_df, hourly_df, params)
        if not candidates:
            return None
        candidate = candidates[-1]
        amount = self._suggested_amount(candidate.score, params)
        shares = amount_to_board_lot_shares(amount, candidate.signal_price)
        if shares < 100:
            return None
        target_sell_price = round(candidate.signal_price * (1 + params.target_return), 3)
        return {
            "code": code,
            "signal_time": candidate.signal_time.strftime("%Y-%m-%d %H:%M:%S"),
            "buy_alert_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": candidate.signal_price,
            "reference_buy_price": candidate.signal_price,
            "suggested_buy_zone": [round(candidate.signal_price * 0.995, 3), round(candidate.signal_price * 1.002, 3)],
            "suggested_amount": amount,
            "suggested_shares": shares,
            "target_sell_price": target_sell_price,
            "max_holding_trade_days": params.max_holding_trade_days,
            "opened_trade_date": now.strftime("%Y-%m-%d"),
            "full_success_rate": report["full_metrics"]["success_rate"],
            "full_trade_count": report["full_metrics"]["trade_count"],
            "recent_success_rate": report["recent_metrics"]["success_rate"],
            "recent_trade_count": report["recent_metrics"]["trade_count"],
            "reasons": candidate.reasons,
        }

    def mark_position_open(self, code: str, payload: dict) -> None:
        if self.session is None:
            return
        open_t0_position(self.session, code, DEFAULT_T0_STRATEGY, json.dumps(payload, ensure_ascii=False))

    def get_open_t0_position(self, code: str):
        if self.session is None:
            return None
        return get_open_t0_position(self.session, code, DEFAULT_T0_STRATEGY)

    def get_current_price(self, code: str) -> float:
        begin_date, end_date = self._date_window()
        hourly_df = self._query_forward_kline(code, begin_date, end_date, "60m")
        return float(hourly_df.sort_values("kline_time").iloc[-1]["close"])

    def holding_trade_days(self, position, now: datetime) -> int:
        payload = json.loads(position.payload_json)
        opened = datetime.strptime(payload["opened_trade_date"], "%Y-%m-%d").date()
        trade_dates = [datetime.strptime(str(day), "%Y%m%d").date() for day in self.client.get_calendar()]
        return sum(opened <= day <= now.date() for day in trade_dates)

    def generate_sell_signal(self, position_payload: dict, current_price: float, holding_trade_days: int, now: datetime) -> dict | None:
        target_sell_price = float(position_payload["target_sell_price"])
        max_holding_trade_days = int(position_payload["max_holding_trade_days"])
        exit_reason = None
        sell_alert_type = None
        trigger_price = current_price

        if current_price >= target_sell_price:
            exit_reason = "target"
            sell_alert_type = "target"
            trigger_price = target_sell_price
        elif holding_trade_days >= max_holding_trade_days:
            exit_reason = "timeout"
            sell_alert_type = "timeout"

        if exit_reason is None:
            return None

        buy_price = float(position_payload["reference_buy_price"])
        shares = int(position_payload["suggested_shares"])
        gross_return = (trigger_price - buy_price) / buy_price
        net_return = gross_return - self.settings.t0_trade_cost_rate
        return {
            **position_payload,
            "sell_alert_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_price": current_price,
            "trigger_price": round(trigger_price, 3),
            "sell_alert_type": sell_alert_type,
            "exit_reason": exit_reason,
            "holding_trade_days": holding_trade_days,
            "gross_return": gross_return,
            "net_return": net_return,
            "estimated_profit_amount": round((trigger_price - buy_price) * shares, 2),
            "position_status": "closed",
        }

    def mark_position_closed(self, position, payload: dict) -> None:
        if self.session is None:
            return
        close_t0_position(self.session, position, json.dumps(payload, ensure_ascii=False))

    def _params(self) -> T0StrategyParams:
        return T0StrategyParams(
            target_return=self.settings.t0_target_return,
            max_holding_trade_days=self.settings.t0_max_holding_trade_days,
            trade_cost_rate=self.settings.t0_trade_cost_rate,
            min_trade_amount=self.settings.min_trade_amount,
            max_trade_amount=self.settings.max_trade_amount,
            min_3y_trades=self.settings.t0_min_3y_trades,
            observe_min_3y_trades=self.settings.t0_observe_min_3y_trades,
            min_success_rate=self.settings.t0_min_success_rate,
        )

    def _date_window(self) -> tuple[int, int]:
        calendar = self.client.get_calendar()
        end_date = int(calendar[-1])
        start_date = int((datetime.strptime(str(end_date), "%Y%m%d") - timedelta(days=365 * 3)).strftime("%Y%m%d"))
        return start_date, end_date

    def _query_forward_kline(self, code: str, begin_date: int, end_date: int, period: str) -> pd.DataFrame:
        period_arg = period
        if hasattr(self.client, "ad"):
            period_arg = period_to_ad_value(self.client.ad, period)
        kline_dict = self.client.query_kline(code, begin_date, end_date, period_arg)
        df = kline_dict.get(code)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"no {period} market data returned")
        return df

    @staticmethod
    def _split_trades(trades):
        if not trades:
            return [], [], []
        ordered = sorted(trades, key=lambda trade: trade.buy_time)
        recent_cutoff = ordered[-1].buy_time - timedelta(days=92)
        historical = [trade for trade in ordered if trade.buy_time < recent_cutoff]
        recent = [trade for trade in ordered if trade.buy_time >= recent_cutoff]
        split_at = int(len(historical) * 0.7)
        return historical[:split_at], historical[split_at:], recent

    def _load_report(self, code: str) -> dict | None:
        if self.session is None:
            return None
        row = get_latest_t0_report(self.session, code, DEFAULT_T0_STRATEGY)
        if row is None:
            return None
        return json.loads(row.report_json)

    @staticmethod
    def _suggested_amount(score: float, params: T0StrategyParams) -> int:
        bounded = max(0.0, min(1.0, score))
        amount = params.min_trade_amount + (params.max_trade_amount - params.min_trade_amount) * bounded
        return int(round(amount / 1000) * 1000)
