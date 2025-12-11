import pandas as pd
from core.registry import datasource
from core.datasources import DataSource

@datasource("Dados Estáticos")
class StaticDataSource(DataSource):

    def load(self):
        # Dados totalmente definidos no código
        data = {
            "Categoria": ["A", "B", "A", "C", "B", "C"],
            "Valor": [10, 20, 15, 5, 30, 25],
            "Ano": [2022, 2022, 2023, 2023, 2024, 2024],
            "Descrição": [
                "Item A1",
                "Item B1",
                "Item A2",
                "Item C1",
                "Item B2",
                "Item C2"
            ]
        }

        return pd.DataFrame(data)
