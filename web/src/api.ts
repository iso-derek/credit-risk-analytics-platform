import { useEffect, useState } from "react";

export type Dataset = "synthetic" | "uci" | "german";

export interface Field {
  key: string;
  label: string;
  kind: string;
  help?: string;
}
export interface Band {
  band: string;
  letter: string;
  name: string;
  range: string;
}
export interface Meta {
  dataset: Dataset;
  synthetic: boolean;
  name: string;
  source_url: string | null;
  protected_fields: string[];
  source: string;
  currency: string;
  outcome: string;
  exposure_assumption: string;
  lgd: number;
  model: string;
  test_applicants: number;
  fields: Field[];
  bands: Band[];
}

const cache = new Map<string, unknown>();

export function apiUrl(path: string, dataset: Dataset, params: Record<string, string | number | undefined> = {}) {
  const query = new URLSearchParams({ dataset });
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  return `/api/${path}?${query.toString()}`;
}

export async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  if (cache.has(url)) return cache.get(url) as T;
  const response = await fetch(url, { signal });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (body?.detail) message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      /* keep default message */
    }
    throw new Error(message);
  }
  const data = (await response.json()) as T;
  cache.set(url, data);
  return data;
}

export interface Loadable<T> {
  data: T | undefined;
  error: string | undefined;
  loading: boolean;
}

/** Fetch JSON for a URL and keep the last good result while a new one loads. */
export function useApi<T>(url: string | null): Loadable<T> {
  const [state, setState] = useState<Loadable<T>>({ data: undefined, error: undefined, loading: url !== null });
  useEffect(() => {
    if (url === null) return;
    const controller = new AbortController();
    setState((previous) => ({ ...previous, loading: true, error: undefined }));
    getJson<T>(url, controller.signal)
      .then((data) => setState({ data, error: undefined, loading: false }))
      .catch((error: Error) => {
        if (error.name !== "AbortError") setState((previous) => ({ ...previous, error: error.message, loading: false }));
      });
    return () => controller.abort();
  }, [url]);
  return state;
}
