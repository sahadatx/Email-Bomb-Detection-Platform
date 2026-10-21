import { mlModelsApi as api } from "./api";
export async function getVersions(params = {}) { return (await api.get("/versions", { params })).data; }
export async function getVersionById(id) { return (await api.get(`/versions/${encodeURIComponent(id)}`)).data; }
export async function activateVersion(id) { return (await api.post(`/versions/${encodeURIComponent(id)}/activate`)).data; }
export async function archiveVersion(id) { return (await api.post(`/versions/${encodeURIComponent(id)}/archive`)).data; }
export async function restoreVersion(id) { return (await api.post(`/versions/${encodeURIComponent(id)}/restore`)).data; }
export async function downloadVersionArtifact(id) {
  const response = await api.get(`/versions/${encodeURIComponent(id)}/artifact`, { responseType: "blob" });
  const disposition = response.headers["content-disposition"] || "";
  const filename = disposition.match(/filename="?([^";]+)"?/i)?.[1] || `model-version-${id}`;
  const url = URL.createObjectURL(response.data);
  const anchor = document.createElement("a"); anchor.href = url; anchor.download = filename;
  document.body.appendChild(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export default { getVersions, getVersionById, activateVersion, archiveVersion, restoreVersion, downloadVersionArtifact };
