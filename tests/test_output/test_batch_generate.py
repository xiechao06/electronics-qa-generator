from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "batch_generate.py"

spec = importlib.util.spec_from_file_location("batch_generate", SCRIPT_PATH)
assert spec is not None
assert spec.loader is not None
batch_generate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(batch_generate)


def test_generate_prompt_files_adds_image_only_instruction(tmp_path):
    jsonl_path = tmp_path / "qa_items.jsonl"
    prompts_dir = tmp_path / "prompts"

    item = {
        "topology": "mosfet_cs_amplifier",
        "seed": 0,
        "schematic_path": "images/mosfet_cs_amplifier/00000000.png",
        "question": "What is V_DS?",
        "answer": "7.45 V",
        "netlist": "* MOSFET CS amplifier\n.end",
    }
    jsonl_path.write_text(json.dumps(item) + "\n", encoding="utf-8")

    written = batch_generate._generate_prompt_files(jsonl_path, prompts_dir)

    assert written == 1
    prompt_path = prompts_dir / "mosfet_cs_amplifier_00000000.md"
    assert prompt_path.exists()
    prompt_text = prompt_path.read_text(encoding="utf-8")
    assert batch_generate.PROMPT_IMAGE_ONLY_INSTRUCTION in prompt_text
    assert "Do not consult the answer file" in prompt_text
    assert "purely from the schematic image above" in prompt_text
    assert "1. What is V_DS?" in prompt_text
