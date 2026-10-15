import type { AssessmentResponse, CompareResponse, ViewState } from "../types";

async function get<T>(path: string, params: Record<string, string | number | boolean>, signal?: AbortSignal): Promise<T> {
  const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)]));
  const res = await fetch(`/api/v1/${path}?${qs}`, { signal });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json() as Promise<T>;
}

export const fetchAssessment = (v: ViewState, signal?: AbortSignal) =>
  get<AssessmentResponse>("assessment", { pathway: v.pathway, year: v.year, subsidence: v.subsidence, water_level: v.waterLevel }, signal);

export const fetchCompare = (v: ViewState, signal?: AbortSignal) =>
  get<CompareResponse>("compare", { year: v.year, water_level: v.waterLevel }, signal);
