export type Protocol = "modbus" | "ethernetip";

export type DeviceStatus = "stopped" | "starting" | "running" | "error";

export interface ModbusRegister {
  address: number;
  value: number;
  type: "holding" | "input" | "coil" | "discrete";
}

export interface ModbusConfig {
  unit_id: number;
  registers: ModbusRegister[];
}

export interface EthernetIPTag {
  name: string;
  type: "BOOL" | "INT" | "DINT" | "REAL" | "STRING";
  value: unknown;
}

export interface EthernetIPConfig {
  tags: EthernetIPTag[];
}

export type DeviceConfig = ModbusConfig | EthernetIPConfig;

export interface Device {
  id: string;
  name: string;
  protocol: Protocol;
  port: number;
  status: DeviceStatus;
  pid: number | null;
  config: DeviceConfig;
  created_at: string;
  updated_at: string;
}

export interface DeviceStatusResponse {
  status: DeviceStatus;
  pid: number | null;
}

export interface CreateDevicePayload {
  name: string;
  protocol: Protocol;
  config: DeviceConfig;
}
