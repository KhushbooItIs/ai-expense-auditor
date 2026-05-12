from django.contrib import admin
from django.http import Http404
from django.urls import path, include


def _well_known(request, path=""):
    raise Http404


urlpatterns = [
    path("admin/", admin.site.urls),
    path(".well-known/<path:path>", _well_known),
    path("leads/", include("leads.urls")),
    path("", include("audits.urls")),
]
