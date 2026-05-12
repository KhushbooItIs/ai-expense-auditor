from django.contrib import admin
from .models import VendorPlan, ToolFitScore


@admin.register(VendorPlan)
class VendorPlanAdmin(admin.ModelAdmin):
    list_display = ["vendor_name", "plan_name", "price_monthly", "price_per_seat",
                    "min_seats", "credex_eligible", "last_verified"]
    list_filter = ["vendor_key", "credex_eligible"]
    search_fields = ["vendor_name", "plan_name"]
    ordering = ["vendor_key", "plan_key"]


@admin.register(ToolFitScore)
class ToolFitScoreAdmin(admin.ModelAdmin):
    list_display = ["vendor_key", "plan_key", "use_case", "score"]
    list_filter = ["use_case", "vendor_key"]
    ordering = ["use_case", "vendor_key", "plan_key"]
