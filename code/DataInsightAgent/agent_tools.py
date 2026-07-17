from __future__ import annotations

import json

from bootstrap import add_vendor_path

add_vendor_path()

from langchain_core.tools import tool

from pipeline import (
    inspect_data_catalog,
    read_latest_summary,
    run_ab_pipeline,
    run_full_pipeline,
    run_refund_pipeline,
)


def _tool_response(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


@tool
def list_available_datasets() -> str:
    """扫描 data 目录，列出 CSV 文件、字段和可执行的业务分析类型。"""
    return _tool_response(inspect_data_catalog())


@tool
def analyze_ab_experiment(
    csv_file: str = "ab_data.csv",
    alpha: float = 0.05,
    generate_dashboard: bool = True,
) -> str:
    """分析 A/B 实验 CSV，执行数据清洗、转化率比较和双侧比例 Z 检验。

    Args:
        csv_file: data 目录中的 CSV 文件名，不要包含目录路径。
        alpha: 显著性水平，必须在 0 和 1 之间，通常为 0.05。
        generate_dashboard: 是否生成离线 HTML 决策大屏。
    """
    return _tool_response(run_ab_pipeline(csv_file, alpha, generate_dashboard))


@tool
def analyze_refund_anomalies(
    csv_file: str = "refund_detail_generated.csv",
    generate_dashboard: bool = True,
) -> str:
    """分析退款明细 CSV，输出退款归因、IQR 高额异常和离线大屏。

    Args:
        csv_file: data 目录中的 CSV 文件名，不要包含目录路径。
        generate_dashboard: 是否生成离线 HTML 分析大屏。
    """
    return _tool_response(run_refund_pipeline(csv_file, generate_dashboard))


@tool
def run_complete_business_analysis(
    ab_csv_file: str = "ab_data.csv",
    refund_csv_file: str = "refund_detail_generated.csv",
    alpha: float = 0.05,
    generate_dashboards: bool = True,
) -> str:
    """一次运行 A/B 测试和退款异常两套分析，并生成综合摘要。

    Args:
        ab_csv_file: data 目录中的 A/B 测试 CSV 文件名。
        refund_csv_file: data 目录中的退款明细 CSV 文件名。
        alpha: A/B 检验显著性水平，通常为 0.05。
        generate_dashboards: 是否生成两个离线 HTML 大屏。
    """
    return _tool_response(run_full_pipeline(
        ab_csv_file=ab_csv_file,
        refund_csv_file=refund_csv_file,
        alpha=alpha,
        generate_dashboards=generate_dashboards,
    ))


@tool
def read_latest_business_summary() -> str:
    """读取最近一次完整业务分析产生的综合 JSON 摘要。"""
    return _tool_response(read_latest_summary())


DATA_INSIGHT_TOOLS = [
    list_available_datasets,
    analyze_ab_experiment,
    analyze_refund_anomalies,
    run_complete_business_analysis,
    read_latest_business_summary,
]
