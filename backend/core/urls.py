from django.contrib import admin
from django.urls import include, path

from devices.views import handler404, handler500

handler404 = handler404  # noqa: F811 — re-assign for Django's URL resolver
handler500 = handler500  # noqa: F811

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("devices.urls")),
]
