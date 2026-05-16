import { useEffect, useState } from "react";
import { devicesApi } from "../api/devices";
import type { Device, DeviceStatus } from "../types/device";

const POLL_INTERVAL_MS = 5000;
const ACTIVE_STATUSES = new Set<DeviceStatus>(["running", "starting"]);

interface UseDeviceStatusResult {
  status: DeviceStatus;
  pid: number | null;
}

/**
 * Polls /devices/{id}/status/ every 5s while the device is running or starting.
 *
 * Design notes:
 * - Only polls when the device's server-side status is active; stops otherwise.
 * - Uses a ref to always hold the latest device id without adding it to the
 *   polling interval's dependency array (avoids restarting the timer on every render).
 * - Does NOT sync props → state inside a useEffect to avoid the
 *   react-hooks/set-state-in-effect lint error; instead, polled data is kept
 *   separately and merged with prop values at return time.
 */
export function useDeviceStatus(device: Device): UseDeviceStatusResult {
  const [polledData, setPolledData] = useState<{
    status: DeviceStatus;
    pid: number | null;
  } | null>(null);

  const shouldPoll = ACTIVE_STATUSES.has(device.status);

  useEffect(() => {
    if (!shouldPoll) return;

    // Capture id in the closure; the effect re-runs if device.id changes.
    const id = device.id;
    const timer = setInterval(() => {
      devicesApi
        .status(id)
        .then((res) => {
          setPolledData({ status: res.status, pid: res.pid });
        })
        .catch(() => {
          // Network error — keep last known polled value
        });
    }, POLL_INTERVAL_MS);

    return () => clearInterval(timer);
  }, [shouldPoll, device.id]);

  // When the device is no longer active, discard stale polled data so we
  // always show the authoritative server-side values.
  const status = shouldPoll ? (polledData?.status ?? device.status) : device.status;
  const pid = shouldPoll ? (polledData?.pid ?? device.pid) : device.pid;

  return { status, pid };
}
