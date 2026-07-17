from __future__ import annotations

import numpy as np
import pandas as pd

from data_loader import REQUIRED_REFUND_COLUMNS, validate_columns


def _category_summary(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    summary = (
        frame.groupby(column, dropna=False, observed=True)["refund_amount"]
        .agg(refund_count="size", refund_amount="sum", avg_refund_amount="mean")
        .reset_index()
        .sort_values("refund_amount", ascending=False)
    )
    summary["count_share"] = summary.refund_count / summary.refund_count.sum()
    summary["amount_share"] = summary.refund_amount / summary.refund_amount.sum()
    return summary


def analyze_refunds(raw: pd.DataFrame) -> dict:
    """分析退款分布、原因、时效及高额异常。"""
    validate_columns(raw, REQUIRED_REFUND_COLUMNS, "refund_detail_generated.csv")
    frame = raw.copy()
    frame["order_time"] = pd.to_datetime(frame["order_time"], errors="coerce")
    frame["refund_time"] = pd.to_datetime(frame["refund_time"], errors="coerce")
    numeric_columns = [
        "original_quantity", "refund_quantity",
        "avg_actual_unit_price", "refund_amount",
    ]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    invalid_mask = (
        frame[["order_time", "refund_time", *numeric_columns]].isna().any(axis=1)
        | frame.refund_amount.lt(0)
        | frame.refund_quantity.lt(0)
    )
    invalid_rows = int(invalid_mask.sum())
    frame = frame.loc[~invalid_mask].copy()
    duplicate_refund_ids = int(frame.duplicated("refund_id", keep="first").sum())
    frame = frame.drop_duplicates("refund_id", keep="first")
    frame["refund_delay_minutes"] = (
        frame.refund_time - frame.order_time
    ).dt.total_seconds() / 60
    frame["refund_date"] = frame.refund_time.dt.date.astype(str)

    q1 = float(frame.refund_amount.quantile(0.25))
    q3 = float(frame.refund_amount.quantile(0.75))
    iqr = q3 - q1
    upper_fence = q3 + 1.5 * iqr
    p95 = float(frame.refund_amount.quantile(0.95))
    p99 = float(frame.refund_amount.quantile(0.99))
    frame["is_high_value_anomaly"] = frame.refund_amount > upper_fence
    anomalies = frame.loc[frame.is_high_value_anomaly].copy()

    reason_summary = _category_summary(frame, "refund_reason")
    promo_summary = _category_summary(frame, "promo_name")
    quantity_summary = _category_summary(frame, "refund_quantity")
    anomaly_reason_summary = _category_summary(anomalies, "refund_reason")
    anomaly_promo_summary = _category_summary(anomalies, "promo_name")
    daily_summary = (
        frame.groupby("refund_date", observed=True)["refund_amount"]
        .agg(refund_count="size", refund_amount="sum", avg_refund_amount="mean")
        .reset_index().sort_values("refund_date")
    )

    counts, edges = np.histogram(frame.refund_amount, bins=12)
    histogram = pd.DataFrame({
        "range": [f"{edges[i]:.0f}-{edges[i + 1]:.0f}" for i in range(12)],
        "count": counts.astype(int),
    })
    top_anomalies = anomalies.sort_values("refund_amount", ascending=False).head(15)[[
        "refund_id", "order_id", "promo_name", "product_name",
        "refund_quantity", "avg_actual_unit_price", "refund_amount",
        "refund_reason", "refund_delay_minutes",
    ]]

    top_reason = reason_summary.iloc[0]
    total_amount = float(frame.refund_amount.sum())
    anomaly_amount = float(anomalies.refund_amount.sum())
    return {
        "clean_data": frame,
        "anomalies": anomalies,
        "reason_summary": reason_summary,
        "promo_summary": promo_summary,
        "quantity_summary": quantity_summary,
        "anomaly_reason_summary": anomaly_reason_summary,
        "anomaly_promo_summary": anomaly_promo_summary,
        "daily_summary": daily_summary,
        "histogram": histogram,
        "top_anomalies": top_anomalies,
        "raw_rows": int(len(raw)),
        "invalid_rows": invalid_rows,
        "duplicate_refund_ids": duplicate_refund_ids,
        "clean_rows": int(len(frame)),
        "total_refund_amount": total_amount,
        "average_refund_amount": float(frame.refund_amount.mean()),
        "median_refund_amount": float(frame.refund_amount.median()),
        "amount_min": float(frame.refund_amount.min()),
        "amount_max": float(frame.refund_amount.max()),
        "p95": p95,
        "p99": p99,
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "iqr_upper_fence": float(upper_fence),
        "anomaly_count": int(len(anomalies)),
        "anomaly_rate": float(len(anomalies) / len(frame)),
        "anomaly_amount": anomaly_amount,
        "anomaly_amount_share": anomaly_amount / total_amount if total_amount else 0.0,
        "top_reason": str(top_reason.refund_reason),
        "top_reason_count_share": float(top_reason.count_share),
        "top_reason_amount_share": float(top_reason.amount_share),
        "median_refund_delay_minutes": float(frame.refund_delay_minutes.median()),
        "product_unique_count": int(frame.product_name.nunique()),
    }

