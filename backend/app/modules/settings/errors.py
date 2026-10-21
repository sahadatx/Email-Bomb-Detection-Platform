"""Settings module domain errors."""


class SettingsError(Exception):
    """Base error for settings read and update operations."""


class SettingsValidationError(SettingsError):
    """A configuration update failed validation or is not editable here."""
