"""Expose the existing settings persistence models to Settings integrations.

The platform already owns these tables through Audit & Admin and Detection.
Aliases intentionally avoid creating a second, competing settings table.
"""

from app.modules.audit_security_admin.models import AdminSetting as SystemSetting
from app.modules.audit_security_admin.models import (
    AdminSettingHistory as SystemSettingHistory,
)

__all__ = ["SystemSetting", "SystemSettingHistory"]
