"""Request and response schemas for category-based system settings."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SettingChoice(BaseModel):
    value: str
    label: str
    description: str | None = None


class SettingField(BaseModel):
    key: str
    label: str
    value: Any = None
    value_type: Literal[
        "string",
        "timezone",
        "integer",
        "threshold",
        "boolean",
        "model_version",
        "status",
    ]
    description: str
    editable: bool = True
    sensitive: bool = False
    options: list[SettingChoice] = Field(default_factory=list)
    updated_at: datetime | None = None


class SettingsCategory(BaseModel):
    category: str
    title: str
    description: str
    supported: bool = True
    editable: bool = True
    notice: str | None = None
    fields: list[SettingField] = Field(default_factory=list)
    links: list[dict[str, str]] = Field(default_factory=list)


class SettingsOverviewItem(BaseModel):
    category: str
    title: str
    description: str
    editable: bool
    supported: bool = True


class SettingsOverview(BaseModel):
    categories: list[SettingsOverviewItem]


class SettingsUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    values: dict[str, Any] = Field(min_length=1)
    reason: str = Field(min_length=3, max_length=1000)


class SettingsUpdateResponse(BaseModel):
    category: SettingsCategory
    changed_keys: list[str]
    saved_at: datetime
