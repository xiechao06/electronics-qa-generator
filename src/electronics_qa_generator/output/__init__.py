"""Dataset assembler + exporters.

Packages each accepted sample into a structured record and exports to
JSONL/Parquet alongside image artifacts, then splits by family/topology/
parameter regime.
"""

from .serialize import record_to_dict, record_to_json

__all__ = ["record_to_dict", "record_to_json"]
