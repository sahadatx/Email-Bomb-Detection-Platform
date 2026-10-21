"""Dashboard adapter over the platform's existing Analytics service."""

from app.modules.analytics.service import AnalyticsService
from ..selectors.dashboard_filters import DashboardFilters


class AnalyticsAdapter:
    """Delegate detection, risk and classification calculations to Analytics."""

    def __init__(self, db):
        self.service = AnalyticsService(db)

    @staticmethod
    def filters(query: DashboardFilters):
        return query.to_analytics_filters()

    def overview(self, query: DashboardFilters):
        return self.service.overview(self.filters(query))

    def classification(self, query: DashboardFilters):
        return self.service.classification(self.filters(query))

    def risk(self, query: DashboardFilters):
        return self.service.risk(self.filters(query))

    def recent(self, query: DashboardFilters, limit: int):
        return self.service.recent(self.filters(query), limit=limit)

    def models(self):
        return self.service.repository.model_options()
