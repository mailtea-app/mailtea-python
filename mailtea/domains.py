from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from urllib.parse import quote

from ._resource import body as _body, query as _query

RequestFn = Callable[..., Any]


class Domains:
    """The ``domains`` resource (email/site sending domains). Access via
    ``mailtea.domains``.

    Scoped to a publication — pass ``publication_id``. Register a domain, add the
    returned DNS ``records``, then :meth:`verify` it before sending from it.
    Every method accepts the payload as a wire-format dict, as keyword
    arguments, or both. Pass ``region`` (fixed at creation), ``tls`` and
    ``tracking_subdomain`` to :meth:`create`; :meth:`list` filters on ``region``
    and ``status``.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request
        #: Tracking sub-domains (CNAME) under a domain.
        self.tracking = TrackingDomains(request)
        #: Domain claims — take a domain back from another publication.
        self.claims = DomainClaims(request)

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Register a domain. The response ``records`` lists the DNS records to add."""
        return self._request("POST", "/v1/domains", _body(params, kwargs))

    def list(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request("GET", "/v1/domains" + _query(_body(params, kwargs)))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET", "/v1/domains/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )

    def verify(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Verify a domain via its DNS records; ``status`` becomes ``"verified"``."""
        return self._request(
            "POST",
            "/v1/domains/" + quote(str(id), safe="") + "/verify" + _query(_body(params, kwargs)),
        )

    def update(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        merged = _body(params, kwargs)
        return self._request(
            "PATCH",
            "/v1/domains/"
            + quote(str(id), safe="")
            + _query({"publication_id": merged.get("publication_id")}),
            merged,
        )

    def delete(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "DELETE", "/v1/domains/" + quote(str(id), safe="") + _query(_body(params, kwargs))
        )


class TrackingDomains:
    """Tracking sub-domains (CNAME) under a domain — used to serve open-pixel
    and click-tracking links from your own domain. Access via
    ``mailtea.domains.tracking``.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, domain_id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Add a tracking sub-domain. Takes ``publication_id`` and ``subdomain``.
        The response ``records`` lists the CNAME to add."""
        merged = _body(params, kwargs)
        return self._request(
            "POST",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains"
            + _query({"publication_id": merged.get("publication_id")}),
            {"subdomain": merged.get("subdomain")},
        )

    def list(self, domain_id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains"
            + _query(_body(params, kwargs)),
        )

    def verify(
        self,
        domain_id: str,
        tracking_domain_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self._request(
            "POST",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains/"
            + quote(str(tracking_domain_id), safe="")
            + "/verify"
            + _query(_body(params, kwargs)),
        )

    def delete(
        self,
        domain_id: str,
        tracking_domain_id: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return self._request(
            "DELETE",
            "/v1/domains/"
            + quote(str(domain_id), safe="")
            + "/tracking-domains/"
            + quote(str(tracking_domain_id), safe="")
            + _query(_body(params, kwargs)),
        )


class DomainClaims:
    """Domain claims. Access via ``mailtea.domains.claims``.

    Use this when adding a domain is refused with ``domain_held_elsewhere``:
    another publication holds the host. Open a claim, publish the TXT record it
    returns to prove you control the DNS, then :meth:`verify` it. On success the
    other publication's domain is released and a fresh one is created for you.
    """

    def __init__(self, request: RequestFn) -> None:
        self._request = request

    def create(self, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Open a claim. Takes ``publication_id``, ``name`` and an optional
        ``region``. The response ``records`` lists the TXT record to publish."""
        return self._request("POST", "/v1/domains/claim", _body(params, kwargs))

    def get(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Poll a claim. Requires ``publication_id``."""
        return self._request(
            "GET",
            "/v1/domains/claims/" + quote(str(id), safe="") + _query(_body(params, kwargs)),
        )

    def verify(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Check the TXT record and complete the claim if it is there.

        Safe to call repeatedly: a record that has not propagated yet leaves the
        claim pending with the same record, so nothing has to be republished. A
        completed claim answers with the fresh ``domain`` beside the claim.
        """
        return self._request(
            "POST",
            "/v1/domains/claims/"
            + quote(str(id), safe="")
            + "/verify"
            + _query(_body(params, kwargs)),
        )

    def cancel(self, id: str, params: Optional[Dict[str, Any]] = None, **kwargs: Any) -> Dict[str, Any]:
        """Withdraw a pending claim. Requires ``publication_id``."""
        return self._request(
            "DELETE",
            "/v1/domains/claims/" + quote(str(id), safe="") + _query(_body(params, kwargs)),
        )
