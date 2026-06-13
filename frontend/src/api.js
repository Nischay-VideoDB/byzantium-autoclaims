const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function uploadClaim({ video, claimantName, claimantId, nric, vehiclePlate, policyNumber }) {
  const form = new FormData();
  form.append("video", video);
  form.append("claimant_name", claimantName);
  form.append("claimant_id_number", claimantId || "");
  form.append("nric", nric || "");
  form.append("vehicle_plate", vehiclePlate || "");
  form.append("policy_number", policyNumber || "");
  return request("/upload-video", { method: "POST", body: form });
}

export async function lookupPolicy(name, plate) {
  const params = new URLSearchParams({ name: name || "", plate: plate || "" });
  return request(`/lookup-policy?${params}`);
}

export async function analyzeClaim(claimId) {
  return request(`/analyze-claim/${claimId}`, { method: "POST" });
}

export function streamClaim(claimId, onStep, onComplete, onError) {
  const es = new EventSource(`${BASE_URL}/stream-claim/${claimId}`);

  es.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.step === "complete") {
      es.close();
      onComplete(data);
    } else if (data.step === "error") {
      es.close();
      onError(new Error(data.message || "Stream failed"));
    } else {
      onStep(data);
    }
  };

  es.onerror = () => {
    es.close();
    onError(new Error("Connection lost"));
  };

  return () => es.close();
}

export async function getDecision(claimId) {
  return request(`/decision/${claimId}`);
}

export async function getReceipt(claimId) {
  return request(`/receipt/${claimId}`);
}

export async function listClaims() {
  return request("/claims");
}

export async function uploadPolicy(file) {
  const form = new FormData();
  form.append("policy", file);
  return request("/upload-policy", { method: "POST", body: form });
}

export async function healthCheck() {
  return request("/health");
}
