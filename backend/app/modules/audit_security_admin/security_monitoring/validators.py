from ..errors import AdminDomainError

ALLOWED_FIELDS = {"severity", "source", "status", "actor_id", "source_ip", "event_type"}
ALLOWED_OPERATORS = {"equals", "contains"}


def validate_condition(condition):
    if not isinstance(condition, dict) or set(condition) != {"field", "operator", "value"}:
        raise AdminDomainError("Condition must contain only field, operator, and value.")
    if condition.get("field") not in ALLOWED_FIELDS:
        raise AdminDomainError("Condition field is not supported.")
    if condition.get("operator") not in ALLOWED_OPERATORS:
        raise AdminDomainError("Condition operator is not supported.")
    value = condition.get("value")
    if not isinstance(value, (str, int, bool)) or len(str(value)) > 200:
        raise AdminDomainError("Condition value must be a short scalar value.")
    if not str(value).strip():
        raise AdminDomainError("Condition value cannot be empty.")
    if condition["field"] in {"severity", "status"} and condition["operator"] == "equals":
        allowed = {"severity": {"critical", "high", "medium", "low"}, "status": {"new", "reviewed", "investigating"}}[condition["field"]]
        if str(value).lower() not in allowed:
            raise AdminDomainError(f"Condition value is invalid for {condition['field']}.")
