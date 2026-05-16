from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DeviceViewSet, available_ports

router = DefaultRouter()
router.register(r"devices", DeviceViewSet, basename="device")

urlpatterns = [
    path("", include(router.urls)),
    path("ports/available/", available_ports, name="available-ports"),
]
