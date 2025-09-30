import logging
from typing import Optional

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from ..core.config import settings

logger = logging.getLogger(__name__)


def build_verification_url(token: str) -> str:
    base = settings.frontend_base_url.rstrip("/")
    return f"{base}/verify-email?token={token}"


def send_verification_email(recipient: str, token: str, expires_at) -> bool:
    """Send an email with the verification link. Returns True if queued."""
    if not settings.sendgrid_api_key or not settings.sendgrid_from_email:
        logger.info(
            "SendGrid not configured; skipping verification email. token=%s recipient=%s",
            token,
            recipient,
        )
        return False

    verify_url = build_verification_url(token)
    subject = f"{settings.project_name} – Verify your email"
    support_line = (
        f"If you did not request this, contact {settings.support_email}"
        if settings.support_email
        else ""
    )

    html_content = f"""
        <p>Hello,</p>
        <p>Thanks for signing up with {settings.project_name}. Please verify your email address.</p>
        <p><a href=\"{verify_url}\">Click here to verify</a>. This link expires at {expires_at}.</p>
        <p>{support_line}</p>
    """

    plain_content = (
        f"Hello,\n\n"
        f"Thanks for signing up with {settings.project_name}. Please verify your email address.\n"
        f"Verification link: {verify_url}\n"
        f"This link expires at {expires_at}.\n"
        f"{support_line}\n"
    )

    message = Mail(
        from_email=settings.sendgrid_from_email,
        to_emails=recipient,
        subject=subject,
        html_content=html_content,
        plain_text_content=plain_content,
    )

    try:
        sg = SendGridAPIClient(settings.sendgrid_api_key)
        response = sg.send(message)
        logger.info(
            "Verification email queued for %s; status=%s",
            recipient,
            response.status_code,
        )
        return 200 <= response.status_code < 400
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("Failed to send verification email: %s", exc, exc_info=True)
        return False
