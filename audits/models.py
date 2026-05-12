import secrets
from django.db import models


def _generate_slug():
    # 8 bytes → 11 URL-safe base64 chars. Collision probability negligible at our scale.
    return secrets.token_urlsafe(8)


class Audit(models.Model):
    """
    Immutable snapshot of one audit run.
    Separating snapshot (this model) from PII (Lead) means the share URL
    (/a/<slug>/) can query Audit only and structurally cannot leak email/company.
    """

    slug = models.CharField(max_length=16, unique=True, db_index=True, default=_generate_slug)

    # Raw form input — stored so we can re-display the form pre-filled if needed
    input_json = models.JSONField()

    # Engine output — findings, totals, route. Source of truth for the result page.
    result_json = models.JSONField()

    # AI-generated or templated summary paragraph
    summary_text = models.TextField(default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Audit {self.slug} ({self.created_at:%Y-%m-%d})"

    @property
    def monthly_savings(self) -> float:
        return self.result_json.get("monthly_savings", 0)

    @property
    def annual_savings(self) -> float:
        return self.result_json.get("annual_savings", 0)

    @property
    def route(self) -> str:
        return self.result_json.get("route", "normal")
