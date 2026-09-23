from dataclasses import dataclass

import pandas as pd

from geocoleta.core.config import Config
from geocoleta.core.model import Dataset


@dataclass
class PageContext:
    config: Config
    dataset: Dataset      # dados completos + schema
    df: pd.DataFrame      # dados após os filtros da barra lateral
    filters: list         # rótulos dos filtros ativos
