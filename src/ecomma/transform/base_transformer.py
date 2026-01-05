import logging
import pandas as pd
from typing import Tuple

logger = logging.getLogger(__name__)

#do it later: move some generic methods here from child classes such as _drop_rows, _validate etc.
class BaseTransformer:
    def __init__(self, file_path) -> None:
        self.file_path = file_path
        self.df = self._dataframe()
        self.df = self._col_names()

    def _dataframe(self) -> pd.DataFrame:
        file_path = self.file_path
        if file_path.suffix == ".jsonl":
            df = pd.read_json(file_path, lines=True)
        elif file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
        return df
    
    def _col_names(self) -> Tuple[pd.DataFrame, list]:
        df = self.df
        df.columns = (
            df.columns
            .str.strip()
            .str.title()
            .replace(r"\s+", "_", regex=True)
        )
        # cols = df.columns.tolist()
        return df