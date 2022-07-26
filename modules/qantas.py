from pandas import DataFrame
from typing import List
from modules.base import BaseProcessor
import re


start_rgx = re.compile(r".*?Statement Begins\s+[0-9]{1,2}\s+[A-Za-z]*?\s+([0-9]{4})")
end_rgx = re.compile(r".*?Statement Ends\s+[0-9]{1,2}\s+[A-Za-z]*?\s+([0-9]{4})")


class QantasProcessor(BaseProcessor):
    def process(data: DataFrame, all_lines: List[str]) -> DataFrame:
        # Get statement start/end date
        lines = [x for x in all_lines if "Statement " in x]
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
        if start == end:
            data["Date"] = data["Date"] + " " + start
        else:
            for index, row in data.iterrows():
                if row["Date"].lower().startswith("jan"):
                    data.iloc[index, data.columns.get_loc("Date")] = (
                        row["Date"] + " " + end
                    )
                else:
                    data.iloc[index, data.columns.get_loc("Date")] = (
                        row["Date"] + " " + start
                    )
        return data
