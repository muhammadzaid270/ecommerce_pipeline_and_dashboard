import logging
import pandas as pd

logger = logging.getLogger(__name__)

class BaseTransformer:
    def __init__(self, file_path) -> None:
        self.file_path = file_path
        self.df = self._dataframe()

    def _dataframe(self) -> pd.DataFrame:
        if self.file_path.suffix == ".jsonl":
            df = pd.read_json(self.file_path, lines=True)
        elif self.file_path.suffix == ".csv":
            df = pd.read_csv(self.file_path)
        else:
            raise ValueError(f"Unsupported file format: {self.file_path.suffix}")
        return df