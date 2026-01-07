import logging
import pandas as pd
import pandera as pa
from typing import Tuple, Any

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
    
    def _drop_rows(self, df: pd.DataFrame, notnull_cols: list[str]) -> pd.DataFrame:
        initial_count = len(df)
        df = df.dropna(subset=notnull_cols)
        final_count = len(df)
        logger.info(f"Dropped {initial_count - final_count} rows with missing critical fields.")
        return df
    
    def _normalize_dates(self, df: pd.DataFrame, date_cols: list[str]) -> pd.DataFrame:
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')
        return df
    
    def _validate(self, df: pd.DataFrame, schema: pa.DataFrameSchema) -> pd.DataFrame:
        if schema is None:
            raise ValueError("No schema provided for validation. Must provide a valid pandera DataFrameSchema.")
        try:
            validated_df = schema.validate(df, lazy=True)
            logger.info(f"Validated {len(validated_df)} rows successfully.")
            return validated_df
        
        except pa.errors.SchemaErrors as e:
            logger.error("Schema validation failed!")
            logger.error(f"Number of failures: {len(e.failure_cases)}")
                
            # Failure cases (rows that failed validation)
            if not e.failure_cases.empty:
                logger.error(f"Failure cases:\n{e.failure_cases.to_string()}")
                
            # Schema errors
            if e.schema_errors:
                for col, errors in e.schema_errors.items():
                    logger.error(f"Column '{col}' errors: {errors}")
                
            # Re-raise with contextual information
            raise ValueError(f"Data validation failed with {len(e.failure_cases)} errors") from e
