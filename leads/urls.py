from django.urls import path
from leads import views

urlpatterns = [
    path("capture/", views.capture_lead, name="capture_lead"),
]
