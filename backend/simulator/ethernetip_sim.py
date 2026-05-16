"""EthernetIP / CIP server that runs inside a subprocess via cpppo."""

import logging
import signal

log = logging.getLogger(__name__)

# Minimum tag required by cpppo — used when config has no tags.
_DUMMY_TAG = "_SimDevice=INT"


def _build_argv(config: dict, port: int) -> list[str]:
    """Build the argv list for cpppo's enip main()."""
    tag_args: list[str] = []
    for tag in config.get("tags", []):
        # Format: TagName=TYPE  (e.g. "Pressure=REAL", "Count=DINT")
        tag_args.append(f"{tag['name']}={tag['type']}")

    if not tag_args:
        tag_args = [_DUMMY_TAG]

    return ["--address", f":{port}", "--no-udp"] + tag_args


def run(config: dict, port: int) -> None:
    """Block until SIGTERM/SIGINT, serving EthernetIP requests."""
    import cpppo.server.enip.main as enip_main

    control: dict[str, bool] = {"done": False}

    def _handle_stop(*_args: object) -> None:
        log.info("EthernetIP server stopping (port %d)", port)
        control["done"] = True

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    argv = _build_argv(config, port)
    log.info("EthernetIP server starting on port %d with tags: %s", port, argv)

    enip_main.main(argv=argv, server={"control": control})
