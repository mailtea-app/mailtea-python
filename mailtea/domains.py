from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote, urlencode

RequestFn = Callable[..., Any]


class Domains:
    """The ``domains`` resource (email/site sending domains). Access via
    ``mailtea.domains``.

    Scoped to a publication — pass ``publication_id``. Register a domain, add the
    returned DNS ``records``, then :meth:`verify` it before sending from it.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request
        #: Tracking sub-domains (CNAME) under a domain.
        self.tracking = TrackingDomains(request)

    def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Register a domain. The response ``records`` lists the DNS records to add."""
        return self._request("POST", "/v1/domains", params)

    def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("GET", "/v1/domains" + _query(params))

    def get(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/domains/" + quote(str(id), safe="") + _query(params)
        )

    def verify(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a domain via its DNS records; ``status`` becomes ``"verified"``."""
        return self._request(
            "POST", "/v1/domains/" + quote(str(id), safe="") + "/verify" + _query(params)
        )

    def update(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "PATCH",
            "/v1/domains/"
            + quote(str(id), safe="")
            + _query({"publication_id": params.get("publication_id")}),
            params,
        )

    def delete(self, id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/domains/" + quote(str(id), safe="") + _query(params)
        )


class TrackingDomains:
    """Tracking sub-domains (CNAME) under a domain — used to serve open-pixel
    and click-tracking links from your own domain. Access via
    ``mailtea.domains.tracking``.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, domain_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add a tracking sub-domain. ``params`` takes ``publication_id`` and
        ``subdomain``. The response ``records`` lists the CNAME to add."""
        return self._request(
            "POST",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains"
            + _query({"publication_id": params.get("publication_id")}),
            {"subdomain": params.get("subdomain")},
        )

    def list(self, domain_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains"
            + _query(params),
        )

    def verify(
        self, domain_id: str, tracking_domain_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains/"
            + quote(str(tracking_domain_id), safe="")
            + "/verify"
            + _query(params),
        )

    def delete(
        self, domain_id: str, tracking_domain_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains/"
            + quote(str(tracking_domain_id), safe="")
            + _query(params),
        )


def _query(params: Optional[Dict[str, Any]]) -> str:
    if not params:
        return ""
    clean = {key: value for key, value in params.items() if value is not None}
    return ("?" + urlencode(clean)) if clean else ""

