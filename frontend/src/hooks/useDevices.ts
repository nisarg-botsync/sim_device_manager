import { useCallback, useEffect, useState } from "react";
import { devicesApi } from "../api/devices";
import type { Device } from "../types/device";

interface UseDevicesResult {
  devices: Device[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useDevices(): UseDevicesResult {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Increment to trigger a refetch without setting loading=true synchronously
  // inside the effect (which would violate react-hooks/set-state-in-effect).
  const [fetchCount, setFetchCount] = useState(0);

  const refresh = useCallback(() => setFetchCount((c) => c + 1), []);

  useEffect(() => {
    let cancelled = false;
    devicesApi
      .list()
      .then((data) => {
        if (!cancelled) {
          setDevices(data);
          setLoading(false);
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : String(e));
          setLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [fetchCount]);

  return { devices, loading, error, refresh };
}
