import logging
import pandas as pd
from ecomma.transform import BaseTransformer
from typing import Tuple

logger = logging.getLogger(__name__)

class PromotionsTransformer(BaseTransformer):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def transform(self) -> Tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame,
        pd.DataFrame
    ]:
        self.df = (
            self.df
            .pipe(self._drop_rows)
            .pipe(self._normalize_data)
            .pipe(self._normalize_dates)
            .pipe(self.validate, schema=None)
        )
        agg_promo_code = self.aggregate_by("Promo_Code")
        agg_promo_type = self.aggregate_by("Promo_Type")
        agg_category = self.aggregate_by("Category")
        agg_status = self.aggregate_by("Status")

        start_daily = self.agg_date("Start_Date", "D")
        start_weekly = self.agg_date("Start_Date", "W")
        start_monthly = self.agg_date("Start_Date", "M")
        end_daily = self.agg_date("End_Date", "D")
        end_weekly = self.agg_date("End_Date", "W")
        end_monthly = self.agg_date("End_Date", "M")

        return (
            self.df,
            agg_promo_code,
            agg_promo_type,
            agg_category,
            agg_status,
            start_daily,
            start_monthly,
            start_weekly,
            end_daily,
            end_weekly,
            end_monthly
        )

    columns = [
        # String Columns
        "Promo_ID",
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
        initial_count = len(self.df)
        nullable_cols = ["Promo_Code", "Discount_Value", "Category", "Min_Purchase", "Usage_Limit"]
        notnull_cols = [col for col in self.df.columns if col not in nullable_cols]
        self.df.dropna(subset=notnull_cols, inplace=True)
        final_count = len(self.df)
        logging.info(f"Dropped {initial_count - final_count} rows due to missing critical fields.")
        return self.df

    def _normalize_data(self) -> pd.DataFrame:
        self.df.columns = (
            self.df.columns
            .str.strip()
            .str.title()
            .replace(" ", "_")
        )

        str_cols = ["Promo_ID", "Promo_Code", "Promo_Type", "Category", "Status"]
        self.df[str_cols] = (
            self.df[str_cols]
            .astype('string')
            .str.strip()
            .str.title()
        )

        num_cols = ["Discount_Value", "Min_Purchase", "Usage_Limit", "Times_Used"]
        for col in num_cols:
            self.df[col] = pd.to_numeric(
                self.df[col].astype('string').str.extract(r'(-?\d+(?:\.\d+)?)', expand=False),
                errors='coerce'
            )
        logging.info("Normalized promotions data columns.")
        return self.df

    def _normalize_dates(self) -> pd.DataFrame:
        self.df["Start_Date"] = pd.to_datetime(self.df["Start_Date"], errors="coerce")
        self.df["End_Date"] = pd.to_datetime(self.df["End_Date"], errors="coerce")
        logging.info("Converted Start_Date and End_Date to datetime format.")
        return self.df
    
    def validate(self, schema) -> None:
        try:
            schema.validate(self.df, lazy=True)
            logging.info("Promotions data validation successful.")
        except pd.errors.SchemaErrors as e:
            logger.error(f"Marketing Spent data validation errors:\n{e.failure_cases}")
            raise

    def aggregate_by(self, col: str) -> pd.DataFrame:
        return (
            self.df.groupby(col)
            .agg(
                promo_count=("Promo_ID", "nunique"),
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
                promo_count=("Promo_ID", "nunique"),
                total_times_used=("Times_Used", "sum"),
                total_discount_given=("Discount_Value", "sum"),
                active_promos=("Status", lambda x: (x == "Active").sum()),
                earliest_start=("Start_Date", "min"),
                latest_end=("End_Date", "max"),
            )
            .reset_index()
        )