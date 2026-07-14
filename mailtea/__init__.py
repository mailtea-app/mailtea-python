"""Mailtea Python SDK — send, schedule, and manage email from your app or AI agent."""

from .client import Mailtea
from .errors import MailteaError

__all__ = ["Mailtea", "MailteaError"]
__version__ = "0.1.2"
