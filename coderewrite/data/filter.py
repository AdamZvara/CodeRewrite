#!/usr/bin/env python3
"""Filter a JSONL dataset by instruction length and code line count."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Filter JSONL dataset rows.")
    parser.add_argument(
        "filename", help="Input JSONL file (in the same directory as this script)"
    )
    parser.add_argument(
        "instruction_length",
        type=int,
        help="Max instruction character length (inclusive)",
    )
    parser.add_argument("code_length", type=int, help="Max code line count (inclusive)")
    parser.add_argument(
        "required_phrase",
        nargs="?",
        default=None,
        help="Phrase that must appear in output",
    )
    args = parser.parse_args()

    data_dir = Path(__file__).parent
    input_path = data_dir / args.filename
    output_path = input_path.with_stem(input_path.stem + "_filtered")

    kept = skipped = 0
    with input_path.open() as fin, output_path.open("w") as fout:
        for line in fin:
            row = json.loads(line)
            if len(row["instruction"]) > args.instruction_length:
                skipped += 1
                continue
            if args.required_phrase and args.required_phrase not in row["output"]:
                skipped += 1
                continue
            if len(row["content"].splitlines()) > args.code_length:
                skipped += 1
                continue

            # Trim output to start from the first `def` keyword
            code = row["content"]
            def_idx = code.find("\ndef ")
            if def_idx == -1:
                def_idx = code.find("def ")
            else:
                def_idx += 1  # keep the newline before def
            if def_idx == -1:
                skipped += 1
                continue
            row["output"] = code[def_idx:]

            fout.write(json.dumps(row) + "\n")
            kept += 1

    print(f"Kept {kept}, skipped {skipped} → {output_path.name}")


if __name__ == "__main__":
    main()
