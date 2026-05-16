from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from devices.models import Device
from devices.services import MODBUS_PORT_RANGE


@pytest.fixture()
def client() -> APIClient:
    return APIClient()


def _modbus_payload(name: str = "test-device") -> dict:
    return {
        "name": name,
        "protocol": "modbus",
        "config": {"unit_id": 1, "registers": [{"address": 0, "value": 0, "type": "holding"}]},
    }


def _create_via_api(client: APIClient, payload: dict | None = None) -> dict:
    if payload is None:
        payload = _modbus_payload()
    resp = client.post(reverse("device-list"), payload, format="json")
    assert resp.status_code == 201, resp.data
    return resp.data["data"]


@pytest.mark.django_db
class TestDeviceList:
    def test_empty_list(self, client: APIClient) -> None:
        resp = client.get(reverse("device-list"))
        assert resp.status_code == 200
        assert resp.data == {"data": [], "error": None}

    def test_list_returns_created_devices(self, client: APIClient) -> None:
        _create_via_api(client)
        resp = client.get(reverse("device-list"))
        assert len(resp.data["data"]) == 1


@pytest.mark.django_db
class TestDeviceCreate:
    def test_create_modbus_device(self, client: APIClient) -> None:
        resp = client.post(reverse("device-list"), _modbus_payload(), format="json")
        assert resp.status_code == 201
        data = resp.data["data"]
        assert data["protocol"] == "modbus"
        assert data["port"] == MODBUS_PORT_RANGE.start
        assert data["status"] == "stopped"
        assert resp.data["error"] is None

    def test_port_auto_assigned(self, client: APIClient) -> None:
        _create_via_api(client, _modbus_payload("dev-a"))
        data = _create_via_api(client, _modbus_payload("dev-b"))
        assert data["port"] == MODBUS_PORT_RANGE.start + 1

    def test_invalid_config_rejected(self, client: APIClient) -> None:
        payload = _modbus_payload()
        payload["config"]["unit_id"] = 999
        resp = client.post(reverse("device-list"), payload, format="json")
        assert resp.status_code == 400
        assert resp.data["error"] is not None

    def test_duplicate_name_rejected(self, client: APIClient) -> None:
        _create_via_api(client, _modbus_payload("dup"))
        resp = client.post(reverse("device-list"), _modbus_payload("dup"), format="json")
        assert resp.status_code == 400


@pytest.mark.django_db
class TestDeviceDetail:
    def test_retrieve_device(self, client: APIClient) -> None:
        created = _create_via_api(client)
        resp = client.get(reverse("device-detail", args=[created["id"]]))
        assert resp.status_code == 200
        assert resp.data["data"]["id"] == created["id"]

    def test_delete_stopped_device(self, client: APIClient) -> None:
        created = _create_via_api(client)
        resp = client.delete(reverse("device-detail", args=[created["id"]]))
        assert resp.status_code == 204

    def test_delete_running_device_rejected(self, client: APIClient) -> None:
        created = _create_via_api(client)
        device = Device.objects.get(pk=created["id"])
        device.status = Device.Status.RUNNING
        device.save()
        resp = client.delete(reverse("device-detail", args=[created["id"]]))
        assert resp.status_code == 400
        assert "stopped" in resp.data["error"]


@pytest.mark.django_db
class TestStartStop:
    def test_start_device(self, client: APIClient) -> None:
        created = _create_via_api(client)
        with patch("simulator.process_manager.process_manager.start_device") as mock_start:
            # Simulate ProcessManager updating the device to running
            def _fake_start(device: Device) -> None:
                device.status = Device.Status.RUNNING
                device.pid = 54321
                device.save(update_fields=["status", "pid", "updated_at"])

            mock_start.side_effect = _fake_start
            resp = client.post(reverse("device-start", args=[created["id"]]))

        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "running"
        assert resp.data["error"] is None

    def test_start_already_running_rejected(self, client: APIClient) -> None:
        created = _create_via_api(client)
        device = Device.objects.get(pk=created["id"])
        device.status = Device.Status.RUNNING
        device.save()
        resp = client.post(reverse("device-start", args=[created["id"]]))
        assert resp.status_code == 400

    def test_stop_device(self, client: APIClient) -> None:
        created = _create_via_api(client)
        device = Device.objects.get(pk=created["id"])
        device.status = Device.Status.RUNNING
        device.pid = 12345
        device.save()
        with patch("simulator.process_manager.process_manager.stop_device") as mock_stop:
            def _fake_stop(device: Device) -> None:
                device.status = Device.Status.STOPPED
                device.pid = None
                device.save(update_fields=["status", "pid", "updated_at"])

            mock_stop.side_effect = _fake_stop
            resp = client.post(reverse("device-stop", args=[created["id"]]))

        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "stopped"
        assert resp.data["data"]["pid"] is None

    def test_stop_already_stopped_rejected(self, client: APIClient) -> None:
        created = _create_via_api(client)
        resp = client.post(reverse("device-stop", args=[created["id"]]))
        assert resp.status_code == 400


@pytest.mark.django_db
class TestStatusEndpoint:
    def test_status_returns_device_status(self, client: APIClient) -> None:
        created = _create_via_api(client)
        resp = client.get(reverse("device-status", args=[created["id"]]))
        assert resp.status_code == 200
        assert resp.data["data"]["status"] == "stopped"
        assert resp.data["data"]["pid"] is None


@pytest.mark.django_db
class TestAvailablePorts:
    def test_modbus_available_port(self, client: APIClient) -> None:
        resp = client.get(reverse("available-ports"), {"protocol": "modbus"})
        assert resp.status_code == 200
        assert resp.data["data"]["port"] == MODBUS_PORT_RANGE.start

    def test_invalid_protocol_rejected(self, client: APIClient) -> None:
        resp = client.get(reverse("available-ports"), {"protocol": "unknown"})
        assert resp.status_code == 400
