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

    # 前复权只调整价格列，成交量和成交额保持原始口径。
    latest_factor = valid.iloc[-1]
    ratio = factor / latest_factor
    for col in ["open", "high", "low", "close"]:
        if col in adjusted.columns:
            adjusted[col] = adjusted[col].astype(float).to_numpy() * ratio.to_numpy()
    return adjusted
