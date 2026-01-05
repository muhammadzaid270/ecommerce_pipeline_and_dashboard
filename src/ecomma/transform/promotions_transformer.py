import logging
import pandas as pd
import pandera as pa
from ecomma.transform import BaseTransformer
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class PromotionsTransformer(BaseTransformer):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def transform(self, schema: pa.DataFrameSchema) -> Dict[str, Any]:
        df = (
            self.df
            .pipe(self._drop_rows)
            .pipe(self._normalize_data)
            .pipe(self._normalize_dates)
            .pipe(self._validate, schema=schema)
        )
        self.df = df

        output: Dict[str, Any] = {
            "clean_df": df,
            "agg": {
                "by_promo_code": self.agg_by("Promo_Code"),
                "by_promo_type": self.agg_by("Promo_Type"),
                "by_category": self.agg_by("Category"),
                "by_status": self.agg_by("Status"),
            },
            "start_over_time": {
                "daily": self.agg_date("Start_Date", "D"),
                "weekly": self.agg_date("Start_Date", "W-MON"),
                "monthly": self.agg_date("Start_Date", "M"),
            },
            "end_over_time": {
                "daily": self.agg_date("End_Date", "D"),
                "weekly": self.agg_date("End_Date", "W-MON"),
                "monthly": self.agg_date("End_Date", "M"),
            },
        }

        return output

    columns = [
        # String Columns
        "Promo_Id",
        "Promo_Code",
        "Promo_Type",
        "Category",
        "Status",
        # Numeric Columns
        "Discount_Value",
        "Min_Purchase",
        "Usage_Limit",
        "Times_Used",
        # Date Columns
        "Start_Date",
        "End_Date"
    ]

    def _drop_rows(self) -> pd.DataFrame:
        df = self.df
        initial_count = len(df)
        nullable_cols = ["Promo_Code", "Discount_Value", "Category", "Min_Purchase", "Usage_Limit"]
        notnull_cols = [col for col in self.df.columns if col not in nullable_cols]
        df = df.dropna(subset=notnull_cols)
        final_count = len(df)
        logging.info(f"Dropped {initial_count - final_count} rows due to missing critical fields.")
        return df

    def _normalize_data(self) -> pd.DataFrame:
        df = self.df
        str_cols = ["Promo_Id", "Promo_Code", "Promo_Type", "Category", "Status"]
        df[str_cols] = df[str_cols].astype('string')
        df[str_cols] = (
            df[str_cols]
            .str.strip()
            .str.title()
        )

        num_cols = ["Discount_Value", "Min_Purchase", "Usage_Limit", "Times_Used"]
        df[num_cols] = df[num_cols].astype('string')
        for col in num_cols:
            df[col] = pd.to_numeric(
                df[col].str.extract(r'(-?\d+(?:\.\d+)?)', expand=False),
                errors='coerce'
            )
        logging.info("Normalized promotions data.")
        return df

    def _normalize_dates(self) -> pd.DataFrame:
        df = self.df
        df["Start_Date"] = pd.to_datetime(df["Start_Date"], errors="coerce")
        df["End_Date"] = pd.to_datetime(df["End_Date"], errors="coerce")
        logging.info("Converted Start_Date and End_Date to datetime format.")
        return df
    
    def _validate(self, schema) -> None:
        df = self.df
        try:
            schema.validate(df, lazy=True)
            logging.info("Promotions data validation successful.")
            return df
        except pa.errors.SchemaErrors as e:
            logger.error(f"Marketing Spent data validation errors:\n{e.failure_cases}")
            raise

    def agg_by(self, col: str) -> pd.DataFrame:
        df = self.df
        return (
            df.groupby(col)
            .agg(
                promo_count=("Promo_Id", "nunique"),
                total_times_used=("Times_Used", "sum"),
                avg_times_used=("Times_Used", "mean"),
                total_discount_given=("Discount_Value", "sum"),
                avg_discount_value=("Discount_Value", "mean"),
                avg_min_purchase=("Min_Purchase", "mean"),
            )
            .reset_index()
        )
    
    def agg_date(self, col: str, freq: str) -> pd.DataFrame:
        df = self.df.assign(date_bucket = self.df[col].dt.to_period(freq))
        return (
            df.groupby("date_bucket")
            .agg(
                promo_count=("Promo_Id", "nunique"),
                total_times_used=("Times_Used", "sum"),
                total_discount_given=("Discount_Value", "sum"),
                active_promos=("Status", lambda x: (x == "Active").sum()),
                earliest_start=("Start_Date", "min"),
                latest_end=("End_Date", "max"),
            )
            .reset_index()
        )