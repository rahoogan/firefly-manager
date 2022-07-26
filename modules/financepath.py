from pandas import DataFrame
from typing import List
from modules.base import BaseProcessor


class FPProcessor(BaseProcessor):
    def process(data: DataFrame, all_lines: List[str]) -> DataFrame:
        return data
