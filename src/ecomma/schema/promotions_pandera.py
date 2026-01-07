import pandera as pa
from pandera.typing import Series

class PromoSchema(pa.DataFrameModel):
    # Mandatory (cannot be null)
    Promo_Id: Series[str] = pa.Field(unique=True, nullable=False)
    Promo_Type: Series[str] = pa.Field(
        isin=["free_shipping", "fixed_amount", "bogo", "bundle_deal", "percentage_off"], 
        nullable=False
    )
    Start_Date: Series[pa.DateTime] = pa.Field(nullable=False)
    End_Date: Series[pa.DateTime] = pa.Field(nullable=False)
    Times_Used: Series[float] = pa.Field(ge=0, nullable=False)
    Status: Series[str] = pa.Field(nullable=False)

    # Optional (can be null)
    Promo_Code: Series[str] = pa.Field(nullable=True)
    Discount_Value: Series[float] = pa.Field(ge=0, nullable=True)
    Category: Series[str] = pa.Field(nullable=True)
    Min_Purchase: Series[float] = pa.Field(ge=0, nullable=True)
    Usage_Limit: Series[float] = pa.Field(ge=0, nullable=True)

    class Config:
        strict = True
        coerce = True