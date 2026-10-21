from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from app.modules.analytics.errors import InvalidAnalyticsFilter
from app.modules.dashboard.selectors.dashboard_filters import DashboardFilters
from app.modules.dashboard.services.dashboard_service import DashboardService
from app.modules.dashboard.utils.aggregation import distribution_map
from app.modules.dashboard.utils.date_range import resolve_window


def test_dashboard_filters_translate_to_existing_analytics_contract():
    model_id = "3ad803b9-bfeb-4c11-b664-2b73b8ff8b1a"
    query = DashboardFilters(
        time_range="custom",
        classification="bomb",
        risk_level="high",
        model_id=model_id,
        start_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
        end_date=datetime(2026, 9, 30, tzinfo=timezone.utc),
    )

    result = query.to_analytics_filters()

    assert result.classification == "bomb"
    assert result.risk_level == "high"
    assert str(result.model_definition_id) == model_id
    assert result.from_date == query.start_date
    assert result.to_date == query.end_date


def test_distribution_includes_empty_levels_without_inventing_counts():
    rows = [{"risk_level": "high", "count": 3}, {"risk_level": "other", "count": 90}]

    result = distribution_map(rows, "risk_level", ("critical", "high", "medium", "low"))

    assert result == [
        {"risk_level": "critical", "count": 0},
        {"risk_level": "high", "count": 3},
        {"risk_level": "medium", "count": 0},
        {"risk_level": "low", "count": 0},
    ]


def test_custom_range_requires_both_dates_and_rejects_reverse_order():
    with pytest.raises(
        InvalidAnalyticsFilter, match="requires start_date and end_date"
    ):
        resolve_window(DashboardFilters(time_range="custom"))

    with pytest.raises(InvalidAnalyticsFilter, match="start_date must be before"):
        resolve_window(
            DashboardFilters(
                time_range="custom",
                start_date=datetime(2026, 9, 2),
                end_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            )
        )


def test_dashboard_summary_separates_intake_from_completed_detections():
    service = DashboardService(db=object())
    service.repository = Mock()
    service.repository.count_emails.return_value = 12
    service.analytics = Mock()
    service.analytics.overview.return_value = {
        "total_detections": 9,
        "bomb_emails": {"value": 2},
        "high_risk_emails": {"value": 1},
    }
    filters = DashboardFilters(time_range="24h")

    result = service.summary(filters)

    assert result["total_emails"]["value"] == 12
    assert result["emails_analyzed"]["value"] == 9
    assert result["bomb_detected"]["value"] == 2
    assert result["high_risk_emails"]["value"] == 1
    assert "unclassified" in result["total_emails"]["description"]


def test_dashboard_overview_api_requires_login_and_returns_live_empty_state(
    client, admin
):
    anonymous = client.get("/api/v1/dashboard/overview")
    assert anonymous.status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "AdminPassword123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/dashboard/overview",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["summary"]["total_emails"]["value"] == 0
    assert body["summary"]["emails_analyzed"]["value"] == 0
    assert [item["risk_level"] for item in body["risk_distribution"]] == [
        "critical",
        "high",
        "medium",
        "low",
    ]
    assert all(item["count"] == 0 for item in body["risk_distribution"])
    assert {item["name"] for item in body["system_health"]["components"]} == {
        "Detection Engine",
        "ML Model",
        "Threat Intelligence",
        "Preprocessing",
    }
