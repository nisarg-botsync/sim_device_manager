import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { devicesApi } from "../api/devices";
import { ConfigViewer } from "../components/ConfigViewer";
import { LogViewer } from "../components/LogViewer";
import { StatusBadge } from "../components/StatusBadge";
import { useDeviceStatus } from "../hooks/useDeviceStatus";
import type { Device } from "../types/device";

export function DeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [device, setDevice] = useState<Device | null>(null);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!id) return;
    devicesApi
      .get(id)
      .then(setDevice)
      .catch((e: unknown) => setFetchError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [id]);

  // Live polling — only active while device is running/starting
  const { status, pid } = useDeviceStatus(device ?? { status: "stopped", pid: null } as Device);

  const handleStart = async () => {
    if (!device) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await devicesApi.start(device.id);
      setDevice(updated);
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleStop = async () => {
    if (!device) return;
    setBusy(true);
    setActionError(null);
    try {
      const updated = await devicesApi.stop(device.id);
      setDevice(updated);
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  const handleDelete = async () => {
    if (!device) return;
    if (!window.confirm(`Delete "${device.name}"? This cannot be undone.`)) return;
    setBusy(true);
    setActionError(null);
    try {
      await devicesApi.delete(device.id);
      navigate("/");
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="mx-auto max-w-3xl px-4 py-8 text-gray-500">Loading...</div>;
  }

  if (fetchError || !device) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-8">
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {fetchError ?? "Device not found"}
        </div>
        <Link to="/" className="mt-4 inline-block text-sm text-indigo-600 hover:underline">
          ← Back to list
        </Link>
      </div>
    );
  }

  const canStart = status === "stopped" || status === "error";
  const canStop = status === "running" || status === "starting";
  const canDelete = status === "stopped";

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      {/* Header */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <Link to="/" className="mb-2 inline-block text-sm text-gray-400 hover:text-gray-600">
            ← Devices
          </Link>
          <h1 className="text-2xl font-semibold text-gray-900">{device.name}</h1>
          <p className="mt-1 text-sm text-gray-500 capitalize">
            {device.protocol} · port {device.port}
          </p>
        </div>
        <StatusBadge status={status} />
      </div>

      {/* PID info */}
      {pid !== null && (
        <p className="mb-4 text-xs text-gray-400">PID {pid}</p>
      )}

      {/* Error banner */}
      {actionError && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </div>
      )}

      {/* Controls */}
      <div className="mb-8 flex gap-3">
        {canStart && (
          <button
            onClick={handleStart}
            disabled={busy}
            className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-500 disabled:opacity-50"
          >
            {busy ? "Starting..." : "Start"}
          </button>
        )}
        {canStop && (
          <button
            onClick={handleStop}
            disabled={busy}
            className="rounded-md bg-amber-600 px-4 py-2 text-sm font-medium text-white hover:bg-amber-500 disabled:opacity-50"
          >
            {busy ? "Stopping..." : "Stop"}
          </button>
        )}
        {canDelete && (
          <button
            onClick={handleDelete}
            disabled={busy}
            className="rounded-md px-4 py-2 text-sm font-medium text-red-600 ring-1 ring-red-200 hover:bg-red-50 disabled:opacity-50"
          >
            Delete
          </button>
        )}
      </div>

      {/* Config */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wider text-gray-500">
          Configuration
        </h2>
        <ConfigViewer device={{ ...device, status, pid }} />
      </div>

      {/* Logs */}
      <LogViewer deviceId={device.id} status={status} />

      {/* Timestamps */}
      <div className="mt-4 flex gap-6 text-xs text-gray-400">
        <span>Created {new Date(device.created_at).toLocaleString()}</span>
        <span>Updated {new Date(device.updated_at).toLocaleString()}</span>
      </div>
    </div>
  );
}
