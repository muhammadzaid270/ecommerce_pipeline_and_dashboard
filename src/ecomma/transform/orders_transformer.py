import logging
import pandas as pd
import pandera as pa
from ecomma.transform import BaseTransformer
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

class OrdersTransformer(BaseTransformer):
    # Expected columns in the orders dataframe, just for reference
    COLUMNS = [
        "Order_Id",
        "User_Id",
        "Status",
        "Total_Amount",
        "Subtotal_Before_Discount",
        "Discount_Applied",
        "Promo_Code_Used",
        "Product_Cost",
        "Payment_Method",
        "Shipping_Address",
        "Order_Date",
        "Delivery_Date",
    ]

    NULLABLE_COLS: list[str] = ["Promo_Code_Used", "Discount_Applied", "Delivery_Date"]
    DATE_COLS: list[str] = ["Order_Date", "Delivery_Date"]
    NUMERIC_COLS: list[str] = ["Total_Amount", "Subtotal_Before_Discount", "Discount_Applied", "Product_Cost"]
    ID_COLS: list[str] = ["Order_Id", "User_Id"]
    PROMO_COLS: list[str] = ["Promo_Code_Used", "Promo_Code_Used_Norm"]

    def __init__(self, file_path) -> None:
        super().__init__(file_path)
    
    #fix-me: Move outputs to a seperate method (_build_outputs)
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
        outputs: Dict[str, Any] = {
            "clean_df": df,
            "agg": {
                "by_user": self._agg_by(df, "User_Id"),
                "by_status": self._agg_by(df, "Status"),
                "by_promo_code_raw": self._agg_by(df, "Promo_Code_Used"),
                "by_promo_code_norm": self._agg_by(df, "Promo_Code_Used_Norm"),
                "by_payment_method": self._agg_by(df, "Payment_Method"),
            },
            "orders_over_time": {
                "daily": self._agg_date(df, "Order_Date", "D"),
                "weekly": self._agg_date(df, "Order_Date", "W-MON"),
                "monthly": self._agg_date(df, "Order_Date", "M"),
            },
            "delivery_over_time": {
                "daily": self._agg_date(df, "Delivery_Date", "D"),
                "weekly": self._agg_date(df, "Delivery_Date", "W-MON"),
                "monthly": self._agg_date(df, "Delivery_Date", "M"),
            },
        }

        total_revenue, total_discounts, net_revenue = self._revenue(df)
        outputs["revenue"] = {
            "total_revenue": total_revenue,
            "total_discounts": total_discounts,
            "net_revenue": net_revenue,
        }

        return outputs

    def _normalize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        # Columns
        ID_COLS = self.ID_COLS
        PROMO_COLS = self.PROMO_COLS
        DATE_COLS = self.DATE_COLS
        NUM_COLS = self.NUMERIC_COLS
        STR_COLS = [c for c in df.columns if c not in NUM_COLS + DATE_COLS]

        df["Promo_Code_Used_Norm"] = (
            df["Promo_Code_Used"]
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

        # Numeric Cleanup
        df[NUM_COLS] = df[NUM_COLS].astype("string")
        df[NUM_COLS] = (
            df[NUM_COLS]
            .str.replace(r"[^\d\.\-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )

        df["Discount_Applied"] = df["Discount_Applied"].fillna(0.0)

        logger.info("Cleaned orders data")
        return df

    def _agg_by(self, df: pd.DataFrame, col: str) -> pd.DataFrame:
        return (
            df.groupby(col)
            .agg(
                order_count=("Order_Id", "nunique"),  # How many unique orders
                total_amount_sum=("Total_Amount", "sum"),  # Total revenue
                total_amount_avg=("Total_Amount", "mean"),  # Average order value
                discount_total=("Discount_Applied", "sum"),  # Total discount given
                discount_avg=("Discount_Applied", "mean"),  # Avg discount per order
                product_cost_total=("Product_Cost", "sum"),  # Total cost of products
                product_cost_avg=("Product_Cost", "mean"),  # Avg product cost per order
            )
            .reset_index()
        )
    
    # Fix_me: Delivery date aggregation issue with orders without delivery dates (fixed)
    def _agg_date(self, df: pd.DataFrame, col: str, freq: str) -> pd.DataFrame:
        df = df[df[col].notna()].assign(
            date_bucket=df[col].dt.to_period(freq),
            delivery_days=(df["Delivery_Date"] - df["Order_Date"]).dt.days
        )
        return (
            df.groupby("date_bucket")
            .agg(
                order_count=("Order_Id", "nunique"),         # How many orders
                total_amount_sum=("Total_Amount", "sum"),    # Total revenue
                total_amount_avg=("Total_Amount", "mean"),   # Avg revenue per order
                discount_total=("Discount_Applied", "sum"),  # Total discounts
                discount_avg=("Discount_Applied", "mean"),   # Avg discount per order
                product_cost_total=("Product_Cost", "sum"),  # Total product cost
                product_cost_avg=("Product_Cost", "mean"),   # Avg product cost
                delivery_days_avg=("delivery_days", "mean")  # Avg delivery time in days
            )
            .reset_index()
        )

    def _revenue(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        total_revenue  = float(df["Total_Amount"].sum())
        total_discounts = float(df["Discount_Applied"].sum())
        net_revenue = total_revenue - total_discounts
        logger.info(
            "Total Revenue: %s, Total Discounts: %s, Net Revenue: %s",
            total_revenue, total_discounts, net_revenue
        )
        return total_revenue, total_discounts, net_revenue