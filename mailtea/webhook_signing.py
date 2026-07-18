"""Standard Webhooks (standardwebhooks.com) signature verification.

A stdlib-only mirror of the Mailtea signer — ``packages/contracts/src/webhook-signing.ts``
(also copied into the Node SDK and the webhook-ingester). Kept in exact parity
so a signature produced by the platform verifies here byte-for-byte.

The stored signing secret is ``whsec_<base64>``; the HMAC key is the base64
remainder decoded to bytes. The signed content is ``{msg_id}.{timestamp}.{payload}``
where ``timestamp`` is Unix SECONDS, matching the ``webhook-timestamp`` header.
The ``webhook-signature`` header is ``v1,<base64 HMAC-SHA256>``; during key
rotation it may carry several space-delimited ``v1,<sig>`` tokens and a match
against any one of them passes.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import math
import time
from typing import Optional, Union

_SECRET_PREFIX = "whsec_"
_SIGNATURE_VERSION = "v1"
_DEFAULT_TOLERANCE_SECONDS = 300


def _decode_signing_key(secret: str) -> bytes:
    """Decode the HMAC key from a ``whsec_``-prefixed secret.

    Matches Node's lenient base64 decoder: accepts the base64url alphabet and
    tolerates missing padding, so a secret minted with either alphabet decodes
    to the same bytes.
    """
    raw = secret[len(_SECRET_PREFIX):] if secret.startswith(_SECRET_PREFIX) else secret
    raw = raw.strip().replace("-", "+").replace("_", "/")
    raw += "=" * ((-len(raw)) % 4)
    return base64.b64decode(raw)


def _compute_signature(secret: str, msg_id: str, timestamp: int, payload: str) -> str:
    signed_content = "{0}.{1}.{2}".format(msg_id, int(timestamp), payload)
    key = _decode_signing_key(secret)
    digest = hmac.new(key, signed_content.encode("utf-8"), hashlib.sha256).digest()
    return base64.b64encode(digest).decode("ascii")


def sign_webhook(
    secret: str,
    msg_id: str,
    timestamp: Union[int, float],
    payload: str,
) -> str:
    """Sign a webhook payload.

    Returns the ``webhook-signature`` header value in Standard Webhooks form,
    ``v1,<base64 HMAC-SHA256>``. Useful for faking Mailtea deliveries in tests.

    :param timestamp: Unix seconds — the same value sent in ``webhook-timestamp``.
    """
    return "{0},{1}".format(
        _SIGNATURE_VERSION,
        _compute_signature(secret, msg_id, math.floor(timestamp), payload),
    )


def verify_webhook_signature(
    secret: str,
    msg_id: str,
    timestamp: Union[int, float, str],
    payload: str,
    signature_header: str,
    tolerance_seconds: int = _DEFAULT_TOLERANCE_SECONDS,
    now: Optional[Union[int, float]] = None,
) -> bool:
    """Verify a ``webhook-signature`` header against the expected HMAC.

    The header may carry multiple space-delimited ``v1,<sig>`` tokens (Standard
    Webhooks allows key rotation — the platform may sign a delivery with both the
    old and new secret); a match against any ``v1`` token passes. Returns
    ``False`` when the timestamp is outside ``tolerance_seconds`` of ``now``
    (replay protection). Uses a constant-time comparison. Never raises on a bad
    signature — it returns ``False``.

    :param secret: the endpoint's signing secret (``whsec_...``).
    :param msg_id: the ``webhook-id`` header value.
    :param timestamp: the ``webhook-timestamp`` header value (Unix seconds; a
        string is accepted and coerced).
    :param payload: the raw request body, exactly as received.
    :param signature_header: the ``webhook-signature`` header value.
    :param tolerance_seconds: allowed clock skew each way. Default 5 minutes.
    :param now: injectable current time (Unix seconds) for tests.
    """
    try:
        timestamp_value = float(timestamp)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(timestamp_value):
        return False
    timestamp_seconds = math.floor(timestamp_value)

    now_seconds = math.floor(time.time()) if now is None else math.floor(now)
    if abs(now_seconds - timestamp_seconds) > tolerance_seconds:
        return False

    expected = _compute_signature(secret, msg_id, timestamp_seconds, payload)

    for token in signature_header.split(" "):
        if not token:
            continue
        comma_index = token.find(",")
        if comma_index == -1:
            continue
        version = token[:comma_index]
        signature = token[comma_index + 1:]
        if version == _SIGNATURE_VERSION and hmac.compare_digest(signature, expected):
            return True

    return False
