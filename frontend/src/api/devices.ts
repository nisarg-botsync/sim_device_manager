import axios, { type AxiosError } from "axios";
import type {
  CreateDevicePayload,
  Device,
  DeviceStatusResponse,
} from "../types/device";

const http = axios.create({ baseURL: "/api" });

/**
 * Unwrap the { data, error } envelope from Django.
 *
 * Handles three failure modes:
 *  1. Django returned { data: null, error: "..." }  → throw with the error string
 *  2. Non-2xx response with no JSON body (e.g. 404 from nginx) → throw with HTTP status text
 *  3. Network-level failure (no response)            → throw with axios message
 */
async function unwrap<T>(promise: Promise<{ data: { data: T; error: string | null } }>): Promise<T> {
  try {
    const res = await promise;
    if (res.data.error) throw new Error(res.data.error);
    return res.data.data;
  } catch (err) {
    const axiosErr = err as AxiosError<{ data: unknown; error: string | null }>;
    if (axiosErr.response) {
      // Server replied — prefer our envelope error string, fall back to status text.
      const apiError = axiosErr.response.data?.error;
      if (apiError) throw new Error(apiError, { cause: err });
      throw new Error(
        `HTTP ${axiosErr.response.status}: ${axiosErr.response.statusText}`,
        { cause: err },
      );
    }
    // No response (network error) or the error we threw above — re-throw as-is.
    throw err;
  }
}

export const devicesApi = {
  list(): Promise<Device[]> {
    return unwrap(http.get("/devices/"));
  },

  get(id: string): Promise<Device> {
    return unwrap(http.get(`/devices/${id}/`));
  },

  create(payload: CreateDevicePayload): Promise<Device> {
    return unwrap(http.post("/devices/", payload));
  },

  update(id: string, payload: Partial<CreateDevicePayload>): Promise<Device> {
    return unwrap(http.put(`/devices/${id}/`, payload));
  },

  delete(id: string): Promise<null> {
    return unwrap(http.delete(`/devices/${id}/`));
  },

  start(id: string): Promise<Device> {
    return unwrap(http.post(`/devices/${id}/start/`));
  },

  stop(id: string): Promise<Device> {
    return unwrap(http.post(`/devices/${id}/stop/`));
  },

  status(id: string): Promise<DeviceStatusResponse> {
    return unwrap(http.get(`/devices/${id}/status/`));
  },

  availablePort(protocol: string): Promise<{ protocol: string; port: number }> {
    return unwrap(http.get("/ports/available/", { params: { protocol } }));
  },

  logs(id: string, lines = 100): Promise<string[]> {
    return unwrap(http.get(`/devices/${id}/logs/`, { params: { lines } }));
  },

  bulkStart(ids: string[]): Promise<{ started: string[]; errors: string[] }> {
    return unwrap(http.post("/devices/bulk_start/", { ids }));
  },

  bulkStop(ids: string[]): Promise<{ stopped: string[]; errors: string[] }> {
    return unwrap(http.post("/devices/bulk_stop/", { ids }));
  },
};
