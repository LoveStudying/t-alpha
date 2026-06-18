def passes_quality_filter(
    sample_count: int,
    win_rate: float,
    expected_return: float,
    min_sample_count: int,
    min_win_rate: float,
    min_expected_return: float,
) -> bool:
    # 样本数、胜率和扣成本期望收益是发提醒的硬门槛。
    return (
        sample_count >= min_sample_count
        and win_rate >= min_win_rate
        and expected_return > min_expected_return
    )
