import logging
from ecomma.transform import OrdersTransformer, PromotionsTransformer, MarketingTransformer
from ecomma.schema import OrderSchema, PromoSchema, MarketingSchema
from pathlib import Path
from typing import Iterator, Tuple
import os

'''
fix me:
1) give schemas to transformers (solved)
2) receiving outputs from transformers
'''

logger = logging.getLogger(__name__)

TRANSFORMER_MAPPING = {
    "orders": OrdersTransformer,
    "marketing": MarketingTransformer,
    "promotions": PromotionsTransformer,
}

SCHEMA_MAPPING = {
    "orders": OrderSchema.get_schema(),
    "marketing": MarketingSchema.get_schema(),
    "promotions": PromoSchema.get_schema(),
}

def search_files(directory: str = RAW_DATA, extension: Tuple[str, str] = (".jsonl", ".csv")) -> Iterator[Path]:
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                yield Path(root) / file

def infer_schema(file_path: Path) -> str:
    return file_path.parent.name

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
        schema = SCHEMA_MAPPING[infer_schema(file_path)]

if __name__ == "__main__":
    from ecomma.settings.config import RAW_DATA, setup_logging
    setup_logging()
    