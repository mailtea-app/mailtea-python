"""Mailtea Python SDK — send, schedule, and manage email from your app or AI agent."""

from .client import Mailtea
from .errors import MailteaError
from .webhook_signing import sign_webhook, verify_webhook_signature

__all__ = ["Mailtea", "MailteaError", "verify_webhook_signature", "sign_webhook"]
__version__ = "0.6.0"
