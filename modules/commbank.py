import pandas as pd
import numpy as np
from pandas import DataFrame
from typing import List
from modules.base import BaseProcessor
import re


start_rgx = re.compile(r".*?Statement Period\s+[0-9]{1,2}\s+[A-Za-z]*?\s+([0-9]{4})")
end_rgx = re.compile(r".*?Statement Period.*?-\s+[0-9]{1,2}\s+[A-Za-z]*?\s+([0-9]{4})")


class CommbankProcessor(BaseProcessor):
    def preprocess(data: DataFrame, all_lines: List[str]) -> DataFrame:
        # Get statement start/end date
        lines = [x for x in all_lines if "Statement Period" in x]
        start, end = None, None
        for line in lines:
            if start is None:
                s = start_rgx.match(line)
                if s and s.groups():
                    start = s[1]
            if end is None:
                e = end_rgx.match(line)
                if e and e.groups():
                    end = e[1]
        # Add year to dates
        if start == end:
            data["Date"] = data["Date"] + " " + start
        else:
            for index, row in data.iterrows():
                if not (pd.isna(row["Date"]) or pd.isnull(row["Date"])):
                    if row["Date"].split()[-1].lower().startswith("jan"):
                        data.iloc[index, data.columns.get_loc("Date")] = (
                            row["Date"] + " " + end
                        )
                    else:
                        data.iloc[index, data.columns.get_loc("Date")] = (
                            row["Date"] + " " + start
                        )
        data = data.drop(data[data.Date == "Date"].index)

        # Merge Unnamed columns with previous column
        for idx, col in enumerate(data.columns):
            if col.startswith("Unnamed") and idx > 0:
                data[data.columns[idx - 1]] = (
                    data[data.columns[idx - 1]].fillna("").astype(str)
                )
                data[data.columns[idx]] = data[data.columns[idx]].fillna("").astype(str)
                data[data.columns[idx - 1]] = (
                    +data[data.columns[idx - 1]] + data[data.columns[idx]]
                )
                data = data.drop(data.columns[idx], axis=1)

        # Merge null columns
        null_columns = pd.isnull(data).sum()
        null_columns = null_columns[null_columns == len(data)]
        new_column = " ".join(
            [x for x in null_columns.index if not x.startswith("Unnamed")]
        )
        data = data.drop(null_columns.index, axis=1)
        if not data.columns.empty:
            if data.columns[-1].startswith("Unnamed"):
                data = data.rename(columns={data.columns[-1]: new_column})
            else:
                data = data.rename(
                    columns={data.columns[-1]: new_column + data.columns[-1]}
                )
        data = data.replace(r"^\s*$", np.nan, regex=True)
        return data
