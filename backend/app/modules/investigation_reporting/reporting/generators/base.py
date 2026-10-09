from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class GeneratedReport:
    body: bytes
    media_type: str
    extension: str


class ReportGenerator(Protocol):
    output_format: str

    def generate(self, snapshot: dict[str, Any]) -> GeneratedReport: ...
