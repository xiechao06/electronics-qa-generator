"""Dataset assembler: transforms internal QA items into MMMU-compatible JSONL.

Outputs a self-contained dataset directory with dataset.jsonl and image files.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..models import QAItem


def assemble_dataset(
    items: list[QAItem],
    schematic_paths: list[str | None],
    topology: str,
    seed: int,
    out_dir: Path,
) -> Path:
    """Write MMMU-compatible JSONL and copy schematics to an output directory.

    Parameters
    ----------
    items : list of QAItem
        Generated QA items.
    schematic_paths : list of str or None
        Filesystem paths to the rendered schematic PNGs, one per item (can be
        the same file shared across all items from one topology).
    topology : str
        Topology name for id generation.
    seed : int
        Seed for reproducible id generation.
    out_dir : Path
        Output directory root.

    Returns
    -------
    Path
        The path to the written `dataset.jsonl` file.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    images_dir = out_dir / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    seed_str = f"{seed & 0xFFFFFFFF:08x}"

    jsonl_path = out_dir / "dataset.jsonl"
    mode = "a" if jsonl_path.exists() else "w"

    with open(jsonl_path, mode) as f:
        for i, item in enumerate(items):
            item_id = f"{topology}_{seed_str}_{i}"

            # Determine answer and options
            answer = item.answer
            options: str | None = None

            if item.question_type == "classification" and item.choices:
                options = json.dumps(item.choices)
            elif item.question_type == "comparison":
                # comparison answers are boolean labels — treat as open-ended
                pass

            # Copy the schematic image into images/ with a topology-unique name
            image_rel_path = _copy_schematic(
                schematic_paths[i] if i < len(schematic_paths) else None,
                topology,
                seed_str,
                images_dir,
            )

            record: dict = {
                "id": item_id,
                "question": item.question,
                "answer": answer,
            }
            if options is not None:
                record["options"] = options
            if item.explanation:
                record["explanation"] = item.explanation
            if image_rel_path is not None:
                record["image"] = image_rel_path

            f.write(json.dumps(record, default=str) + "\n")

    return jsonl_path


def _copy_schematic(
    source_path: str | None,
    topology: str,
    seed_str: str,
    images_dir: Path,
) -> str | None:
    """Copy a schematic PNG into the images directory.

    Returns the relative path (e.g. ``images/rc_lowpass_0000002a.png``).
    """
    if source_path is None:
        return None

    src = Path(source_path)
    if not src.exists():
        return None

    dest_name = f"{topology}_{seed_str}.png"
    dest = images_dir / dest_name
    shutil.copy2(src, dest)
    return f"images/{dest_name}"
