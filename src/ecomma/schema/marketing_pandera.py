import pandera as pa
from pandera.typing import Series

class MarketingSchema(pa.DataFrameModel):
    Campaign_ID: Series[str] = pa.Field(unique=True, nullable=False)
    Channel: Series[str] = pa.Field(nullable=False)
    Start_Date: Series[pa.DateTime] = pa.Field(nullable=False)
    End_Date: Series[pa.DateTime] = pa.Field(nullable=False)
    Budget_Spend: Series[float] = pa.Field(ge=0, nullable=False)
    Impressions: Series[float] = pa.Field(ge=0, nullable=False)
    Clicks: Series[float] = pa.Field(ge=0, nullable=False)
    Campaign_Type: Series[str] = pa.Field(nullable=False)
    Target_Region: Series[str] = pa.Field(nullable=True)
    Promo_Code_Linked: Series[str] = pa.Field(nullable=True)

    class Config:
        strict = True
        coerce = True