from __future__ import annotations

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
            "profit_loss_ratio": 0.0,
            "max_consecutive_losses": 0,
        }

    arr = np.array(returns, dtype=float)
    equity = np.cumprod(1 + arr)
    peak = np.maximum.accumulate(equity)
    drawdown = equity / peak - 1
    wins = arr[arr > 0]
    losses = arr[arr < 0]
    loss_flags = arr < 0
    max_loss_streak = 0
    current = 0
    for flag in loss_flags:
        current = current + 1 if flag else 0
        max_loss_streak = max(max_loss_streak, current)

    return {
        "sample_count": int(len(arr)),
        "win_rate": float((arr > 0).mean()),
        "average_return": float(arr.mean()),
        "median_return": float(np.median(arr)),
        "expected_return": float(arr.mean()),
        "max_drawdown": float(drawdown.min()),
        "profit_loss_ratio": float(wins.mean() / abs(losses.mean())) if len(wins) and len(losses) else 0.0,
        "max_consecutive_losses": int(max_loss_streak),
    }
