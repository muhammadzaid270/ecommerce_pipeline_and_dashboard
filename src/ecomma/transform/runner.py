import logging
from ecomma.settings.config import RAW_DATA, setup_logging
from ecomma.transform import OrdersTransformer, PromotionsTransformer, MarketingTransformer
from ecomma.schema import OrdersSchema, PromotionsSchema, MarketingSchema
from pathlib import Path
from typing import Iterator
import os

logger = logging.getLogger(__name__)
setup_logging()

def search_files(directory: str = RAW_DATA, extension: tuple[str] = (".jsonl", ".csv")) -> Iterator[Path]:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                yield Path(root) / file

def infer_schema(file_path: Path) -> str:
    return file_path.parent.name

TRANSFORMER_MAPPING = {
    "orders": OrdersTransformer,
    "marketing": MarketingTransformer,
    "promotions": PromotionsTransformer,
}

def map_transformer(file_path: Path) -> object:
    schema = infer_schema(file_path)
    transformer_class = TRANSFORMER_MAPPING.get(schema)
    if not transformer_class:
        raise ValueError(f"No transformer found for schema: {schema}")
    return transformer_class(file_path)

def load_files() -> None:
    for file_path in search_files(RAW_DATA, (".jsonl", ".csv")):
        logger.info(f"Loading file: {file_path}")
        transformer_obj = map_transformer(file_path)
        transformer_obj.transform() # A critical thing to do later! regarding schema validation

        if transformer_obj == OrdersSchema(file_path):
            transformer_obj.validate(schema=OrdersSchema)
            agg_df = transformer_obj.aggregate()
            total_rev, total_discounts, net_rev = transformer_obj.revenue(agg_df)

        if transformer_obj == MarketingSchema(file_path):
            transformer_obj.validate(schema=MarketingSchema)