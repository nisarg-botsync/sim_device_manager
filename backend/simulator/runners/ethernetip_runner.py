"""Subprocess entry point for the EthernetIP / CIP simulator.

Environment variables:
  SIM_PORT    – TCP port to bind (integer)
  SIM_CONFIG  – JSON-encoded device config dict
"""

import json
import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="[ethernetip:%(process)d] %(levelname)s %(message)s",
    stream=sys.stderr,
)


def main() -> None:
    port = int(os.environ["SIM_PORT"])
    config = json.loads(os.environ["SIM_CONFIG"])

    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    from simulator.ethernetip_sim import run

    run(config, port)


if __name__ == "__main__":
    main()
