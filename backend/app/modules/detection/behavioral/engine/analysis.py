from app.modules.detection.behavioral.engine.anomaly import detect_sender_anomalies


def analyze_sender_history(email, feature_rows, enabled: bool = True):
    if not enabled:
        return "disabled", "Behavioral analysis is disabled in settings.", {}, []
    sender_rows = [(item, features) for item, features in feature_rows if item.sender == email.sender]
    return detect_sender_anomalies(email, sender_rows)
