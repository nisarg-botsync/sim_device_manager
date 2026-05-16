import { useEffect, useRef, useState } from "react";
import { devicesApi } from "../api/devices";
import type { DeviceStatus } from "../types/device";

interface LogViewerProps {
  deviceId: string;
  status: DeviceStatus;
}

const POLL_INTERVAL_MS = 5000;
const ACTIVE_STATUSES = new Set<DeviceStatus>(["running", "starting"]);

export function LogViewer({ deviceId, status }: LogViewerProps) {
  const [lines, setLines] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const fetchLogs = () => {
    devicesApi
      .logs(deviceId, 200)
      .then((data) => {
        setLines(data);
        setError(null);
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : String(e)));
  };

  // Fetch once when panel opens.
  useEffect(() => {
    if (!open) return;
    fetchLogs();
  // fetchLogs is stable (no deps) so safe to omit from the array.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, deviceId]);

  // Poll while running/starting and panel is open.
  useEffect(() => {
    if (!open || !ACTIVE_STATUSES.has(status)) return;
    const timer = setInterval(fetchLogs, POLL_INTERVAL_MS);
    return () => clearInterval(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, status, deviceId]);

  // Auto-scroll to bottom when new lines arrive.
  useEffect(() => {
    if (open && bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [lines, open]);

  return (
    <div className="mt-6 rounded-lg border border-gray-200 bg-white shadow-sm">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-6 py-4 text-left"
      >
        <span className="text-sm font-semibold uppercase tracking-wider text-gray-500">
          Logs
        </span>
        <span className="text-xs text-gray-400">{open ? "▲ hide" : "▼ show"}</span>
      </button>

      {open && (
        <div className="border-t border-gray-100">
          {error && (
            <p className="px-4 py-2 text-xs text-red-500">{error}</p>
          )}
          {lines.length === 0 && !error ? (
            <p className="px-6 py-4 text-sm text-gray-400 italic">No log output yet.</p>
          ) : (
            <pre className="max-h-80 overflow-y-auto bg-gray-950 px-4 py-3 text-xs leading-relaxed text-gray-200 font-mono">
              {lines.map((line, i) => (
                <div key={i}>{line}</div>
              ))}
              <div ref={bottomRef} />
            </pre>
          )}
          <div className="flex items-center justify-between border-t border-gray-100 px-4 py-2">
            <span className="text-xs text-gray-400">
              {lines.length} line{lines.length !== 1 ? "s" : ""}
              {ACTIVE_STATUSES.has(status) ? " · polling" : ""}
            </span>
            <button
              type="button"
              onClick={fetchLogs}
              className="text-xs text-indigo-500 hover:underline"
            >
              Refresh
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
