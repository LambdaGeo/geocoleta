import streamlit as st
import pandas as pd

class FilterEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.filtered_df = df.copy()

    def apply(self):
        st.markdown("### 🎚️ Filtros Automáticos")

        # detecta tipos de dados
        cat_cols = [c for c in self.df.columns if self.df[c].dtype == "object"]
        num_cols = [c for c in self.df.columns if pd.api.types.is_numeric_dtype(self.df[c])]
        date_cols = [c for c in self.df.columns if pd.api.types.is_datetime64_any_dtype(self.df[c])]

        with st.expander("Configurar filtros"):
            # ---------------------------
            # 1. Filtros para categorias
            # ---------------------------
            for col in cat_cols:
                valores = self.df[col].dropna().unique()
                selecionados = st.multiselect(f"{col}:", valores, default=valores)

                # aplica filtro
                self.filtered_df = self.filtered_df[self.filtered_df[col].isin(selecionados)]

            # ---------------------------
            # 2. Filtros para números
            # ---------------------------
            for col in num_cols:
                minimo = float(self.df[col].min())
                maximo = float(self.df[col].max())
                vmin, vmax = st.slider(f"{col}:", minimo, maximo, (minimo, maximo))
                self.filtered_df = self.filtered_df[
                    (self.filtered_df[col] >= vmin) & (self.filtered_df[col] <= vmax)
                ]

            # ---------------------------
            # 3. Filtros para datas
            # ---------------------------
            for col in date_cols:
                min_date = self.df[col].min()
                max_date = self.df[col].max()

                vmin, vmax = st.date_input(
                    f"{col}:",
                    value=[min_date, max_date]
                )

                self.filtered_df = self.filtered_df[
                    (self.filtered_df[col] >= pd.to_datetime(vmin)) &
                    (self.filtered_df[col] <= pd.to_datetime(vmax))
                ]

        return self.filtered_df
