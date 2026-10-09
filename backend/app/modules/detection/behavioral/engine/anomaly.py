from datetime import datetime, timedelta, timezone


def detect_sender_anomalies(email, sender_rows):
    if not email.sender:
        return "insufficient_data", "Sender information is unavailable for behavioral analysis.", {"emails_in_history": 0}, []
    if len(sender_rows) < 3:
        return "insufficient_data", "Insufficient sender history for behavioral analysis.", {"emails_in_history": len(sender_rows)}, []
    now = email.received_at or email.collected_at or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    cutoff = now - timedelta(hours=1)
    recent = []
    for item, _ in sender_rows:
        stamp = item.received_at
        if stamp is None:
            continue
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        if stamp >= cutoff:
            recent.append(item)
    anomalies = []
    if len(recent) >= 5:
        anomalies.append({"pattern": "email_burst", "severity": "high", "description": f"{len(recent)} emails from this sender in the last hour."})
    if len(sender_rows) >= 10:
        anomalies.append({"pattern": "repeated_sender", "severity": "medium", "description": f"{len(sender_rows)} stored emails share this sender."})
    summary = "Unusual sender activity detected." if anomalies else "No behavioral anomaly found in the available sender history."
    return "completed", summary, {"emails_in_history": len(sender_rows), "sender_emails_last_hour": len(recent), "analysis_window": "1h"}, anomalies
