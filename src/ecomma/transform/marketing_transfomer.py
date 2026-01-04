import logging
import pandas as pd
from ecomma.transform import BaseTransformer
from typing import Tuple

class MarketingTransformer(BaseTransformer):
    def __init__(self, file_path) -> None:
        super().__init__(file_path)
    
    def transform(self) -> pd.DataFrame:
        self.df = (
            self.df
            .pipe(self._drop_rows)
            .pipe(self._normalize_data)
            .pipe(self._clean_dates)
            .pipe(self.validate, schema=None)
        )
        agg_campaign = self.agg_by_campaign()
        agg_region = self.agg_by_target_region()
        agg_channel = self.agg_by_channel()
        agg_type = self.agg_by_campaign_type()
        total_budget, total_impressions, total_clicks = self.totals()

        return self.df

    columns = [
        "Campaign_ID",
        "Channel",
        "Target_Region",
        "Start_Date",
        "End_Date",
        "Budget_Spend",
        "Impressions",
        "Clicks",
        "Campaign_Type",
        "Promo_Code_Linked"
    ]

    def _drop_rows(self, nullable_cols: list[str] = ["Promo_Code_Linked", "Target_Region"]) -> None:
        initial_count = len(self.df)
        notnull_cols = [col for col in self.df.columns if col not in nullable_cols]
        self.df.dropna(subset=notnull_cols, inplace=True)
        final_count = len(self.df)
        logging.info(f"Dropped {initial_count - final_count} rows due to missing critical fields.")

    def _normalize_data(self) -> None:
        self.df = self.df.columns.str.strip().str.title().replace(" ", "_")
        non_str_col = ["Start_Date", "End_Date", "Budget_Spend", "Impressions", "Clicks"]
        str_cols = [col for col in self.df.columns if col not in non_str_col]
        self.df[str_cols] = self.df[str_cols].astype("string").str.strip().str.title()
        num_cols = ["Budget_Spend", "Impressions", "Clicks"]
        self.df[num_cols] = (
            self.df[num_cols]
            .astype("string")
            .replace(r"[^\d.-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )
        logging.info("Normalized marketing data columns.")

    def _normalize_dates(self) -> None:
        self.df["Start_Date"] = pd.to_datetime(self.df["Start_Date"], errors="coerce")
        self.df["End_Date"] = pd.to_datetime(self.df["End_Date"], errors="coerce")
        logging.info("Converted Start_Date and End_Date to datetime format.")
    
    def validate(self, schema) -> None:
        try:
            schema.validate(self.df, lazy=True)
            logging.info("Marketing data validation successful.")
        except pd.errors.SchemaErrors as e:
            logging.error(f"Marketing Spent data validation errors:\n{e.failure_cases}")
            raise
    
    def agg_by_target_region(self) -> pd.DataFrame:
        agg_df = self.df.groupby("Target_Region").agg({
            "Budget_Spend": "sum",
            "Impressions": "sum",
            "Clicks": "sum"
        }).reset_index()
        logging.info("Aggregated marketing data by Target_Region.")
        return agg_df

    def agg_by_channel(self) -> pd.DataFrame:
        agg_df = self.df.groupby("Channel").agg({
            "Budget_Spend": "sum",
            "Impressions": "sum",
            "Clicks": "sum"
        }).reset_index()
        logging.info("Aggregated marketing data by Channel.")
        return agg_df
    
    def agg_by_campaign_type(self) -> pd.DataFrame:
        agg_df = self.df.groupby("Campaign_Type").agg({
            "Budget_Spend": "sum",
            "Impressions": "sum",
            "Clicks": "sum"
        }).reset_index()
        logging.info("Aggregated marketing data by Campaign_Type.")
        return agg_df

    def totals(self) -> Tuple[float, int, int]:
        total_budget = self.df["Budget_Spend"].sum()
        total_impressions = self.df["Impressions"].sum()
        total_clicks = self.df["Clicks"].sum()
        logging.info(f"Total Budget Spend: {total_budget}, Total Impressions: {total_impressions}, Total Clicks: {total_clicks}")
        return total_budget, total_impressions, total_clicks