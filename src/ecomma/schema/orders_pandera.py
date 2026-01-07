import pandera as pa
from pandera.typing import Series

class OrderSchema(pa.DataFrameModel):
    # Mandatory (cannot be null)
    Order_Id: Series[int] = pa.Field(unique=True, nullable=False)
    User_Id: Series[int] = pa.Field(gt=0, nullable=False)
    Order_Date: Series[pa.DateTime] = pa.Field(nullable=False)
    Status: Series[str] = pa.Field(
        isin=["COMPLETED", "PENDING", "RETURNED", "CANCELLED", "SHIPPED"], 
        nullable=False
    )
    Payment_Method: Series[str] = pa.Field(
        isin=["Apple Pay", "Debit Card", "Credit Card", "PayPal"], 
        nullable=False
    )
    Total_Amount: Series[float] = pa.Field(ge=0, nullable=False)
    Product_Cost: Series[float] = pa.Field(ge=0, nullable=False)
    Subtotal_Before_Discount: Series[float] = pa.Field(ge=0, nullable=False)
    Shipping_Address: Series[str] = pa.Field(nullable=False)

    # Optional (can be null)
    Delivery_Date: Series[pa.DateTime] = pa.Field(nullable=True)
    Discount_Applied: Series[float] = pa.Field(ge=0, nullable=True)
    Promo_Code_Used: Series[str] = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = True