"""Excel and CSV import utilities."""

import io
from pathlib import Path
from typing import Optional

import pandas as pd

from config import UPLOADS_DIR


COLUMN_ALIASES = {
    "transaction id": "Transaction ID",
    "txn id": "Transaction ID",
    "date": "Date",
    "txn date": "Date",
    "from account": "From Account",
    "from": "From Account",
    "to account": "To Account",
    "to": "To Account",
    "amount": "Amount",
    "approved by": "Approved By",
    "account": "Account",
    "principal": "Principal",
    "rate": "Rate",
    "actual interest": "Actual Interest",
    "balance": "Balance",
    "last transaction date": "Last Transaction Date",
    "authorized signatory": "Authorized Signatory",
    "case id": "Case ID",
    "case name": "Case Name",
}


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        renamed[col] = COLUMN_ALIASES.get(key, str(col).strip())
    return df.rename(columns=renamed)


def read_uploaded_file(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    elif name.endswith(".xls"):
        df = pd.read_excel(uploaded_file, engine="xlrd")
    else:
        df = pd.read_excel(uploaded_file, engine="openpyxl")
    return normalize_columns(df)


def profile_dataframe(df: pd.DataFrame) -> dict:
    profile = {
        "rows": len(df),
        "columns": len(df.columns),
        "duplicates": int(df.duplicated().sum()),
        "missing": {col: int(df[col].isna().sum()) for col in df.columns if df[col].isna().any()},
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
    }
    outliers = {}
    for col in df.select_dtypes(include="number").columns:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            outlier_count = int(((series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)).sum())
            if outlier_count:
                outliers[col] = outlier_count
    profile["outliers"] = outliers
    return profile


def detect_duplicates(df: pd.DataFrame, subset: Optional[list] = None) -> pd.DataFrame:
    if subset:
        cols = [c for c in subset if c in df.columns]
        if cols:
            return df[df.duplicated(subset=cols, keep=False)]
    return df[df.duplicated(keep=False)]


def save_upload_temp(uploaded_file) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOADS_DIR / uploaded_file.name
    with open(path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return path


def export_dataframe_excel(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
    return buffer.getvalue()


def export_dataframe_csv(df: pd.DataFrame) -> str:
    return df.to_csv(index=False)


def auto_map_columns(df: pd.DataFrame, expected: list[str]) -> dict[str, str]:
    mapping = {}
    normalized = {str(c).strip().lower(): c for c in df.columns}
    for exp in expected:
        key = exp.lower()
        if key in normalized:
            mapping[exp] = normalized[key]
        else:
            for ncol, orig in normalized.items():
                if key in ncol or ncol in key:
                    mapping[exp] = orig
                    break
    return mapping
