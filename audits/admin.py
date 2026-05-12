from django.contrib import admin
from .models import Audit


@admin.register(Audit)
class AuditAdmin(admin.ModelAdmin):
    list_display = ["slug", "monthly_savings", "route", "created_at"]
    list_filter = ["created_at"]
    readonly_fields = ["slug", "input_json", "result_json", "summary_text", "created_at"]
    search_fields = ["slug"]
