import { threatIntelligenceApi as api } from "./threatIntelligenceApi";

const id = (value) => encodeURIComponent(value);
export const threatIntelligenceService = {
  overview: (filters) => api.get("/overview", filters),
  exportOverview: (filters) =>
    api.download("/overview/export", filters, "threat-overview.csv"),
  indicators: (filters) => api.get("/indicators", filters),
  indicator: (indicatorId) => api.get(`/indicators/${id(indicatorId)}`),
  createIndicator: (body) => api.post("/indicators", body),
  updateIndicator: (indicatorId, body) =>
    api.patch(`/indicators/${id(indicatorId)}`, body),
  setIndicatorStatus: (indicatorId, status) =>
    api.patch(`/indicators/${id(indicatorId)}/status`, { status }),
  indicatorMatches: (indicatorId, params) =>
    api.get(`/indicators/${id(indicatorId)}/matches`, params),
  feeds: (filters) => api.get("/feeds", filters),
  feedSummary: () => api.get("/feeds/summary"),
  feed: (feedId) => api.get(`/feeds/${id(feedId)}`),
  createFeed: (body) => api.post("/feeds", body),
  updateFeed: (feedId, body) => api.patch(`/feeds/${id(feedId)}`, body),
  syncFeed: (feedId) => api.post(`/feeds/${id(feedId)}/sync`),
  feedSyncHistory: (feedId, params) =>
    api.get(`/feeds/${id(feedId)}/sync-history`, params),
  matches: (filters) => api.get("/matches", filters),
  matchSummary: (filters) => api.get("/matches/summary", filters),
  reconcileMatches: () => api.post("/matches/reconcile"),
  match: (matchId) => api.get(`/matches/${id(matchId)}`),
  updateMatchStatus: (matchId, match_status) =>
    api.patch(`/matches/${id(matchId)}/status`, { match_status }),
};
