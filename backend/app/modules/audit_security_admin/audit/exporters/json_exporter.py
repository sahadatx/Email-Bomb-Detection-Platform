import json


def export_json(events: list[dict]) -> bytes:
    return json.dumps(events, ensure_ascii=False, indent=2, default=str).encode("utf-8")
