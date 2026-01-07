import logging
import pandas as pd
import pandera as pa
from ecomma.transform import BaseTransformer
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

class PromotionsTransformer(BaseTransformer):
    # Expected columns in the promotions dataframe, just for reference
    COLUMNS = [
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

    NULLABLE_COLS = ["Promo_Code", "Discount_Value", "Category", "Min_Purchase", "Usage_Limit"]
    NUMERIC_COLS = ["Discount_Value", "Min_Purchase", "Usage_Limit", "Times_Used"]
    STR_COLS = ["Promo_Id", "Promo_Code", "Promo_Type", "Category", "Status"]
    ID_COLS = ["Promo_Id"]
    DATE_COLS = ["Start_Date", "End_Date"]
    PROMO_COLS = ["Promo_Code", "Promo_Code_Norm"]

    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def transform(self, schema: pa.DataFrameSchema) -> Dict[str, Any]:
        NON_NULL_COLS = [col for col in self.df.columns if col not in self.NULLABLE_COLS]

        df = (
            self.df
            .pipe(self._drop_rows, NON_NULL_COLS)
            .pipe(self._normalize_data)
            .pipe(self._normalize_dates, self.DATE_COLS)
            .pipe(self._validate, schema)
        )
        self.df = df

        return self._build_outputs(df)

    def _build_outputs(self, df: pd.DataFrame) -> Dict[str, Any]:
        output: Dict[str, Any] = {
            "clean_df": df,
            "agg": {
                "by_promo_code": self.agg_by(df, "Promo_Code"),
                "by_promo_type": self.agg_by(df, "Promo_Type"),
                "by_category": self.agg_by(df, "Category"),
                "by_status": self.agg_by(df, "Status"),
            },
            "start_over_time": {
                "daily": self.agg_date(df, "Start_Date", "D"),
                "weekly": self.agg_date(df, "Start_Date", "W-MON"),
                "monthly": self.agg_date(df, "Start_Date", "M"),
            },
            "end_over_time": {
                "daily": self.agg_date(df, "End_Date", "D"),
                "weekly": self.agg_date(df, "End_Date", "W-MON"),
                "monthly": self.agg_date(df, "End_Date", "M"),
            },
        }

        return output

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        NUM_COLS = self.NUMERIC_COLS
        STR_COLS = self.STR_COLS
        ID_COLS = self.ID_COLS
        PROMO_COLS = self.PROMO_COLS

        df["Promo_Code_Norm"] = (
            df["Promo_Code"]
            .astype('string')
            .fillna("NO_PROMO")
            .str.strip()
            .str.replace(r"\s+", "_", regex=True)
            .str.upper()
        )

        df[STR_COLS] = df[STR_COLS].astype('string')
        for col in STR_COLS:
            if col in ID_COLS or col in PROMO_COLS:
                df[col] = df[col].str.strip()
            else:
                df[col] = (
                    df[col]
                    .str.strip()
                    .str.replace(r"\s+", "_", regex=True)
                    .str.title()
                )
                
        df[NUM_COLS] = df[NUM_COLS].astype('string')
        df[NUM_COLS] = (
            df[NUM_COLS]
            .str.replace(r"[^\d\.\-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )

        df["Discount_Value"] = df["Discount_Value"].fillna(0.0)

        logging.info("Normalized promotions data.")
        return df
    
    def agg_by(self, df:pd.DataFrame, col: str) -> pd.DataFrame:
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

    def agg_date(self, df: pd.DataFrame, col: str, freq: str) -> pd.DataFrame:
        df = df.assign(date_bucket = df[col].dt.to_period(freq))
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