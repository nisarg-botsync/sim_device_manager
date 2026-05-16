import type { Device, EthernetIPConfig, ModbusConfig } from "../types/device";

interface ConfigViewerProps {
  device: Device;
}

export function ConfigViewer({ device }: ConfigViewerProps) {
  if (device.protocol === "modbus") {
    const config = device.config as ModbusConfig;
    return (
      <div className="space-y-3">
        <div className="flex gap-4 text-sm">
          <span className="text-gray-500">Unit ID</span>
          <span className="font-mono font-medium">{config.unit_id}</span>
        </div>
        {config.registers.length === 0 ? (
          <p className="text-sm text-gray-400 italic">No registers configured</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs text-gray-500">
                <th className="pb-1 pr-4">Address</th>
                <th className="pb-1 pr-4">Type</th>
                <th className="pb-1">Value</th>
              </tr>
            </thead>
            <tbody className="font-mono">
              {config.registers.map((r, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-1 pr-4">{r.address}</td>
                  <td className="py-1 pr-4 text-gray-500">{r.type}</td>
                  <td className="py-1">{r.value}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  }

  const config = device.config as EthernetIPConfig;
  return (
    <div className="space-y-3">
      {config.tags.length === 0 ? (
        <p className="text-sm text-gray-400 italic">No tags configured</p>
      ) : (
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-xs text-gray-500">
              <th className="pb-1 pr-4">Name</th>
              <th className="pb-1 pr-4">Type</th>
              <th className="pb-1">Value</th>
            </tr>
          </thead>
          <tbody className="font-mono">
            {config.tags.map((t, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-1 pr-4">{t.name}</td>
                <td className="py-1 pr-4 text-gray-500">{t.type}</td>
                <td className="py-1">{String(t.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
