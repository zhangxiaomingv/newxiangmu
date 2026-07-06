// API base URL - hardcoded for reliability with localtunnel
// Tunnel restarts change the URL; update this when tunnel changes
const API_BASE = "https://polite-rings-argue.loca.lt/api";

export async function startAnalysis(brand, url = null, locale = "en") {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ brand, url, locale }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Analysis failed (${res.status})`);
  }
  return res.json();
}

export async function getAnalysis(id) {
  const res = await fetch(`${API_BASE}/analysis/${id}`);
  if (!res.ok) throw new Error("Analysis not found");
  return res.json();
}

export async function reanalyze(id, locale = "en") {
  const res = await fetch(`${API_BASE}/analyze/${id}/reanalyze?locale=${locale}`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Re-analysis failed (${res.status})`);
  }
  return res.json();
}

export async function getHistory(id) {
  const res = await fetch(`${API_BASE}/analysis/${id}/history`);
  if (!res.ok) return [];
  return res.json();
}

export async function getRecent() {
  const res = await fetch(`${API_BASE}/analyses/recent`);
  if (!res.ok) return [];
  return res.json();
}

export async function getBrands() {
  const res = await fetch(`${API_BASE}/brands`);
  if (!res.ok) return [];
  return res.json();
}
