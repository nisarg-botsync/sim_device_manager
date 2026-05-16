import pytest

from devices.models import Device
from devices.services import ETHERNETIP_PORT_RANGE, MODBUS_PORT_RANGE, allocate_port, peek_next_port


def _create_device(protocol: str, port: int, name: str) -> Device:
    config = {"unit_id": 1, "registers": []} if protocol == "modbus" else {"tags": []}
    return Device.objects.create(name=name, protocol=protocol, port=port, config=config)


@pytest.mark.django_db
class TestAllocatePort:
    def test_first_modbus_port_is_range_start(self) -> None:
        port = allocate_port(Device.Protocol.MODBUS)
        assert port == MODBUS_PORT_RANGE.start

    def test_first_ethernetip_port_is_range_start(self) -> None:
        port = allocate_port(Device.Protocol.ETHERNETIP)
        assert port == ETHERNETIP_PORT_RANGE.start

    def test_allocates_next_port_after_existing(self) -> None:
        _create_device("modbus", MODBUS_PORT_RANGE.start, "dev-a")
        port = allocate_port(Device.Protocol.MODBUS)
        assert port == MODBUS_PORT_RANGE.start + 1

    def test_skips_occupied_ports(self) -> None:
        # Occupy first and third ports; second should be returned
        _create_device("modbus", MODBUS_PORT_RANGE.start, "dev-a")
        _create_device("modbus", MODBUS_PORT_RANGE.start + 2, "dev-c")
        port = allocate_port(Device.Protocol.MODBUS)
        assert port == MODBUS_PORT_RANGE.start + 1

    def test_protocols_use_independent_ranges(self) -> None:
        modbus_port = allocate_port(Device.Protocol.MODBUS)
        eip_port = allocate_port(Device.Protocol.ETHERNETIP)
        assert modbus_port != eip_port
        assert modbus_port in MODBUS_PORT_RANGE
        assert eip_port in ETHERNETIP_PORT_RANGE

    def test_raises_when_all_ports_exhausted(self) -> None:
        # Fill all modbus ports
        for i, port in enumerate(MODBUS_PORT_RANGE):
            _create_device("modbus", port, f"dev-{i}")
        with pytest.raises(ValueError, match="No available ports"):
            allocate_port(Device.Protocol.MODBUS)


@pytest.mark.django_db
class TestPeekNextPort:
    def test_peek_does_not_reserve_port(self) -> None:
        port1 = peek_next_port(Device.Protocol.MODBUS)
        port2 = peek_next_port(Device.Protocol.MODBUS)
        assert port1 == port2  # no device was created, so same port each time

    def test_peek_reflects_existing_devices(self) -> None:
        _create_device("modbus", MODBUS_PORT_RANGE.start, "dev-a")
        port = peek_next_port(Device.Protocol.MODBUS)
        assert port == MODBUS_PORT_RANGE.start + 1
