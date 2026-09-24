from dataclasses import dataclass

import pandas as pd

from fielddash.core.config import Config
from fielddash.core.model import Dataset


@dataclass
class PageContext:
    config: Config
    dataset: Dataset      # complete data + schema
    df: pd.DataFrame      # data after sidebar filters
    filters: list         # active filter labels
