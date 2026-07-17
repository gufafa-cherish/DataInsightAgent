from pathlib import Path

import pandas as pd


REQUIRED_AB_COLUMNS = {
    "user_id", "timestamp", "group", "landing_page", "converted"
}
REQUIRED_REFUND_COLUMNS = {
    "refund_id", "order_id", "promo_name", "product_name", "order_time",
    "refund_time", "original_quantity", "refund_quantity",
    "avg_actual_unit_price", "refund_amount", "refund_reason",
}


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在: {path}")
    errors = []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeError(f"无法识别 CSV 编码: {path}; {' | '.join(errors)}")


def read_csv_columns_with_fallback(path: Path) -> list[str]:
    """只读取表头，用于快速识别 data 目录中的 CSV 业务类型。"""
    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在: {path}")
    errors = []
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return list(pd.read_csv(path, encoding=encoding, nrows=0).columns)
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    raise UnicodeError(f"无法识别 CSV 编码: {path}; {' | '.join(errors)}")


def validate_columns(frame: pd.DataFrame, required: set[str], name: str) -> None:
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"{name} 缺少必要字段: {missing}")
