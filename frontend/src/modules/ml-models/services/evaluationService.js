import { mlModelsApi as api } from "./api";
export async function getEvaluationRuns(params = {}) { return (await api.get("/evaluation-runs", { params })).data; }
export async function getEvaluationRunById(id) { return (await api.get(`/evaluation-runs/${encodeURIComponent(id)}`)).data; }
export async function createEvaluationRun(payload) { return (await api.post("/evaluation-runs", payload)).data; }
export async function exportEvaluationReport(id) {
  const response = await api.get(`/evaluation-runs/${encodeURIComponent(id)}/export`, { params: { format: "json" }, responseType: "blob" });
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = `evaluation-${id}.json`;
  document.body.appendChild(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default { getEvaluationRuns, getEvaluationRunById, createEvaluationRun, exportEvaluationReport };
