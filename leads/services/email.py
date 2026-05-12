"""
Transactional email via Resend.
Failure is caught by the caller and never surfaces to the user.
"""
import os
import logging

logger = logging.getLogger(__name__)


def send_audit_confirmation(lead, audit):
    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        logger.info("RESEND_API_KEY not set — skipping email for %s", lead.email)
        return

    import resend
    resend.api_key = api_key

    route = audit.result_json.get("route", "normal")
    monthly = audit.result_json.get("monthly_savings", 0)
    annual = audit.result_json.get("annual_savings", 0)

    if route == "high_savings":
        credex_note = (
            f"<p>Based on your audit showing <strong>${monthly:.0f}/mo</strong> in potential savings, "
            f"a Credex specialist will be in touch to discuss how discounted AI credits "
            f"could capture even more of those savings.</p>"
        )
    else:
        credex_note = ""

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 32px;">
      <h1 style="font-size: 24px; font-weight: 700;">Your OverpaidAI Audit</h1>
      <p>Here's a snapshot of what we found:</p>
      <div style="background: #f9fafb; border-radius: 8px; padding: 24px; margin: 16px 0;">
        <p style="font-size: 32px; font-weight: 800; margin: 0;">${monthly:.0f}<span style="font-size: 16px; font-weight: 400;">/mo potential savings</span></p>
        <p style="color: #6b7280; margin: 4px 0 0;">${annual:.0f}/year</p>
      </div>
      {credex_note}
      <p>View your full audit: <a href="https://overpaidai.onrender.com/a/{audit.slug}/">overpaidai.onrender.com/a/{audit.slug}/</a></p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
      <p style="color: #9ca3af; font-size: 12px;">OverpaidAI · Free AI spend audits · Powered by Credex</p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": "audit@overpaidai.com",
            "to": lead.email,
            "subject": f"Your AI audit: ${monthly:.0f}/mo in potential savings",
            "html": html,
        })
    except Exception as e:
        logger.warning("Resend failed for %s: %s", lead.email, e)
