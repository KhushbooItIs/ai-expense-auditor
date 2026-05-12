from django.urls import path
from audits import views

urlpatterns = [
    path("", views.index, name="index"),
    path("audit/", views.run_audit, name="run_audit"),
    path("r/<str:slug>/", views.audit_result, name="audit_result"),
    path("a/<str:slug>/", views.audit_share, name="audit_share"),
    path("healthz/", views.healthz, name="healthz"),
]
