import logging
import pandas as pd
from ecomma.transform import BaseTransformer


logger = logging.getLogger(__name__)

class OrdersTransformer(BaseTransformer):
    def __init__(self, file_path) -> None:
        super().__init__(file_path)
    
    def transform(self) -> pd.DataFrame:
        self.df = (
            self.df
            .pipe(self._columns_rename)
            .pipe(self._drop_rows)
            .pipe(self._normalize_data)
            .pipe(self._normalize_dates)
            .pipe(self.validate, schema=None)
        )
        agg_user = self.agg_by("UserID")
        agg_status = self.agg_by("Status")
        agg_promo_code = self.agg_by("PromoCodeUsed")
        agg_payment_method = self.agg_by("PaymentMethod")

        return self.df, agg_user, agg_status, agg_promo_code, agg_payment_method

    column_mappings = {
        "order_id": "OrderID",
        "user_id": "UserID",
        "order_date": "Order_Date",
        "status": "Status",
        "total_amount": "Total_Amount",
        "subtotal_before_discount": "Subtotal_Before_Discount",
        "discount_applied": "Discount_Applied",
        "promo_code_used": "Promo_Code_Used",
        "product_cost": "Product_Cost",
        "payment_method": "Payment_Method",
        "shipping_address": "Shipping_Address",
        "delivery_date": "Delivery_Date",
    }

    def _columns_rename(self) -> None:
        self.df.rename(columns=self.column_mappings, inplace=True)
        logger.info("Columns renamed according to mapping.")

    def _drop_rows(self, nullable_cols: list[str] = ["PromoCodeUsed", "DiscountApplied", "DeliveryDate"]) -> None:
        i_rows = len(self.df)
        notnull_cols = [col for col in self.df.columns if col not in nullable_cols]
        self.df.dropna(subset=notnull_cols, inplace=True)
        f_rows = len(self.df)
        logger.info(f"Dropped {i_rows - f_rows} rows with missing critical fields.")

    def _normalize_data(self) -> None:
        self.df.columns = self.df.columns.str.strip().str.title().replace(" ", "_")
        non_str_cols = ["UserID", "Order_Date","Total_Amount", "Subtotal_Before_Discount", "Discount_Applied", "Product_Cost", "Delivery_Date"]
        str_cols = [col for col in self.df.columns if col not in non_str_cols]
        self.df[str_cols] = self.df[str_cols].astype("string").str.strip().str.title()
        num_cols = ["UserID", "Total_Amount", "Subtotal_Before_Discount", "Discount_Applied", "Product_Cost"]
        self.df[num_cols] = (
            self.df[num_cols]
            .astype("int64")
            .replace(r"[^\d.-]", "", regex=True)
            .apply(pd.to_numeric, errors="coerce")
        )
        logger.info("Normalized order data columns.")

    def _normalize_dates(self) -> None:
        self.df["OrderDate"] = pd.to_datetime(self.df["OrderDate"], errors="coerce")
        self.df["DeliveryDate"] = pd.to_datetime(self.df["DeliveryDate"], errors="coerce")
        logger.info("Converted OrderDate and DeliveryDate to datetime format.")
    
    def validate(self, schema) -> None:
        try:
            schema.validate(self.df, lazy=True)
            logger.info("Data validation successful.")
        except pd.errors.SchemaErrors as e:
            logger.error(f"Data validation errors:\n{e.failure_cases}")
            raise
    
    def agg_by(self, col: str) -> pd.DataFrame:
        return (
            self.df.groupby(col)
            .agg(
                order_count=("OrderID", "nunique"),  # How many unique orders
                total_amount_sum=("Total_Amount", "sum"),  # Total revenue
                total_amount_avg=("Total_Amount", "mean"),  # Average order value
                discount_total=("Discount_Applied", "sum"),  # Total discount given
                discount_avg=("Discount_Applied", "mean"),  # Avg discount per order
                product_cost_total=("Product_Cost", "sum"),  # Total cost of products
                product_cost_avg=("Product_Cost", "mean"),  # Avg product cost per order
            )
            .reset_index()
        )
    
    def agg_date_range(self, col: str, freq: str) -> pd.DataFrame:
        df = self.df.assign(
            date_bucket = self.df[col].dt.to_period(freq), 
            delivery_days = (pd.to_datetime(self.df["Delivery_Date"]) - pd.to_datetime(self.df["Order_Date"])).dt.days
            )
        return (
            df.groupby(col)
            .agg(
                order_count=("OrderID", "nunique"),          # How many orders
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
        
    def revenue(self, agg_df):
        total_revenue  = agg_df["Total_Amount"].sum()
        total_discounts = self.df["Discount_Applied"].sum()
        net_revenue = total_revenue - total_discounts
        logger.info(f"Total Revenue: {total_revenue}, Total Discounts: {total_discounts}, Net Revenue: {net_revenue}")
        return total_revenue, total_discounts, net_revenue
        