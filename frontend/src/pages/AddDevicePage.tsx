import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { devicesApi } from "../api/devices";
import type {
  EthernetIPTag,
  ModbusRegister,
  Protocol,
} from "../types/device";

const MODBUS_REGISTER_TYPES = ["holding", "input", "coil", "discrete"] as const;
const ETHERNETIP_TAG_TYPES = ["BOOL", "INT", "DINT", "REAL", "STRING"] as const;

function emptyRegister(): ModbusRegister {
  return { address: 0, value: 0, type: "holding" };
}

function emptyTag(): EthernetIPTag {
  return { name: "", type: "DINT", value: 0 };
}

export function AddDevicePage() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [protocol, setProtocol] = useState<Protocol>("modbus");
  const [unitId, setUnitId] = useState(1);
  const [registers, setRegisters] = useState<ModbusRegister[]>([emptyRegister()]);
  const [tags, setTags] = useState<EthernetIPTag[]>([emptyTag()]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // ----- register helpers -----

  const updateRegister = (i: number, patch: Partial<ModbusRegister>) => {
    setRegisters((prev) => prev.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  };

  const removeRegister = (i: number) => {
    setRegisters((prev) => prev.filter((_, idx) => idx !== i));
  };

  // ----- tag helpers -----

  const updateTag = (i: number, patch: Partial<EthernetIPTag>) => {
    setTags((prev) => prev.map((t, idx) => (idx === i ? { ...t, ...patch } : t)));
  };

  const removeTag = (i: number) => {
    setTags((prev) => prev.filter((_, idx) => idx !== i));
  };

  // ----- submit -----

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const config =
      protocol === "modbus"
        ? { unit_id: unitId, registers }
        : { tags };

    try {
      const device = await devicesApi.create({ name, protocol, config });
      navigate(`/devices/${device.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-8">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Add Device</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Name</label>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            placeholder="e.g. plc-line-a"
          />
        </div>

        {/* Protocol */}
        <div>
          <label className="block text-sm font-medium text-gray-700">Protocol</label>
          <div className="mt-1 flex gap-4">
            {(["modbus", "ethernetip"] as Protocol[]).map((p) => (
              <label key={p} className="flex cursor-pointer items-center gap-2 text-sm">
                <input
                  type="radio"
                  name="protocol"
                  value={p}
                  checked={protocol === p}
                  onChange={() => setProtocol(p)}
                  className="text-indigo-600 focus:ring-indigo-500"
                />
                {p === "modbus" ? "Modbus TCP" : "EthernetIP"}
              </label>
            ))}
          </div>
        </div>

        {/* Protocol-specific config */}
        {protocol === "modbus" ? (
          <div className="space-y-4 rounded-lg bg-gray-50 p-4">
            <h2 className="text-sm font-semibold text-gray-700">Modbus Config</h2>

            <div>
              <label className="block text-xs font-medium text-gray-600">Unit ID (1–247)</label>
              <input
                type="number"
                min={1}
                max={247}
                value={unitId}
                onChange={(e) => setUnitId(Number(e.target.value))}
                className="mt-1 w-24 rounded border border-gray-300 px-2 py-1 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">Registers</span>
                <button
                  type="button"
                  onClick={() => setRegisters((prev) => [...prev, emptyRegister()])}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  + Add register
                </button>
              </div>

              {registers.length === 0 && (
                <p className="text-xs text-gray-400 italic">No registers — device starts with empty datastore</p>
              )}

              {registers.map((r, i) => (
                <div key={i} className="mb-2 flex items-center gap-2">
                  <input
                    type="number"
                    min={0}
                    max={65535}
                    value={r.address}
                    onChange={(e) => updateRegister(i, { address: Number(e.target.value) })}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                    placeholder="Address"
                  />
                  <select
                    value={r.type}
                    onChange={(e) =>
                      updateRegister(i, { type: e.target.value as ModbusRegister["type"] })
                    }
                    className="rounded border border-gray-300 px-2 py-1 text-sm"
                  >
                    {MODBUS_REGISTER_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    value={r.value}
                    onChange={(e) => updateRegister(i, { value: Number(e.target.value) })}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                    placeholder="Value"
                  />
                  <button
                    type="button"
                    onClick={() => removeRegister(i)}
                    className="text-red-400 hover:text-red-600"
                    aria-label="Remove register"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 rounded-lg bg-gray-50 p-4">
            <h2 className="text-sm font-semibold text-gray-700">EthernetIP Config</h2>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">Tags</span>
                <button
                  type="button"
                  onClick={() => setTags((prev) => [...prev, emptyTag()])}
                  className="text-xs text-indigo-600 hover:underline"
                >
                  + Add tag
                </button>
              </div>

              {tags.length === 0 && (
                <p className="text-xs text-gray-400 italic">No tags — a placeholder tag will be created automatically</p>
              )}

              {tags.map((t, i) => (
                <div key={i} className="mb-2 flex items-center gap-2">
                  <input
                    type="text"
                    value={t.name}
                    onChange={(e) => updateTag(i, { name: e.target.value })}
                    className="w-36 rounded border border-gray-300 px-2 py-1 text-sm font-mono"
                    placeholder="TagName"
                  />
                  <select
                    value={t.type}
                    onChange={(e) =>
                      updateTag(i, { type: e.target.value as EthernetIPTag["type"] })
                    }
                    className="rounded border border-gray-300 px-2 py-1 text-sm"
                  >
                    {ETHERNETIP_TAG_TYPES.map((tp) => (
                      <option key={tp} value={tp}>{tp}</option>
                    ))}
                  </select>
                  <input
                    type="text"
                    value={String(t.value)}
                    onChange={(e) => updateTag(i, { value: e.target.value })}
                    className="w-24 rounded border border-gray-300 px-2 py-1 text-sm"
                    placeholder="Value"
                  />
                  <button
                    type="button"
                    onClick={() => removeTag(i)}
                    className="text-red-400 hover:text-red-600"
                    aria-label="Remove tag"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
        )}

        <div className="flex gap-3">
          <button
            type="submit"
            disabled={submitting}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create Device"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/")}
            className="rounded-md px-4 py-2 text-sm font-medium text-gray-600 ring-1 ring-gray-300 hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
