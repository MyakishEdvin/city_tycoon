import { getInitData } from "./telegram";
import type { MeResponse, TransactionHistoryResponse } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const initData = getInitData();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // The backend re-validates this signature on every call — the
      // frontend never asserts who the user is by any other means.
      Authorization: `tma ${initData}`,
      ...(options.headers ?? {}),
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API ${response.status}: ${body || response.statusText}`);
  }

  return (await response.json()) as T;
}

export function fetchMe(): Promise<MeResponse> {
  return request<MeResponse>("/api/me");
}

export function fetchTransactions(limit = 20, offset = 0): Promise<TransactionHistoryResponse> {
  return request<TransactionHistoryResponse>(`/api/transactions?limit=${limit}&offset=${offset}`);
}

export function updateLanguage(language: string): Promise<MeResponse> {
  return request<MeResponse>("/api/me/language", {
    method: "PATCH",
    body: JSON.stringify({ language }),
  });
}