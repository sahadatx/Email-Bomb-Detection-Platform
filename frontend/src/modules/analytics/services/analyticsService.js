import { analyticsApi } from "./analyticsApi";

export const analyticsService = {
  models: () => analyticsApi.get("/models"),
  overview: (filters) => analyticsApi.get("/overview", filters),
  classification: (filters) => analyticsApi.get("/classification", filters),
  risk: (filters) => analyticsApi.get("/risk", filters),
  performance: (filters) => analyticsApi.get("/detection-performance", filters),
  behavior: (filters) => analyticsApi.get("/behavior", filters),
  recent: (filters) => analyticsApi.get("/recent-detections", { ...filters, limit: 8 }),
  export: (filters) => analyticsApi.export(filters),
};
