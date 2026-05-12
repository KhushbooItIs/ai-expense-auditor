from django.db import models
from audits.models import Audit


class Lead(models.Model):
    """
    PII collected after value is shown (email gate on the result page).
    OneToOne with Audit — one lead per audit, captured separately.

    Never queried by the share view (/a/<slug>/). PII is isolated by
    architecture, not just by application logic.
    """

    audit = models.OneToOneField(Audit, on_delete=models.CASCADE, related_name="lead")
    email = models.EmailField()
    company = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=100, blank=True)
    team_size = models.IntegerField(null=True, blank=True)
    consent_credex_outreach = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.audit.slug})"
