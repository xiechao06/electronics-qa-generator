#!/usr/bin/env python3
"""Unpack MMMU Electronics parquet files into JSONL/CSV plus image files.

Input:  mmmu_electronics/*.parquet
Output: mmmu_electronics_unpacked/{dev,validation,test}.jsonl/.csv and images/
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pyarrow.parquet as pq

INPUT_DIR = Path("mmmu_electronics")
OUTPUT_DIR = Path("mmmu_electronics_unpacked")
IMAGE_COLUMNS = [f"image_{i}" for i in range(1, 8)]
NON_IMAGE_COLUMNS = [
    "id",
    "question",
    "options",
    "explanation",
    "img_type",
    "answer",
    "topic_difficulty",
    "question_type",
    "subfield",
]


def split_name(parquet_path: Path) -> str:
    name = parquet_path.name
    if name.startswith("dev-"):
        return "dev"
    if name.startswith("validation-"):
        return "validation"
    if name.startswith("test-"):
        return "test"
    return parquet_path.stem


def image_suffix(path: str | None, data: bytes) -> str:
    if path:
        suffix = Path(path).suffix
        if suffix:
            return suffix
    if data.startswith(b"\x89PNG"):
        return ".png"
    if data.startswith(b"\xff\xd8"):
        return ".jpg"
    if data.startswith(b"GIF"):
        return ".gif"
    return ".bin"


def unpack_file(parquet_path: Path) -> dict:
    split = split_name(parquet_path)
    table = pq.read_table(parquet_path)
    rows = table.to_pylist()

    split_dir = OUTPUT_DIR / split
    image_dir = split_dir / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = split_dir / f"{split}.jsonl"
    csv_path = split_dir / f"{split}.csv"

    image_count = 0
    jsonl_records = []

    for row_idx, row in enumerate(rows):
        record = {col: row.get(col) for col in NON_IMAGE_COLUMNS}
        record["images"] = []

        row_id = row.get("id") or f"{split}_{row_idx}"
        safe_row_id = str(row_id).replace("/", "_").replace(" ", "_")

        for col in IMAGE_COLUMNS:
            image_obj = row.get(col)
            if not image_obj:
                continue

            data = image_obj.get("bytes") if isinstance(image_obj, dict) else None
            original_path = image_obj.get("path") if isinstance(image_obj, dict) else None
            if not data:
                continue

            suffix = image_suffix(original_path, data)
            original_name = Path(original_path).name if original_path else f"{safe_row_id}_{col}{suffix}"
            if not Path(original_name).suffix:
                original_name += suffix
            out_name = f"{safe_row_id}_{col}_{original_name}"
            out_path = image_dir / out_name
            out_path.write_bytes(data)
            image_count += 1

            record["images"].append(
                {
                    "column": col,
                    "path": str(out_path.relative_to(split_dir)),
                    "original_path": original_path,
                }
            )

        jsonl_records.append(record)

    with jsonl_path.open("w", encoding="utf-8") as f:
        for record in jsonl_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    csv_columns = NON_IMAGE_COLUMNS + ["images_json"]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=csv_columns)
        writer.writeheader()
        for record in jsonl_records:
            writer.writerow(
                {
                    **{col: record.get(col) for col in NON_IMAGE_COLUMNS},
                    "images_json": json.dumps(record["images"], ensure_ascii=False),
                }
            )

    return {
        "split": split,
        "rows": len(rows),
        "images": image_count,
        "jsonl": str(jsonl_path),
        "csv": str(csv_path),
        "image_dir": str(image_dir),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    summaries = []
    for parquet_path in sorted(INPUT_DIR.glob("*.parquet")):
        summaries.append(unpack_file(parquet_path))

    summary_path = OUTPUT_DIR / "summary.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")

    readme = OUTPUT_DIR / "README.md"
    readme.write_text(
        "# Unpacked MMMU Electronics subset\n\n"
        "Each split directory contains:\n\n"
        "- `<split>.jsonl`: one JSON record per example, with image paths\n"
        "- `<split>.csv`: tabular metadata, with `images_json` for image paths\n"
        "- `images/`: extracted image files\n\n"
        "See `summary.json` for row and image counts.\n",
        encoding="utf-8",
    )

    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
