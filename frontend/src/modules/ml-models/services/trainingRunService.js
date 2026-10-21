import { mlModelsApi as api, preprocessingApi } from "./api";

export async function getTrainingRuns(params = {}) {
  return (await api.get("/training-runs", { params })).data;
}

export async function getTrainingRunById(id) {
  return (await api.get(`/training-runs/${encodeURIComponent(id)}`)).data;
}

export async function getTrainingRunModelVersion(id) {
  return (await api.get(`/training-runs/${encodeURIComponent(id)}/model-version`)).data;
}

export async function getTrainingRunLogs(id) {
  return (await api.get(`/training-runs/${encodeURIComponent(id)}/logs`)).data;
}

export async function createTrainingRun(payload) {
  return (await api.post("/training-runs", payload)).data;
}

export async function retryTrainingRun(id) {
  return (await api.post(`/training-runs/${encodeURIComponent(id)}/retry`)).data;
}

export async function resumeTrainingRun(id) {
  return (await api.post(`/training-runs/${encodeURIComponent(id)}/resume`)).data;
}

export async function getTrainableModels() {
  return (await api.get("/models", { params: { status: "active", limit: 200 } })).data;
}

export async function getCompletedPreprocessingRuns() {
  const response = await preprocessingApi.get("/runs", {
    params: { status: "completed", page: 1, page_size: 100 },
  });
  return response.data;
}

export async function getPreprocessingRun(id) {
  return (await preprocessingApi.get(`/runs/${encodeURIComponent(id)}`)).data;
}

export default {
  getTrainingRuns,
  getTrainingRunById,
  getTrainingRunModelVersion,
  getTrainingRunLogs,
  createTrainingRun,
  retryTrainingRun,
  resumeTrainingRun,
  getTrainableModels,
  getCompletedPreprocessingRuns,
  getPreprocessingRun,
};
