import csv
import io
import json


def export_csv(events: list[dict]) -> bytes:
    output = io.StringIO(newline="")
    columns = ("id", "created_at", "actor_name", "actor_role", "action", "target_type", "target_id", "target_label", "status", "severity", "source", "ip_address", "correlation_id", "details")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for event in events:
        row = dict(event)
        row["details"] = json.dumps(row.get("details") or {}, ensure_ascii=False)
        writer.writerow(row)
    return output.getvalue().encode("utf-8-sig")
