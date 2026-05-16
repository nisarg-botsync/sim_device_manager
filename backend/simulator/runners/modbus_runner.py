"""Subprocess entry point for the Modbus TCP simulator.

Invoked by ProcessManager via subprocess.Popen.  Reads configuration from
environment variables so no Django ORM access is required inside the process.

Environment variables:
  SIM_PORT    – TCP port to bind (integer)
  SIM_CONFIG  – JSON-encoded device config dict
"""

import asyncio
import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[modbus:%(process)d] %(levelname)s %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    port = int(os.environ["SIM_PORT"])
    config = json.loads(os.environ["SIM_CONFIG"])

    # Ensure backend/ is importable (needed when spawned fresh by Popen).
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from simulator.modbus_sim import run_async

    asyncio.run(run_async(config, port))


if __name__ == "__main__":
    main()
