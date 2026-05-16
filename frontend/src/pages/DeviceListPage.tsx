import { useState } from "react";
import { Link } from "react-router-dom";
import { devicesApi } from "../api/devices";
import { StatusBadge } from "../components/StatusBadge";
import { useDevices } from "../hooks/useDevices";
import type { Device } from "../types/device";

export function DeviceListPage() {
  const { devices, loading, error, refresh } = useDevices();
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);     // single-device action id
  const [bulkBusy, setBulkBusy] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());

  // ----- selection helpers -----

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleAll = () => {
    setSelected((prev) =>
      prev.size === devices.length ? new Set() : new Set(devices.map((d) => d.id))
    );
  };

  // Clear selection after list refreshes (devices may have changed).
  const refreshAndClear = () => {
    setSelected(new Set());
    refresh();
  };

  // ----- single device actions -----

  const handleStart = async (device: Device) => {
    setBusy(device.id);
    setActionError(null);
    try {
      await devicesApi.start(device.id);
      refresh();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const handleStop = async (device: Device) => {
    setBusy(device.id);
    setActionError(null);
    try {
      await devicesApi.stop(device.id);
      refresh();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  const handleDelete = async (device: Device) => {
    if (!window.confirm(`Delete "${device.name}"? This cannot be undone.`)) return;
    setBusy(device.id);
    setActionError(null);
    try {
      await devicesApi.delete(device.id);
      refreshAndClear();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(null);
    }
  };

  // ----- bulk actions -----

  const handleBulkStart = async () => {
    setBulkBusy(true);
    setActionError(null);
    try {
      const result = await devicesApi.bulkStart([...selected]);
      if (result.errors.length > 0) setActionError(result.errors.join("; "));
      refreshAndClear();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBulkBusy(false);
    }
  };

  const handleBulkStop = async () => {
    setBulkBusy(true);
    setActionError(null);
    try {
      const result = await devicesApi.bulkStop([...selected]);
      if (result.errors.length > 0) setActionError(result.errors.join("; "));
      refreshAndClear();
    } catch (e: unknown) {
      setActionError(e instanceof Error ? e.message : String(e));
    } finally {
      setBulkBusy(false);
    }
  };

  const anySelected = selected.size > 0;
  const allSelected = devices.length > 0 && selected.size === devices.length;

  return (
    <div className="mx-auto max-w-6xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-gray-900">Simulated Devices</h1>
        <Link
          to="/devices/new"
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-600 focus:ring-offset-2"
        >
          + Add Device
        </Link>
      </div>

      {/* Bulk action bar */}
      {anySelected && (
        <div className="mb-4 flex items-center gap-3 rounded-lg bg-indigo-50 px-4 py-2.5">
          <span className="text-sm font-medium text-indigo-800">
            {selected.size} selected
          </span>
          <button
            onClick={handleBulkStart}
            disabled={bulkBusy}
            className="rounded px-3 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-500 disabled:opacity-50"
          >
            Start all
          </button>
          <button
            onClick={handleBulkStop}
            disabled={bulkBusy}
            className="rounded px-3 py-1 text-xs font-medium text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-50"
          >
            Stop all
          </button>
          <button
            onClick={() => setSelected(new Set())}
            className="ml-auto text-xs text-gray-400 hover:text-gray-600"
          >
            Clear
          </button>
        </div>
      )}

      {actionError && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {actionError}
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load devices: {error}
        </div>
      )}

      {loading ? (
        <p className="text-gray-500">Loading...</p>
      ) : devices.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-gray-200 py-16 text-center">
          <p className="text-gray-400">No devices yet.</p>
          <Link to="/devices/new" className="mt-2 text-sm text-indigo-600 hover:underline">
            Add your first device
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="w-10 px-4 py-3">
                  <input
                    type="checkbox"
                    checked={allSelected}
                    onChange={toggleAll}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    aria-label="Select all"
                  />
                </th>
                {["Name", "Protocol", "Port", "Status", "Actions"].map((h) => (
                  <th
                    key={h}
                    className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 bg-white">
              {devices.map((device) => (
                <tr
                  key={device.id}
                  className={`hover:bg-gray-50 ${selected.has(device.id) ? "bg-indigo-50" : ""}`}
                >
                  <td className="px-4 py-4">
                    <input
                      type="checkbox"
                      checked={selected.has(device.id)}
                      onChange={() => toggleSelect(device.id)}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                      aria-label={`Select ${device.name}`}
                    />
                  </td>
                  <td className="px-6 py-4">
                    <Link
                      to={`/devices/${device.id}`}
                      className="font-medium text-indigo-600 hover:underline"
                    >
                      {device.name}
                    </Link>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 capitalize">{device.protocol}</td>
                  <td className="px-6 py-4 font-mono text-sm text-gray-600">{device.port}</td>
                  <td className="px-6 py-4">
                    <StatusBadge status={device.status} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {device.status === "stopped" || device.status === "error" ? (
                        <button
                          onClick={() => handleStart(device)}
                          disabled={busy === device.id}
                          className="rounded px-2.5 py-1 text-xs font-medium text-white bg-green-600 hover:bg-green-500 disabled:opacity-50"
                        >
                          Start
                        </button>
                      ) : (
                        <button
                          onClick={() => handleStop(device)}
                          disabled={busy === device.id}
                          className="rounded px-2.5 py-1 text-xs font-medium text-white bg-amber-600 hover:bg-amber-500 disabled:opacity-50"
                        >
                          Stop
                        </button>
                      )}
                      <Link
                        to={`/devices/${device.id}`}
                        className="rounded px-2.5 py-1 text-xs font-medium text-gray-600 ring-1 ring-gray-300 hover:bg-gray-50"
                      >
                        Details
                      </Link>
                      {device.status === "stopped" && (
                        <button
                          onClick={() => handleDelete(device)}
                          disabled={busy === device.id}
                          className="rounded px-2.5 py-1 text-xs font-medium text-red-600 ring-1 ring-red-200 hover:bg-red-50 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
