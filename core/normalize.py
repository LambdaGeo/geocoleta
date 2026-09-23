"""Converte as respostas brutas do Epicollect em tipos que a UI usa diretamente."""
import numpy as np
import pandas as pd


def _empty_to_nan(value):
    if isinstance(value, str) and value.strip() == "":
        return np.nan
    return value


def _as_list(value):
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    # CSV do Epicollect traz múltipla escolha separada por vírgula
    return [v.strip() for v in text.split(",") if v.strip()] if text else []


def _first(value):
    if isinstance(value, list):
        return value[0] if value else np.nan
    return value


def _coord(value, key):
    if isinstance(value, dict):
        return value.get(key)
    return np.nan


def _unify_case(series):
    """Respostas digitadas ("anjo da guarda", "Anjo  da Guarda", "AnjodaGuarda") viram a grafia mais frequente."""
    def key(value):
        return "".join(value.lower().split())

    counts = series.dropna().value_counts()
    canonical = {}
    for value in counts.index:
        canonical.setdefault(key(value), value)
    return series.map(lambda v: v if pd.isna(v) else canonical[key(v)])


def _categorical(series, options):
    observed = [v for v in series.dropna().unique() if v not in options]
    return pd.Categorical(series, categories=list(options) + sorted(map(str, observed)))


def normalize(df: pd.DataFrame, fields: list, timezone: str | None = None) -> pd.DataFrame:
    df = df.copy()
    for f in fields:
        if f.column not in df.columns:
            continue
        col = df[f.column]
        kind = f.kind

        if kind == "location":
            df[f.lat] = pd.to_numeric(col.map(lambda v: _coord(v, "latitude")), errors="coerce")
            df[f.lon] = pd.to_numeric(col.map(lambda v: _coord(v, "longitude")), errors="coerce")
            continue

        if kind == "multi":
            df[f.column] = col.map(_as_list)
            continue

        col = col.map(_empty_to_nan)

        if kind == "categorical":
            col = col.map(_first).map(lambda v: v if pd.isna(v) else " ".join(str(v).split()))
            if not f.options:
                col = _unify_case(col)
            options = f.options or sorted(col.dropna().unique(), key=str.lower)
            df[f.column] = _categorical(col, options)
        elif kind == "numeric":
            df[f.column] = pd.to_numeric(col, errors="coerce")
        elif kind == "date":
            parsed = pd.to_datetime(col, errors="coerce", utc=True, format="mixed")
            if timezone:
                parsed = parsed.dt.tz_convert(timezone)
            df[f.column] = parsed.dt.tz_localize(None)
        else:
            df[f.column] = col
    return df


def flat_for_export(df: pd.DataFrame, fields: list) -> pd.DataFrame:
    """Tabela plana (listas unidas, localização em lat/lon) com as perguntas como cabeçalho."""
    out = pd.DataFrame(index=df.index)
    for f in fields:
        if f.kind == "location":
            if f.lat in df.columns:
                out[f"{f.label} (lat)"] = df[f.lat]
                out[f"{f.label} (lon)"] = df[f.lon]
        elif f.column in df.columns:
            col = df[f.column]
            if f.kind == "multi":
                col = col.map(lambda v: "; ".join(v) if isinstance(v, list) else v)
            elif f.kind == "categorical":
                col = col.astype(object)
            name = f.label if f.label not in out.columns else f"{f.label} [{f.column}]"
            out[name] = col
    return out
