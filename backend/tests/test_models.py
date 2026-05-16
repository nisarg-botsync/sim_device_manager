import pytest
from django.db import IntegrityError

from devices.models import Device


def make_device(**kwargs) -> Device:
    defaults = {
        "name": "test-device",
        "protocol": Device.Protocol.MODBUS,
        "port": 5020,
        "config": {"unit_id": 1, "registers": []},
    }
    defaults.update(kwargs)
    return Device.objects.create(**defaults)


@pytest.mark.django_db
class TestDeviceModel:
    def test_create_modbus_device(self) -> None:
        device = make_device()
        assert device.pk is not None
        assert device.status == Device.Status.STOPPED
        assert device.pid is None

    def test_create_ethernetip_device(self) -> None:
        device = make_device(
            name="eip-device",
            protocol=Device.Protocol.ETHERNETIP,
            port=44818,
            config={"tags": []},
        )
        assert device.protocol == Device.Protocol.ETHERNETIP

    def test_name_must_be_unique(self) -> None:
        make_device(name="dup")
        with pytest.raises(IntegrityError):
            make_device(name="dup", port=5021)

    def test_port_must_be_unique(self) -> None:
        make_device(port=5020)
        with pytest.raises(IntegrityError):
            make_device(name="second", port=5020)

    def test_str_representation(self) -> None:
        device = make_device()
        assert "test-device" in str(device)
        assert "modbus" in str(device)
        assert "5020" in str(device)

    def test_default_status_is_stopped(self) -> None:
        device = make_device()
        assert device.status == "stopped"
