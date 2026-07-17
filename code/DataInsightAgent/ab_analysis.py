from __future__ import annotations

import math

import pandas as pd
from scipy.stats import norm

from data_loader import REQUIRED_AB_COLUMNS, validate_columns


def analyze_ab_test(raw: pd.DataFrame, alpha: float = 0.05) -> dict:
    """清洗实验数据并执行双侧双样本比例 Z 检验。"""
    validate_columns(raw, REQUIRED_AB_COLUMNS, "ab_data.csv")
    frame = raw.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce")
    frame["converted"] = pd.to_numeric(frame["converted"], errors="coerce")

    invalid_mask = (
        frame["timestamp"].isna()
        | ~frame["group"].isin(["control", "treatment"])
        | ~frame["landing_page"].isin(["old_page", "new_page"])
        | ~frame["converted"].isin([0, 1])
    )
    invalid_value_rows = int(invalid_mask.sum())
    frame = frame.loc[~invalid_mask].copy()

    consistent_mask = (
        frame["group"].eq("control") & frame["landing_page"].eq("old_page")
    ) | (
        frame["group"].eq("treatment") & frame["landing_page"].eq("new_page")
    )
    mismatch_rows = int((~consistent_mask).sum())
    frame = frame.loc[consistent_mask].sort_values("timestamp").copy()
    duplicate_rows = int(frame.duplicated("user_id", keep="first").sum())
    clean = frame.drop_duplicates("user_id", keep="first").copy()
    clean["date"] = clean["timestamp"].dt.date.astype(str)

    grouped = (
        clean.groupby("group", observed=True)["converted"]
        .agg(sample_size="size", conversions="sum", conversion_rate="mean")
        .reindex(["control", "treatment"])
        .reset_index()
    )
    if grouped[["sample_size", "conversions"]].isna().any().any():
        raise ValueError("A/B 数据必须同时包含 control 和 treatment 两个分组")

    control = grouped.iloc[0]
    treatment = grouped.iloc[1]
    n_control, n_treatment = int(control.sample_size), int(treatment.sample_size)
    x_control, x_treatment = int(control.conversions), int(treatment.conversions)
    p_control = float(control.conversion_rate)
    p_treatment = float(treatment.conversion_rate)
    difference = p_treatment - p_control
    relative_lift = difference / p_control if p_control else math.nan

    pooled_rate = (x_control + x_treatment) / (n_control + n_treatment)
    pooled_se = math.sqrt(
        pooled_rate * (1 - pooled_rate) * (1 / n_control + 1 / n_treatment)
    )
    z_score = difference / pooled_se if pooled_se else 0.0
    p_value = float(2 * norm.sf(abs(z_score)))
    unpooled_se = math.sqrt(
        p_control * (1 - p_control) / n_control
        + p_treatment * (1 - p_treatment) / n_treatment
    )
    critical = float(norm.ppf(1 - alpha / 2))
    ci_low = difference - critical * unpooled_se
    ci_high = difference + critical * unpooled_se
    significant = p_value < alpha

    daily = (
        clean.groupby(["date", "group"], observed=True)["converted"]
        .agg(sample_size="size", conversions="sum", conversion_rate="mean")
        .reset_index()
    )
    daily_rates = (
        daily.pivot(index="date", columns="group", values="conversion_rate")
        .reindex(columns=["control", "treatment"])
        .reset_index()
    )
    daily_rates["absolute_lift"] = daily_rates.treatment - daily_rates.control

    cumulative = clean.sort_values("timestamp").copy()
    cumulative["cum_conversions"] = cumulative.groupby("group")["converted"].cumsum()
    cumulative["cum_sample"] = cumulative.groupby("group").cumcount() + 1
    cumulative["cumulative_rate"] = cumulative.cum_conversions / cumulative.cum_sample
    cumulative_rates = (
        cumulative.groupby(["date", "group"], observed=True)
        .tail(1)
        .pivot(index="date", columns="group", values="cumulative_rate")
        .reindex(columns=["control", "treatment"])
        .reset_index()
    )

    conclusion = (
        "实验组与对照组转化率存在统计显著差异。"
        if significant else "未发现实验组与对照组转化率存在统计显著差异。"
    )
    if significant and difference > 0:
        recommendation = "实验组显著优于对照组，可结合收益与实施成本评估上线。"
    elif significant and difference < 0:
        recommendation = "实验组显著劣于对照组，不建议上线当前方案。"
    else:
        recommendation = "当前证据不足以支持上线实验方案，建议继续实验或重新评估效应量。"

    return {
        "clean_data": clean,
        "group_summary": grouped,
        "daily_rates": daily_rates,
        "cumulative_rates": cumulative_rates,
        "raw_rows": int(len(raw)),
        "invalid_value_rows": invalid_value_rows,
        "mismatch_rows": mismatch_rows,
        "duplicate_rows_removed": duplicate_rows,
        "clean_rows": int(len(clean)),
        "control_rate": p_control,
        "treatment_rate": p_treatment,
        "absolute_difference": difference,
        "relative_lift": relative_lift,
        "z_score": float(z_score),
        "p_value": p_value,
        "alpha": alpha,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
        "significant": bool(significant),
        "conclusion": conclusion,
        "recommendation": recommendation,
    }

