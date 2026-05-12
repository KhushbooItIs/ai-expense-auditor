from django.db import models


USE_CASE_CHOICES = [
    ("coding", "Coding"),
    ("writing", "Writing"),
    ("data", "Data / Analysis"),
    ("research", "Research"),
    ("mixed", "Mixed"),
]


class VendorPlan(models.Model):
    """
    One row per billable plan (e.g. Cursor / Business).
    price_monthly XOR price_per_seat — exactly one must be set.
    """

    vendor_key = models.CharField(max_length=50)    # "cursor"
    vendor_name = models.CharField(max_length=100)  # "Cursor"
    plan_key = models.CharField(max_length=50)      # "business"
    plan_name = models.CharField(max_length=100)    # "Business"

    # Pricing — use price_monthly for flat plans, price_per_seat for per-seat plans
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_per_seat = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    min_seats = models.IntegerField(default=1)
    max_seats = models.IntegerField(null=True, blank=True)  # null = unlimited

    # Features the plan includes (used to validate if a downgrade is safe)
    features = models.JSONField(default=list)  # e.g. ["sso", "admin", "privacy"]

    # Credex can source discounted licenses for these vendors/plans
    credex_eligible = models.BooleanField(default=False)

    # Audit trail for pricing freshness
    source_url = models.URLField()
    last_verified = models.DateField()

    class Meta:
        unique_together = [("vendor_key", "plan_key")]
        ordering = ["vendor_key", "plan_key"]

    def __str__(self):
        return f"{self.vendor_name} / {self.plan_name}"

    def monthly_cost(self, seats: int) -> float:
        """Compute total monthly cost for a given seat count."""
        if self.price_per_seat is not None:
            effective_seats = max(seats, self.min_seats)
            return float(self.price_per_seat * effective_seats)
        if self.price_monthly is not None:
            return float(self.price_monthly)
        return 0.0


class ToolFitScore(models.Model):
    """
    Editorial score (1-5) for how well a vendor/plan serves a given use case.
    Drives alternative recommendations: we only suggest a switch if the
    alternative's score is within 1 point of the current tool's score.
    """

    vendor_key = models.CharField(max_length=50)
    plan_key = models.CharField(max_length=50)
    use_case = models.CharField(max_length=20, choices=USE_CASE_CHOICES)
    score = models.IntegerField()       # 1 (poor fit) to 5 (perfect fit)
    reasoning = models.TextField(blank=True)  # shown in the "evidence" block on the result page

    class Meta:
        unique_together = [("vendor_key", "plan_key", "use_case")]
        ordering = ["use_case", "-score"]

    def __str__(self):
        return f"{self.vendor_key}.{self.plan_key} / {self.use_case} = {self.score}"
