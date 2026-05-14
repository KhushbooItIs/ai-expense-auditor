"""
Referral feature tests — uses Django test DB.
Run: pytest audits/tests/test_referrals.py
"""
import pytest
from audits.models import Audit


@pytest.mark.django_db
def test_referrer_slug_stored_on_audit():
    """An audit created with a referrer slug should keep that attribution."""
    referrer = Audit.objects.create(
        input_json={"team_size": 1, "use_case": "mixed", "tools": []},
        result_json={"monthly_savings": 50, "annual_savings": 600},
    )
    referred = Audit.objects.create(
        input_json={"team_size": 1, "use_case": "mixed", "tools": []},
        result_json={"monthly_savings": 30, "annual_savings": 360},
        referred_by_slug=referrer.slug,
    )
    assert referred.referred_by_slug == referrer.slug


@pytest.mark.django_db
def test_referral_count_aggregates_correctly():
    """Counting Audits with a given referred_by_slug returns the referral count."""
    referrer = Audit.objects.create(
        input_json={"team_size": 1, "use_case": "mixed", "tools": []},
        result_json={"monthly_savings": 0, "annual_savings": 0},
    )
    for savings in (100, 200, 50):
        Audit.objects.create(
            input_json={"team_size": 1, "use_case": "mixed", "tools": []},
            result_json={"monthly_savings": savings, "annual_savings": savings * 12},
            referred_by_slug=referrer.slug,
        )

    referrals = Audit.objects.filter(referred_by_slug=referrer.slug)
    assert referrals.count() == 3
    total = sum(a.result_json["monthly_savings"] for a in referrals)
    assert total == 350


@pytest.mark.django_db
def test_audit_without_referrer_has_blank_slug():
    """Default empty string when no referral attribution provided."""
    audit = Audit.objects.create(
        input_json={"team_size": 1, "use_case": "mixed", "tools": []},
        result_json={"monthly_savings": 0, "annual_savings": 0},
    )
    assert audit.referred_by_slug == ""
