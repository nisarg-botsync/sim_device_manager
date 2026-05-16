from rest_framework import serializers

from .models import Device


# ---------------------------------------------------------------------------
# Protocol config sub-serializers
# ---------------------------------------------------------------------------

REGISTER_TYPES = ["holding", "input", "coil", "discrete"]
TAG_TYPES = ["BOOL", "INT", "DINT", "REAL", "STRING"]


class ModbusRegisterSerializer(serializers.Serializer):
    address = serializers.IntegerField(min_value=0, max_value=65535)
    value = serializers.FloatField(default=0)
    type = serializers.ChoiceField(choices=REGISTER_TYPES)


class ModbusConfigSerializer(serializers.Serializer):
    unit_id = serializers.IntegerField(min_value=1, max_value=247, default=1)
    registers = ModbusRegisterSerializer(many=True, default=list)


class EthernetIPTagSerializer(serializers.Serializer):
    name = serializers.RegexField(
        r"^[A-Za-z_][A-Za-z0-9_]*$",
        max_length=100,
        error_messages={"invalid": "Tag name must be a valid identifier (letters, digits, underscores)."},
    )
    type = serializers.ChoiceField(choices=TAG_TYPES)
    value = serializers.JSONField(default=None)


class EthernetIPConfigSerializer(serializers.Serializer):
    tags = EthernetIPTagSerializer(many=True, default=list)


# ---------------------------------------------------------------------------
# Device serializer
# ---------------------------------------------------------------------------

_CONFIG_SERIALIZERS = {
    Device.Protocol.MODBUS: ModbusConfigSerializer,
    Device.Protocol.ETHERNETIP: EthernetIPConfigSerializer,
}


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            "id",
            "name",
            "protocol",
            "port",
            "status",
            "pid",
            "config",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "port", "status", "pid", "created_at", "updated_at"]

    def validate(self, attrs: dict) -> dict:
        # On partial updates the protocol may come from the existing instance.
        protocol = attrs.get("protocol") or (self.instance.protocol if self.instance else None)
        config = attrs.get("config", self.instance.config if self.instance else {})

        if protocol is None:
            raise serializers.ValidationError({"protocol": "This field is required."})

        config_cls = _CONFIG_SERIALIZERS.get(protocol)
        if config_cls is None:
            raise serializers.ValidationError({"protocol": f"Unknown protocol '{protocol}'."})

        config_serializer = config_cls(data=config)
        if not config_serializer.is_valid():
            raise serializers.ValidationError({"config": config_serializer.errors})

        attrs["config"] = config_serializer.validated_data
        return attrs
