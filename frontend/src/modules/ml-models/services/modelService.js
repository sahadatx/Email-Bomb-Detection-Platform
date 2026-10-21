import { mlModelsApi as api } from "./api";

export const modelService = {
  async getModels(params = {}) {
    const response = await api.get("/models", { params });
    return response.data;
  },

  async getModelCount(params = {}) {
    const response = await api.get("/models/count", { params });
    return response.data;
  },

  async getSummary() {
    const response = await api.get("/models/summary");
    return response.data;
  },

  async getAlgorithms() {
    const response = await api.get("/algorithms");
    return response.data?.items || [];
  },

  async getTrainingHistory(modelId, params = {}) {
    const response = await api.get(`/models/${encodeURIComponent(modelId)}/training-runs`, { params });
    return response.data;
  },

  async deleteModel(modelId) {
    await api.delete(`/models/${encodeURIComponent(modelId)}`);
  },

  async getModelById(modelId) {
    const response = await api.get(
      `/models/${encodeURIComponent(modelId)}`
    );
    return response.data;
  },

  async createModel(payload) {
    const response = await api.post("/models", payload);
    return response.data;
  },

  async updateModel(modelId, payload) {
    const response = await api.patch(
      `/models/${encodeURIComponent(modelId)}`,
      payload
    );
    return response.data;
  },

  async updateModelStatus(modelId, status) {
    const response = await api.patch(
      `/models/${encodeURIComponent(modelId)}/status`,
      { status }
    );
    return response.data;
  },
};

export default modelService;
