"""Asyncio Modbus TCP server that runs inside a subprocess."""

import asyncio
import logging
import signal

from pymodbus.server import ModbusTcpServer
from pymodbus.simulator.simdata import DataType, SimData
from pymodbus.simulator.simdevice import SimDevice

log = logging.getLogger(__name__)


def _build_sim_device(config: dict) -> SimDevice:
    """Build a SimDevice from the device config dict."""
    unit_id = int(config.get("unit_id", 1))

    di: list[SimData] = []
    co: list[SimData] = []
    ir: list[SimData] = []
    hr: list[SimData] = []

    for reg in config.get("registers", []):
        addr = int(reg["address"])
        val = int(reg.get("value", 0))
        match reg.get("type", "holding"):
            case "discrete":
                di.append(SimData(addr, values=val, datatype=DataType.BITS))
            case "coil":
                co.append(SimData(addr, values=val, datatype=DataType.BITS))
            case "input":
                ir.append(SimData(addr, values=val, datatype=DataType.REGISTERS))
            case "holding":
                hr.append(SimData(addr, values=val, datatype=DataType.REGISTERS))

    # Each list must have at least one entry.
    def _default(lst: list[SimData], dtype: DataType) -> list[SimData]:
        return lst if lst else [SimData(0, values=0, datatype=dtype)]

    return SimDevice(
        id=unit_id,
        simdata=(
            _default(di, DataType.BITS),
            _default(co, DataType.BITS),
            _default(ir, DataType.REGISTERS),
            _default(hr, DataType.REGISTERS),
        ),
    )


async def run_async(config: dict, port: int) -> None:
    server = ModbusTcpServer(context=_build_sim_device(config), address=("", port))

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGTERM, stop_event.set)
    loop.add_signal_handler(signal.SIGINT, stop_event.set)

    log.info("Modbus TCP server starting on port %d", port)
    serve_task = asyncio.create_task(server.serve_forever())

    await stop_event.wait()
    log.info("Modbus TCP server shutting down (port %d)", port)
    await server.shutdown()
    serve_task.cancel()
    try:
        await serve_task
    except asyncio.CancelledError:
        pass
