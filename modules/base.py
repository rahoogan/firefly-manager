from pandas import DataFrame
from typing import List


class BaseProcessor:
    def process(data: DataFrame, all_lines: List[str]) -> DataFrame:
        return data

    def preprocess(data: DataFrame, all_lines: List[str]) -> DataFrame:
        return data
