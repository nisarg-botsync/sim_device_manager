from django.db import transaction

from .models import Device

MODBUS_PORT_RANGE = range(5020, 5100)
ETHERNETIP_PORT_RANGE = range(44818, 44900)


def _port_range(protocol: str) -> range:
    if protocol == Device.Protocol.MODBUS:
        return MODBUS_PORT_RANGE
    return ETHERNETIP_PORT_RANGE


def allocate_port(protocol: str) -> int:
    """Atomically claim the lowest available port for the given protocol.

    Uses SELECT FOR UPDATE to prevent two concurrent requests from claiming
    the same port. Must be called inside the same transaction as the Device
    INSERT (i.e. within perform_create).
    """
    with transaction.atomic():
        used_ports = set(
            Device.objects.select_for_update()
            .filter(protocol=protocol)
            .values_list("port", flat=True)
        )
        for port in _port_range(protocol):
            if port not in used_ports:
                return port
        raise ValueError(f"No available ports for protocol '{protocol}' — all ports exhausted")


def peek_next_port(protocol: str) -> int:
    """Return the next available port without locking (for informational use only)."""
    used_ports = set(Device.objects.filter(protocol=protocol).values_list("port", flat=True))
    for port in _port_range(protocol):
        if port not in used_ports:
            return port
    raise ValueError(f"No available ports for protocol '{protocol}' — all ports exhausted")
