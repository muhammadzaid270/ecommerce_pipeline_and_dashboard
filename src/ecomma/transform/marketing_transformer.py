import logging
import pandas as pd
import pandera as pa
from ecomma.transform import BaseTransformer
from typing import Tuple, Dict, Any

class MarketingTransformer(BaseTransformer):
    # Expected columns in the marketing dataframe, just for reference
    COLUMNS = [
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

    NULLABLE_COLS = ["Promo_Code_Linked", "Target_Region"]
    STR_COLS = ["Campaign_ID", "Channel", "Target_Region", "Campaign_Type", "Promo_Code_Linked"]
    NUMERIC_COLS = ["Budget_Spend", "Impressions", "Clicks"]
    ID_COLS = ["Campaign_ID"]
    DATE_COLS = ["Start_Date", "End_Date"]
    PROMO_COLS = ["Promo_Code_Linked", "Promo_Code_Linked_Norm"]

    def __init__(self, file_path) -> None:
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
                "by_target_region": self.agg_by_target_region(),
                "by_channel": self.agg_by_channel(),
                "by_campaign_type": self.agg_by_campaign_type(),
            },
            "totals": self.totals()
        }
        return output

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        STR_COLS = self.STR_COLS
        NUM_COLS = self.NUMERIC_COLS
        ID_COLS = self.ID_COLS
        PROMO_COLS = self.PROMO_COLS

        df["Promo_Code_Linked_Norm"] = (
            df["Promo_Code_Linked"]
            .astype("string")
            .fillna("NO_PROMO")
            .str.strip()
            .str.replace(r"\s+", "_", regex=True)
            .str.upper()
        )

        df[STR_COLS] = df[STR_COLS].astype("string")
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
            .replace(r"[^\d\.\-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )
        logging.info("Normalized marketing data columns.")
        return df
    
    #fix_me: One general agg function through which you can aggregate data, and agg_by_date
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