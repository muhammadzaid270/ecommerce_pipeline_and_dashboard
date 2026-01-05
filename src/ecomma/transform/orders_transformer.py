import logging
import pandas as pd
import pandera as pa
from ecomma.transform import BaseTransformer
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)

class OrdersTransformer(BaseTransformer):
    def __init__(self, file_path) -> None:
        super().__init__(file_path)
    
    def transform(self, schema: pa.DataFrameSchema) -> Dict[str, Any]:
        df = (
            self.df
            .pipe(self._col_names)
            .pipe(self._drop_rows)
            .pipe(self._normalize_data)
            .pipe(self._normalize_dates)
            .pipe(self._validate, schema=schema)
        )
        self.df = df

        outputs: Dict[str, Any] = {
            "clean_df": df,
            "agg": {
                "by_user": self.agg_by("User_Id"),
                "by_status": self.agg_by("Status"),
                "by_promo_code": self.agg_by("Promo_Code_Used"),
                "by_payment_method": self.agg_by("Payment_Method"),
            },
            "orders_over_time": {
                "daily": self.agg_date("Order_Date", "D"),
                "weekly": self.agg_date("Order_Date", "W-MON"),
                "monthly": self.agg_date("Order_Date", "M"),
            },
            "delivery_over_time": {
                "daily": self.agg_date("Delivery_Date", "D"),
                "weekly": self.agg_date("Delivery_Date", "W-MON"),
                "monthly": self.agg_date("Delivery_Date", "M"),
            },
        }

        total_revenue, total_discounts, net_revenue = self.revenue(df)
        outputs["revenue"] = {
            "total_revenue": total_revenue,
            "total_discounts": total_discounts,
            "net_revenue": net_revenue,
        }

        return outputs

    # Expected columns in the orders dataframe, just for reference
    columns = [
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

    def _drop_rows(self) -> pd.DataFrame:
        df = self.df
        nullable_cols = ["Promo_Code_Used", "Discount_Applied", "Delivery_Date"]
        notnull_cols = [col for col in df.columns if col not in nullable_cols]

        initial_count = len(df)
        df.dropna(subset=notnull_cols, inplace=True)
        final_count = len(df)

        logger.info(f"Dropped {initial_count - final_count} rows with missing critical fields.")
        return df
    
    def _normalize_data(self) -> pd.DataFrame:
        df = self.df
        non_str_cols = [
            "Order_Date",
            "Total_Amount",
            "Subtotal_Before_Discount",
            "Discount_Applied",
            "Product_Cost",
            "Delivery_Date"
        ]
        str_cols = [c for c in df.columns if c not in non_str_cols]
        num_cols = ["Total_Amount", "Subtotal_Before_Discount", "Discount_Applied", "Product_Cost"]

        df[str_cols] = df[str_cols].astype("string")
        for col in str_cols:
            df[col] = df[col].str.strip().str.title()

        df[num_cols] = df[num_cols].astype("string")
        df[num_cols] = (
            df[num_cols]
            .str.replace(r"[^\d\.\-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )

        if "Discount_Applied" in df.columns:
            df["Discount_Applied"] = df["Discount_Applied"].fillna(0.0)

        logger.info("Normalized orders data")
        return df

    def _normalize_dates(self) -> pd.DataFrame:
        df = self.df
        if "Order_Date" in df.columns:
            df["Order_Date"] = pd.to_datetime(df["Order_Date"], errors="coerce")
        if "Delivery_Date" in df.columns:
            df["Delivery_Date"] = pd.to_datetime(df["Delivery_Date"], errors="coerce")
        logger.info("Converted Order_Date and Delivery_Date to datetime format.")
        return df

    # Fix_me: Add None check for schema (prevents runtime crash)
    def _validate(self, schema: pa.DataFrameSchema) -> pd.DataFrame:
        try:
            validated_df = schema.validate(self.df, lazy=True)
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

    def agg_by(self, col: str) -> pd.DataFrame:
        return (
            self.df.groupby(col)
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
    
    # Fix_me: Delivery date aggregation issue with orders without delivery dates.
    def agg_date(self, col: str, freq: str) -> pd.DataFrame:
        df = self.df.assign(
            date_bucket = self.df[col].dt.to_period(freq), 
            delivery_days = (self.df["Delivery_Date"] - self.df["Order_Date"]).dt.days
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

    def revenue(self, df: pd.DataFrame) -> Tuple[float, float, float]:
        total_revenue  = float(df["Total_Amount"].sum())
        total_discounts = float(df["Discount_Applied"].sum())
        net_revenue = total_revenue - total_discounts
        logger.info(
            "Total Revenue: %s, Total Discounts: %s, Net Revenue: %s",
            total_revenue, total_discounts, net_revenue
        )
        return total_revenue, total_discounts, net_revenue