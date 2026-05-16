import json

from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Device
from .serializers import DeviceSerializer
from .services import allocate_port, peek_next_port


def _ok(data: object, status_code: int = status.HTTP_200_OK) -> Response:
    return Response({"data": data, "error": None}, status=status_code)


def _err(message: object, status_code: int = status.HTTP_400_BAD_REQUEST) -> Response:
    # Ensure error is always a plain string so the frontend can display it directly.
    if not isinstance(message, str):
        message = json.dumps(message)
    return Response({"data": None, "error": message}, status=status_code)


class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all().order_by("created_at")
    serializer_class = DeviceSerializer

    # ------------------------------------------------------------------
    # Override standard CRUD responses to match { data, error } format
    # ------------------------------------------------------------------

    def list(self, request: Request, *args: object, **kwargs: object) -> Response:
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return _ok(serializer.data)

    def retrieve(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(self.get_object())
        return _ok(serializer.data)

    def create(self, request: Request, *args: object, **kwargs: object) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return _err(serializer.errors, status.HTTP_400_BAD_REQUEST)
        try:
            port = allocate_port(serializer.validated_data["protocol"])
        except ValueError as exc:
            return _err(str(exc), status.HTTP_409_CONFLICT)
        device = serializer.save(port=port)
        return _ok(DeviceSerializer(device).data, status.HTTP_201_CREATED)

    def update(self, request: Request, *args: object, **kwargs: object) -> Response:
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if not serializer.is_valid():
            return _err(serializer.errors, status.HTTP_400_BAD_REQUEST)
        device = serializer.save()
        return _ok(DeviceSerializer(device).data)

    def destroy(self, request: Request, *args: object, **kwargs: object) -> Response:
        device = self.get_object()
        if device.status != Device.Status.STOPPED:
            return _err("Device must be stopped before deletion.")
        device.delete()
        return _ok(None, status.HTTP_204_NO_CONTENT)

    # ------------------------------------------------------------------
    # Per-device actions
    # ------------------------------------------------------------------

    @action(detail=True, methods=["post"])
    def start(self, request: Request, pk: str | None = None) -> Response:
        device = self.get_object()
        if device.status in (Device.Status.RUNNING, Device.Status.STARTING):
            return _err(f"Device is already {device.status}.")
        from simulator.process_manager import process_manager
        try:
            process_manager.start_device(device)
        except Exception as exc:
            return _err(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        device.refresh_from_db()
        return _ok(DeviceSerializer(device).data)

    @action(detail=True, methods=["post"])
    def stop(self, request: Request, pk: str | None = None) -> Response:
        device = self.get_object()
        if device.status == Device.Status.STOPPED:
            return _err("Device is already stopped.")
        from simulator.process_manager import process_manager
        try:
            process_manager.stop_device(device)
        except Exception as exc:
            return _err(str(exc), status.HTTP_500_INTERNAL_SERVER_ERROR)
        device.refresh_from_db()
        return _ok(DeviceSerializer(device).data)

    @action(detail=True, methods=["get"])
    def status(self, request: Request, pk: str | None = None) -> Response:
        device = self.get_object()
        from simulator.process_manager import process_manager
        process_manager.health_check(device)
        device.refresh_from_db()
        return _ok({"status": device.status, "pid": device.pid})

    @action(detail=True, methods=["get"])
    def logs(self, request: Request, pk: str | None = None) -> Response:
        device = self.get_object()
        try:
            n = int(request.query_params.get("lines", 100))
        except ValueError:
            return _err("'lines' must be an integer.")
        from simulator.process_manager import process_manager
        lines = process_manager.read_logs(str(device.id), lines=n)
        return _ok(lines)

    # ------------------------------------------------------------------
    # Bulk actions (detail=False — operate on multiple devices at once)
    # ------------------------------------------------------------------

    @action(detail=False, methods=["post"])
    def bulk_start(self, request: Request) -> Response:
        ids: list[str] = request.data.get("ids", [])
        if not ids:
            return _err("Provide at least one device id in 'ids'.")
        from simulator.process_manager import process_manager
        started: list[str] = []
        errors: list[str] = []
        for device_id in ids:
            try:
                device = Device.objects.get(pk=device_id)
            except Device.DoesNotExist:
                errors.append(f"{device_id}: not found")
                continue
            if device.status in (Device.Status.RUNNING, Device.Status.STARTING):
                errors.append(f"{device.name}: already {device.status}")
                continue
            try:
                process_manager.start_device(device)
                started.append(str(device.id))
            except Exception as exc:
                errors.append(f"{device.name}: {exc}")
        return _ok({"started": started, "errors": errors})

    @action(detail=False, methods=["post"])
    def bulk_stop(self, request: Request) -> Response:
        ids: list[str] = request.data.get("ids", [])
        if not ids:
            return _err("Provide at least one device id in 'ids'.")
        from simulator.process_manager import process_manager
        stopped: list[str] = []
        errors: list[str] = []
        for device_id in ids:
            try:
                device = Device.objects.get(pk=device_id)
            except Device.DoesNotExist:
                errors.append(f"{device_id}: not found")
                continue
            if device.status == Device.Status.STOPPED:
                errors.append(f"{device.name}: already stopped")
                continue
            try:
                process_manager.stop_device(device)
                stopped.append(str(device.id))
            except Exception as exc:
                errors.append(f"{device.name}: {exc}")
        return _ok({"stopped": stopped, "errors": errors})


# ------------------------------------------------------------------
# Custom 404 / 500 handlers — registered in core/urls.py
# ------------------------------------------------------------------

def handler404(request: Request, exception: object = None) -> Response:
    from django.http import JsonResponse
    return JsonResponse({"data": None, "error": "Not found."}, status=404)


def handler500(request: Request) -> Response:
    from django.http import JsonResponse
    return JsonResponse({"data": None, "error": "Internal server error."}, status=500)


@api_view(["GET"])
def available_ports(request: Request) -> Response:
    protocol = request.query_params.get("protocol")
    if protocol not in [Device.Protocol.MODBUS, Device.Protocol.ETHERNETIP]:
        return _err("Query param 'protocol' must be 'modbus' or 'ethernetip'.")
    try:
        port = peek_next_port(protocol)
        return _ok({"protocol": protocol, "port": port})
    except ValueError as exc:
        return _err(str(exc), status.HTTP_409_CONFLICT)
