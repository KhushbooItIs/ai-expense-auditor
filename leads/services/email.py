"""
Transactional email via Resend (prod) or Django console backend (dev).
Failure is caught by the caller and never surfaces to the user.
"""
import os
import logging

logger = logging.getLogger(__name__)


def send_audit_confirmation(lead, audit):
    api_key = os.environ.get("RESEND_API_KEY")
    if api_key:
        _send_via_resend(lead, audit, api_key)
    else:
        logger.info("RESEND_API_KEY not set — falling back to Django email backend")
        _send_via_django(lead, audit)


def _build_content(lead, audit):
    route = audit.result_json.get("route", "normal")
    monthly = audit.result_json.get("monthly_savings", 0)
    annual = audit.result_json.get("annual_savings", 0)

    base_url = os.environ.get("SITE_URL", "http://localhost:8000")
    share_url = f"{base_url}/a/{audit.slug}/"

    credex_note_html = ""
    credex_note_text = ""
    if route == "high_savings":
        credex_note_html = (
            f"<p>Based on your audit showing <strong>${monthly:.0f}/mo</strong> in potential savings, "
            f"a Credex specialist will be in touch to discuss how discounted AI credits "
            f"could capture even more of those savings.</p>"
        )
        credex_note_text = (
            f"\nYour audit shows ${monthly:.0f}/mo in potential savings. "
            f"A Credex specialist will reach out about discounted AI credits.\n"
        )

    subject = f"Your AI audit: ${monthly:.0f}/mo in potential savings"

    html = f"""
    <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; padding: 32px;">
      <h1 style="font-size: 24px; font-weight: 700;">Your OverpaidAI Audit</h1>
      <p>Here's a snapshot of what we found:</p>
      <div style="background: #f9fafb; border-radius: 8px; padding: 24px; margin: 16px 0;">
        <p style="font-size: 32px; font-weight: 800; margin: 0;">
          ${monthly:.0f}<span style="font-size: 16px; font-weight: 400;">/mo potential savings</span>
        </p>
        <p style="color: #6b7280; margin: 4px 0 0;">${annual:.0f}/year</p>
      </div>
      {credex_note_html}
      <p>View your full audit: <a href="{share_url}">{share_url}</a></p>
      <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
      <p style="color: #9ca3af; font-size: 12px;">OverpaidAI · Free AI spend audits · Powered by Credex</p>
    </div>
    """

    text = (
        f"Your OverpaidAI Audit\n\n"
        f"Potential savings: ${monthly:.0f}/mo (${annual:.0f}/year)\n"
        f"{credex_note_text}"
        f"View your audit: {share_url}\n"
    )

    return subject, html, text


def _send_via_resend(lead, audit, api_key):
    import resend
    resend.api_key = api_key
    subject, html, _ = _build_content(lead, audit)
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    try:
        resend.Emails.send({
            "from": from_email,
            "to": lead.email,
            "subject": subject,
            "html": html,
        })
    except Exception as e:
        logger.warning("Resend failed for %s: %s", lead.email, e)


def _send_via_django(lead, audit):
    from django.core.mail import send_mail
    subject, _, text = _build_content(lead, audit)
    from_email = os.environ.get("RESEND_FROM_EMAIL", "onboarding@resend.dev")
    try:
        send_mail(
            subject=subject,
            message=text,
            from_email=from_email,
            recipient_list=[lead.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.warning("Django email failed for %s: %s", lead.email, e)
