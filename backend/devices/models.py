import uuid

from django.db import models


class Device(models.Model):
    class Protocol(models.TextChoices):
        MODBUS = "modbus", "Modbus TCP"
        ETHERNETIP = "ethernetip", "EthernetIP"

    class Status(models.TextChoices):
        STOPPED = "stopped", "Stopped"
        STARTING = "starting", "Starting"
        RUNNING = "running", "Running"
        ERROR = "error", "Error"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    protocol = models.CharField(max_length=20, choices=Protocol.choices)
    port = models.IntegerField(unique=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STOPPED)
    pid = models.IntegerField(null=True, blank=True)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(protocol="modbus", port__gte=5020, port__lte=5099)
                    | models.Q(protocol="ethernetip", port__gte=44818, port__lte=44899)
                ),
                name="devices_valid_port_range",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.protocol}:{self.port})"
