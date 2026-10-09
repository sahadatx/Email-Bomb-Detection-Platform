from __future__ import annotations

import json
from typing import Any

from fastapi.encoders import jsonable_encoder

from .base import GeneratedReport


class JsonReportGenerator:
    output_format = "json"

    def generate(self, snapshot: dict[str, Any]) -> GeneratedReport:
        body = json.dumps(jsonable_encoder(snapshot), ensure_ascii=False, indent=2).encode("utf-8")
        return GeneratedReport(body, "application/json", "json")
