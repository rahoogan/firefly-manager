import importlib
import re
import io
import json
import pdftotext
from pathlib import Path
from typing import List
import pandas as pd
import argparse
from pydantic import BaseModel


class Config(BaseModel):
    files_whitelist: List[str]
    files_blacklist: List[str]
    transaction_blocks: List[List[str]]
    ignore_lines: List[str]
    post_process: str = None
    pre_process: str = None
    column_number: int = None


def accept_file(filename: Path, files_whitelist: List[str], files_blacklist: List[str]):
    if files_whitelist and [x for x in files_whitelist if x in filename.name.lower()]:
        return True
    if files_blacklist and [x for x in files_blacklist if x in filename.name.lower()]:
        return False
    if not files_whitelist and not files_blacklist:
        return True
    return False


def get_input_files(input_path: str, config: Config):
    # Get list of all input files
    files_whitelist = config.files_whitelist
    files_blacklist = config.files_blacklist
    input_files = []
    for input_file in input_path:
        input_file = Path(input_file)
        if input_file.is_dir():
            print(f"Adding files in path for extraction: {input_file}")
            for file in input_file.iterdir():
                if file.is_file() and accept_file(
                    file, files_whitelist, files_blacklist
                ):
                    input_files.append(file)
        elif input_file.is_file() and accept_file(
            input_file, files_whitelist, files_blacklist
        ):
            print(f"Adding file for extraction: {input_file}")
            input_files.append(input_file)
    return input_files


def main(args):
    output_path = Path(args.output)
    config = args.config
    with open(args.config, "r") as f:
        config = json.loads(f.read())
    config = Config(**config)

    # Get list of regexes for finding transaction blocks
    transaction_blocks = []
    for tb in config.transaction_blocks:
        transaction_blocks.append(
            (re.compile(tb[0]), re.compile(tb[1]), re.compile(tb[2]))
        )

    # Get list of regexes for ignoring lines
    ignore_lines = []
    for line in config.ignore_lines:
        ignore_lines.append(re.compile(line))

    input_files = get_input_files(config)

    # Process input files
    append = False
    for input_file in input_files:
        parsed_pdf = []
        print(f"Extracting file - {input_file}")

        # Check file is valid pdf
        with open(input_file, "rb") as f:
            try:
                parsed_pdf = pdftotext.PDF(f, physical=True)
            except:
                print(f"File is not valid pdf - ignoring - {input_file}")
                continue

        if parsed_pdf:
            lines_to_parse = ("\n\n".join(parsed_pdf)).split("\n")
            parsed_blocks = []
            parsed_block = []
            for start, end, _ in transaction_blocks:
                start_line = None
                in_transaction_block = False
                for idx2, line in enumerate(lines_to_parse):
                    if [x for x in parsed_blocks if idx2 <= x[1] and idx2 >= x[0]]:
                        continue
                    if in_transaction_block:
                        if end.match(line):
                            in_transaction_block = False
                            # No lines in block
                            if not parsed_block:
                                continue
                            file = io.BytesIO("\n".join(parsed_block).encode("utf-8"))
                            data_frame = pd.read_fwf(file)

                            # Run preprocess code
                            if config.pre_process:
                                mod_details = config.pre_process.split(".")
                                process_module = importlib.import_module(
                                    f"modules.{'.'.join(mod_details[:-1])}"
                                )
                                process_class = getattr(process_module, mod_details[-1])
                                data_frame = process_class.preprocess(
                                    data_frame, lines_to_parse
                                )
                            # Ensure correct number of fixed width columns
                            if config.column_number:
                                n = 2
                                while (
                                    config.column_number != len(data_frame.columns)
                                ) and len(data_frame) / n > 1:
                                    file = io.BytesIO(
                                        "\n".join(parsed_block).encode("utf-8")
                                    )
                                    data_frame = pd.read_fwf(
                                        file, infer_nrows=len(data_frame) / n
                                    )
                                    n = n * 2
                                # Merge extra columns
                                if len(data_frame.columns) > config.column_number:
                                    cols_to_drop = []
                                    for idx, col in enumerate(data_frame.columns):
                                        if col.startswith("Unnamed:"):
                                            data_frame[col] = data_frame[col].fillna("")
                                            data_frame[
                                                data_frame.columns[idx - 1]
                                            ] = data_frame[
                                                data_frame.columns[idx - 1]
                                            ].astype(
                                                str
                                            ) + data_frame[
                                                data_frame.columns[idx]
                                            ].astype(
                                                str
                                            )
                                            cols_to_drop.append(col)
                                    data_frame = data_frame.drop(cols_to_drop, axis=1)
                                # Merge rows (with overflow descriptions)
                                drop_indices = []
                                for index, row in data_frame.iterrows():
                                    if (
                                        data_frame.iloc[index].isnull().sum()
                                        == len(data_frame.columns) - 1
                                    ):
                                        for i in range(len(data_frame.columns)):
                                            if not pd.isnull(data_frame.iloc[index, i]):
                                                data_frame.iloc[index - 1, i] = (
                                                    data_frame.iloc[index - 1, i]
                                                    + " "
                                                    + data_frame.iloc[index, i]
                                                )
                                        drop_indices.append(index)
                                data_frame = data_frame.drop(
                                    data_frame.index[drop_indices]
                                )
                            # run postprocess code
                            if config.post_process:
                                mod_details = config.post_process.split(".")
                                process_module = importlib.import_module(
                                    f"modules.{'.'.join(mod_details[:-1])}"
                                )
                                process_class = getattr(process_module, mod_details[-1])
                                data_frame = process_class.process(
                                    data_frame, lines_to_parse
                                )
                            if args.debug:
                                breakpoint()
                            if append == False:
                                data_frame.to_csv(f"{output_path}", index=False)
                                append = True
                            else:
                                data_frame.to_csv(
                                    f"{output_path}",
                                    index=False,
                                    header=False,
                                    mode="a",
                                )
                            parsed_block = []
                            parsed_blocks.append((start_line, idx2 - 1))
                        elif line.strip():
                            if not [x for x in ignore_lines if x.match(line)]:
                                parsed_block.append(line)
                    elif start.match(line):
                        if parsed_block:
                            parsed_block = []
                        in_transaction_block = True
                        start_line = idx2


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse pdf bank statements to a CSV file containing transactions")
    parser.add_argument(
        "-i", "--input", nargs="+", required=True, help="Input directories or files"
    )
    parser.add_argument("-o", "--output", required=True, help="Output file")
    parser.add_argument("-c", "--config", required=True, help="Config file")
    parser.add_argument(
        "-d",
        "--debug",
        help="Debug with breakpoint",
        default=False,
        action="store_true",
    )
    args = parser.parse_args()
    main(args)
