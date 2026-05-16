import type { DeviceStatus } from "../types/device";

interface StatusBadgeProps {
  status: DeviceStatus;
}

const STATUS_STYLES: Record<DeviceStatus, string> = {
  running: "bg-green-100 text-green-800 ring-green-600/20",
  starting: "bg-yellow-100 text-yellow-800 ring-yellow-600/20",
  stopped: "bg-gray-100 text-gray-700 ring-gray-500/20",
  error: "bg-red-100 text-red-800 ring-red-600/20",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ring-1 ring-inset ${STATUS_STYLES[status]}`}
    >
      {status === "starting" && (
        <span className="mr-1 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-yellow-500" />
      )}
      {status === "running" && (
        <span className="mr-1 inline-block h-1.5 w-1.5 rounded-full bg-green-500" />
      )}
      {status}
    </span>
  );
}
