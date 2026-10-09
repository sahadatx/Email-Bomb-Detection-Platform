class InvestigationError(Exception):
    """An expected, user-correctable Investigation & Reporting error."""


class EvidenceValidationError(InvestigationError):
    """Evidence failed a domain invariant or source-record check."""
