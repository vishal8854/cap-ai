import pandas as pd


def profile_dataframe(df: pd.DataFrame) -> dict:
    if df.empty:
        return {"rows": 0, "columns": 0, "missing": {}, "duplicates": 0, "outliers": {}}

    missing = df.isnull().sum().to_dict()
    duplicates = int(df.duplicated().sum())
    outliers = {}
    for col in df.select_dtypes(include="number").columns:
        q1, q3 = df[col].quantile(0.25), df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            outlier_count = int(((df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)).sum())
            if outlier_count > 0:
                outliers[col] = outlier_count

    return {
        "rows": len(df),
        "columns": len(df.columns),
        "missing": {k: int(v) for k, v in missing.items() if v > 0},
        "duplicates": duplicates,
        "outliers": outliers,
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip() for c in df.columns]
    return df
