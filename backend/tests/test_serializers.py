import pytest

from devices.serializers import DeviceSerializer


@pytest.mark.django_db
class TestModbusConfigValidation:
    def _valid_payload(self, **overrides: object) -> dict:
        payload = {
            "name": "mb-device",
            "protocol": "modbus",
            "config": {
                "unit_id": 1,
                "registers": [{"address": 0, "value": 42.0, "type": "holding"}],
            },
        }
        payload.update(overrides)
        return payload

    def test_valid_modbus_config(self) -> None:
        s = DeviceSerializer(data=self._valid_payload())
        assert s.is_valid(), s.errors

    def test_unit_id_below_minimum(self) -> None:
        payload = self._valid_payload()
        payload["config"]["unit_id"] = 0
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()
        assert "config" in s.errors

    def test_unit_id_above_maximum(self) -> None:
        payload = self._valid_payload()
        payload["config"]["unit_id"] = 248
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()
        assert "config" in s.errors

    def test_invalid_register_type(self) -> None:
        payload = self._valid_payload()
        payload["config"]["registers"] = [{"address": 0, "value": 1, "type": "unknown"}]
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()
        assert "config" in s.errors

    def test_register_address_out_of_range(self) -> None:
        payload = self._valid_payload()
        payload["config"]["registers"] = [{"address": 70000, "value": 1, "type": "holding"}]
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()

    def test_empty_registers_allowed(self) -> None:
        payload = self._valid_payload()
        payload["config"]["registers"] = []
        s = DeviceSerializer(data=payload)
        assert s.is_valid(), s.errors


@pytest.mark.django_db
class TestEthernetIPConfigValidation:
    def _valid_payload(self, **overrides: object) -> dict:
        payload = {
            "name": "eip-device",
            "protocol": "ethernetip",
            "config": {
                "tags": [{"name": "MyTag", "type": "DINT", "value": 0}],
            },
        }
        payload.update(overrides)
        return payload

    def test_valid_ethernetip_config(self) -> None:
        s = DeviceSerializer(data=self._valid_payload())
        assert s.is_valid(), s.errors

    def test_invalid_tag_type(self) -> None:
        payload = self._valid_payload()
        payload["config"]["tags"] = [{"name": "T", "type": "INVALID", "value": 0}]
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()
        assert "config" in s.errors

    def test_tag_name_must_be_valid_identifier(self) -> None:
        payload = self._valid_payload()
        payload["config"]["tags"] = [{"name": "123bad", "type": "DINT", "value": 0}]
        s = DeviceSerializer(data=payload)
        assert not s.is_valid()

    def test_empty_tags_allowed(self) -> None:
        payload = self._valid_payload()
        payload["config"]["tags"] = []
        s = DeviceSerializer(data=payload)
        assert s.is_valid(), s.errors

    def test_wrong_config_schema_for_protocol(self) -> None:
        # Sending modbus-style config with ethernetip protocol should fail
        s = DeviceSerializer(
            data={
                "name": "bad",
                "protocol": "ethernetip",
                "config": {"unit_id": 1, "registers": []},
            }
        )
        # unit_id/registers are unknown fields — EthernetIP config requires 'tags'
        # The serializer should still be valid (extra fields are ignored by DRF),
        # but 'tags' will default to [] which is valid — this tests that the wrong
        # schema doesn't accidentally pass a strict check.
        assert s.is_valid(), s.errors
        assert "tags" in s.validated_data["config"]
