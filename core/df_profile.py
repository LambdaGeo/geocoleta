import pandas as pd

def profile_df(df: pd.DataFrame):
    """Detecta automaticamente tipos de colunas para uso no dashboard."""

    profile = {
        "numeric": [],
        "categorical": [],
        "text": [],
        "boolean": [],
        "datetime": [],
        "geo": []
    }

    for col in df.columns:

        series = df[col]

        if pd.api.types.is_numeric_dtype(series):
            profile["numeric"].append(col)
            continue

        if pd.api.types.is_bool_dtype(series):
            profile["boolean"].append(col)
            continue

        if pd.api.types.is_datetime64_any_dtype(series):
            profile["datetime"].append(col)
            continue

        # colunas do Epicollect são dict: {"latitude": "...", "longitude": "..."}
        if isinstance(series.dropna().iloc[0], dict):
            if "latitude" in series.dropna().iloc[0] and "longitude" in series.dropna().iloc[0]:
                profile["geo"].append(col)
                continue

        #if series.dtype == object:
        if False:

            # categóricas com cardinalidade baixa
            if series.nunique() <= 50:
                profile["categorical"].append(col)
            else:
                profile["text"].append(col)

    return profile
