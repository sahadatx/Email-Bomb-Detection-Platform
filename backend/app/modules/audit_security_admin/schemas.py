from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class PageResult(BaseModel):
    items: list[dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class MonitoringRuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    event_type: str = Field(min_length=2, max_length=80)
    severity: Literal["critical", "high", "medium", "low"]
    condition: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

    @model_validator(mode="after")
    def normalize_rule_identity(self):
        self.name = self.name.strip()
        self.event_type = self.event_type.strip()
        if not self.name or not self.event_type:
            raise ValueError("Rule name and event type cannot be blank.")
        return self


class MonitoringRuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=2000)
    event_type: str | None = Field(default=None, min_length=2, max_length=80)
    severity: Literal["critical", "high", "medium", "low"] | None = None
    condition: dict[str, Any] | None = None
    enabled: bool | None = None

    @model_validator(mode="after")
    def require_an_update(self):
        if not self.model_fields_set:
            raise ValueError("Provide at least one field to update.")
        if self.name is not None:
            self.name = self.name.strip()
            if not self.name:
                raise ValueError("Rule name cannot be blank.")
        if self.event_type is not None:
            self.event_type = self.event_type.strip()
            if not self.event_type:
                raise ValueError("Event type cannot be blank.")
        return self


class AlertTransition(BaseModel):
    status: Literal["open", "investigating", "resolved"]
    assigned_to: str | None = None
    resolution_note: str | None = Field(default=None, max_length=4000)
    note: str | None = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def require_resolution_note(self):
        if self.status == "resolved" and not (self.resolution_note or "").strip():
            raise ValueError("A resolution note is required to resolve an alert.")
        return self


class SecurityEventTransition(BaseModel):
    status: Literal["new", "reviewed", "investigating"] | None = None
    assigned_to: str | None = None
    disposition: Literal["confirmed_threat", "false_positive", "benign", "needs_follow_up"] | None = None
    note: str | None = Field(default=None, max_length=4000)


class SettingUpdate(BaseModel):
    value: Any
    reason: str = Field(min_length=3, max_length=2000)


class SecurityEventIngest(BaseModel):
    event_type: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=2, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    severity: Literal["critical", "high", "medium", "low"]
    source: str = Field(min_length=2, max_length=80)
    actor_id: str | None = None
    source_ip: str | None = Field(default=None, max_length=45)
    details: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None

    @model_validator(mode="after")
    def normalize_event_identity(self):
        self.event_type = self.event_type.strip()
        self.title = self.title.strip()
        self.source = self.source.strip()
        if not self.event_type or not self.title or not self.source:
            raise ValueError("Event type, title, and source cannot be blank.")
        return self
