from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bootstrap import add_vendor_path

add_vendor_path()

from ab_analysis import analyze_ab_test
from ab_dashboard import build_ab_dashboard
from config import (
    AB_DASHBOARD_PATH,
    AB_DATA_PATH,
    AB_SUMMARY_PATH,
    DATA_DIR,
    OUTPUT_DIR,
    PROJECT_ROOT,
    REFUND_DASHBOARD_PATH,
    REFUND_DATA_PATH,
    REFUND_SUMMARY_PATH,
    SIGNIFICANCE_LEVEL,
    SUMMARY_PATH,
)
from data_loader import (
    REQUIRED_AB_COLUMNS,
    REQUIRED_REFUND_COLUMNS,
    read_csv_columns_with_fallback,
    read_csv_with_fallback,
)
from refund_analysis import analyze_refunds
from refund_dashboard import build_refund_dashboard


AB_SUMMARY_KEYS = [
    "raw_rows", "invalid_value_rows", "mismatch_rows",
    "duplicate_rows_removed", "clean_rows", "control_rate",
    "treatment_rate", "absolute_difference", "relative_lift", "z_score",
    "p_value", "alpha", "ci_low", "ci_high", "significant",
    "conclusion", "recommendation",
]
REFUND_SUMMARY_KEYS = [
    "raw_rows", "invalid_rows", "duplicate_refund_ids", "clean_rows",
    "total_refund_amount", "average_refund_amount", "median_refund_amount",
    "amount_min", "amount_max", "p95", "p99", "q1", "q3", "iqr",
    "iqr_upper_fence", "anomaly_count", "anomaly_rate", "anomaly_amount",
    "anomaly_amount_share", "top_reason", "top_reason_count_share",
    "top_reason_amount_share", "median_refund_delay_minutes",
    "product_unique_count",
]


def _select_keys(result: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    return {key: result[key] for key in keys}


def _relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
    except ValueError:
        return str(path.resolve())


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def resolve_data_file(csv_file: str | None, default_path: Path) -> Path:
    """将 Agent 提供的 CSV 文件名安全限制在 data 目录内。"""
    if not csv_file:
        return default_path
    requested = Path(csv_file)
    if requested.name != csv_file or requested.suffix.lower() != ".csv":
        raise ValueError("csv_file 只能是 data 目录内的 CSV 文件名，不能包含路径")
    candidate = DATA_DIR / requested.name
    if not candidate.exists():
        raise FileNotFoundError(f"数据文件不存在: {candidate}")
    return candidate


def inspect_data_catalog() -> list[dict[str, Any]]:
    """扫描 data 目录并按必要字段识别可执行的分析类型。"""
    catalog: list[dict[str, Any]] = []
    for path in sorted(DATA_DIR.glob("*.csv")):
        try:
            columns = read_csv_columns_with_fallback(path)
            column_set = set(columns)
            analysis_types = []
            if REQUIRED_AB_COLUMNS.issubset(column_set):
                analysis_types.append("ab_test")
            if REQUIRED_REFUND_COLUMNS.issubset(column_set):
                analysis_types.append("refund_anomaly")
            catalog.append({
                "file": path.name,
                "size_bytes": path.stat().st_size,
                "columns": columns,
                "analysis_types": analysis_types or ["unknown"],
            })
        except Exception as exc:
            catalog.append({
                "file": path.name,
                "analysis_types": ["unreadable"],
                "error": str(exc),
            })
    return catalog


def run_ab_pipeline(
    csv_file: str | None = None,
    alpha: float = SIGNIFICANCE_LEVEL,
    generate_dashboard: bool = True,
) -> dict[str, Any]:
    if not 0 < alpha < 1:
        raise ValueError("alpha 必须在 0 和 1 之间")
    source_path = resolve_data_file(csv_file, AB_DATA_PATH)
    raw = read_csv_with_fallback(source_path)
    result = analyze_ab_test(raw, alpha)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    group_summary_path = OUTPUT_DIR / "ab_group_summary.csv"
    result["group_summary"].to_csv(
        group_summary_path, index=False, encoding="utf-8-sig"
    )
    if generate_dashboard:
        build_ab_dashboard(result, AB_DASHBOARD_PATH)

    payload = {
        "analysis_type": "ab_test",
        "source_file": _relative_path(source_path),
        "metrics": _select_keys(result, AB_SUMMARY_KEYS),
        "artifacts": {
            "group_summary": _relative_path(group_summary_path),
            "dashboard": (
                _relative_path(AB_DASHBOARD_PATH) if generate_dashboard else None
            ),
        },
    }
    _write_json(AB_SUMMARY_PATH, payload)
    return payload


def run_refund_pipeline(
    csv_file: str | None = None,
    generate_dashboard: bool = True,
) -> dict[str, Any]:
    source_path = resolve_data_file(csv_file, REFUND_DATA_PATH)
    raw = read_csv_with_fallback(source_path)
    result = analyze_refunds(raw)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reason_summary_path = OUTPUT_DIR / "refund_reason_summary.csv"
    anomaly_records_path = OUTPUT_DIR / "refund_anomaly_records.csv"
    result["reason_summary"].to_csv(
        reason_summary_path, index=False, encoding="utf-8-sig"
    )
    result["anomalies"].to_csv(
        anomaly_records_path, index=False, encoding="utf-8-sig"
    )
    if generate_dashboard:
        build_refund_dashboard(result, REFUND_DASHBOARD_PATH)

    payload = {
        "analysis_type": "refund_anomaly",
        "source_file": _relative_path(source_path),
        "metrics": _select_keys(result, REFUND_SUMMARY_KEYS),
        "artifacts": {
            "reason_summary": _relative_path(reason_summary_path),
            "anomaly_records": _relative_path(anomaly_records_path),
            "dashboard": (
                _relative_path(REFUND_DASHBOARD_PATH)
                if generate_dashboard else None
            ),
        },
    }
    _write_json(REFUND_SUMMARY_PATH, payload)
    return payload


def run_full_pipeline(
    ab_csv_file: str | None = None,
    refund_csv_file: str | None = None,
    alpha: float = SIGNIFICANCE_LEVEL,
    generate_dashboards: bool = True,
) -> dict[str, Any]:
    ab_payload = run_ab_pipeline(
        csv_file=ab_csv_file,
        alpha=alpha,
        generate_dashboard=generate_dashboards,
    )
    refund_payload = run_refund_pipeline(
        csv_file=refund_csv_file,
        generate_dashboard=generate_dashboards,
    )
    summary = {
        "ab_test": ab_payload["metrics"],
        "refund_analysis": refund_payload["metrics"],
        "artifacts": {
            "ab_test": ab_payload["artifacts"],
            "refund_analysis": refund_payload["artifacts"],
        },
    }
    _write_json(SUMMARY_PATH, summary)
    return summary


def read_latest_summary() -> dict[str, Any]:
    if not SUMMARY_PATH.exists():
        raise FileNotFoundError(
            "尚未生成综合分析摘要，请先运行完整业务分析工具"
        )
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
