from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["email", "company", "role", "consent_credex_outreach", "created_at"]
    list_filter = ["consent_credex_outreach", "created_at"]
    search_fields = ["email", "company"]
    readonly_fields = ["audit", "created_at"]
