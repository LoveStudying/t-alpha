import numpy as np
import pandas as pd


def ma(series: pd.Series, n: int) -> pd.Series:
    return series.astype(float).rolling(n, min_periods=n).mean()


def ema(series: pd.Series, n: int) -> pd.Series:
    return series.astype(float).ewm(span=n, adjust=False, min_periods=n).mean()


def rsi(series: pd.Series, n: int = 6) -> pd.Series:
    delta = series.astype(float).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    avg_loss = loss.ewm(alpha=1 / n, adjust=False, min_periods=n).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def boll(series: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    mid = ma(series, n)
    std = series.astype(float).rolling(n, min_periods=n).std()
    return pd.DataFrame({"mid": mid, "upper": mid + k * std, "lower": mid - k * std})


def atr(high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14) -> pd.Series:
    high = high.astype(float)
    low = low.astype(float)
    close = close.astype(float)
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def kdj(close: pd.Series, high: pd.Series, low: pd.Series, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
    close = close.astype(float)
    low_min = low.astype(float).rolling(n, min_periods=n).min()
    high_max = high.astype(float).rolling(n, min_periods=n).max()
    # 分母为 0 时保留缺失值，避免低波动数据产生虚假极端信号。
    rsv = (close - low_min) / (high_max - low_min).replace(0, np.nan) * 100
    k = rsv.ewm(alpha=1 / m1, adjust=False).mean()
    d = k.ewm(alpha=1 / m2, adjust=False).mean()
    j = 3 * k - 2 * d
    return pd.DataFrame({"k": k, "d": d, "j": j})
