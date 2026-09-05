import json
import unittest

from mailtea import Mailtea
from mailtea._transport import HttpResponse


def fake_transport(responses):
    calls = []
    queue = list(responses)

    def transport(method, url, headers, body):
        calls.append({"method": method, "url": url, "headers": headers, "body": body})
        spec = queue.pop(0) if queue else {"status": 200, "json": {}}
        raw = spec.get("raw")
        text = raw if raw is not None else json.dumps(spec.get("json", {}))
        return HttpResponse(spec.get("status", 200), {"x-request-id": "req_1"}, text)

    transport.calls = calls
    return transport


class DomainClaimsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_create_posts_the_claim(self):
        client, t = self._client([{"json": {"object": "domain_claim", "id": "clm_1"}}])
        claim = client.domains.claims.create(
            publication_id="pub_1", name="acme.com", region="eu-west-1"
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/domains/claim")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "acme.com", "region": "eu-west-1"},
        )
        self.assertEqual(claim["id"], "clm_1")

    def test_get_scopes_by_publication(self):
        client, t = self._client([{"json": {"object": "domain_claim", "id": "clm_1"}}])
        client.domains.claims.get("clm_1", publication_id="pub_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/claims/clm_1?publication_id=pub_1",
        )
        self.assertEqual(t.calls[0]["method"], "GET")

    def test_verify_posts_the_verify_subpath(self):
        client, t = self._client([{"json": {"object": "domain_claim", "id": "clm_1"}}])
        client.domains.claims.verify("clm_1", publication_id="pub_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/claims/clm_1/verify?publication_id=pub_1",
        )
        self.assertEqual(t.calls[0]["method"], "POST")

    def test_verify_answers_with_the_claim_and_the_domain(self):
        # A completed claim answers with the fresh domain beside it, so the
        # caller can publish its DNS records without a second request.
        client, _ = self._client(
            [
                {
                    "json": {
                        "object": "domain_claim",
                        "id": "clm_1",
                        "status": "completed",
                        "domain_id": "dom_2",
                        "domain": {"object": "domain", "id": "dom_2", "records": []},
                    }
                }
            ]
        )
        result = client.domains.claims.verify("clm_1", publication_id="pub_1")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.domain.id, "dom_2")

    def test_cancel_deletes(self):
        client, t = self._client([{"json": {"object": "domain_claim", "deleted": True}}])
        client.domains.claims.cancel("clm_1", publication_id="pub_1")
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/claims/clm_1?publication_id=pub_1",
        )

    def test_claim_id_is_escaped(self):
        client, t = self._client([{"json": {"object": "domain_claim"}}])
        client.domains.claims.get("clm/1", publication_id="pub_1")
        self.assertIn("/claims/clm%2F1?", t.calls[0]["url"])

    def test_claim_records_are_readable(self):
        # The claim carries `records`, not a bare `txt` — a caller publishes
        # every record the list names.
        client, _ = self._client(
            [
                {
                    "json": {
                        "object": "domain_claim",
                        "id": "clm_1",
                        "status": "pending",
                        "expires_at": "2026-09-10T00:00:00.000Z",
                        "records": [
                            {
                                "record": "Claim",
                                "type": "TXT",
                                "name": "_mailtea-claim.acme.com",
                                "value": "mailtea-claim=abc123",
                            }
                        ],
                    }
                }
            ]
        )
        claim = client.domains.claims.create(publication_id="pub_1", name="acme.com")
        self.assertEqual(claim.records[0].record, "Claim")
        self.assertEqual(claim.records[0].type, "TXT")
        self.assertEqual(claim.expires_at, "2026-09-10T00:00:00.000Z")

    def test_create_forwards_the_new_domain_fields(self):
        # The resource is a pass-through, so region/tls/tracking_subdomain need
        # no code — this is the test that says so out loud, and that fails if
        # somebody ever adds a whitelist.
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.create(
            publication_id="pub_1",
            name="acme.com",
            region="ap-southeast-2",
            tls="enforced",
            tracking_subdomain="links",
        )
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {
                "publication_id": "pub_1",
                "name": "acme.com",
                "region": "ap-southeast-2",
                "tls": "enforced",
                "tracking_subdomain": "links",
            },
        )

    def test_update_forwards_the_new_domain_fields(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.update(
            "dom_1", publication_id="pub_1", tls="enforced", tracking_subdomain="links"
        )
        self.assertEqual(t.calls[0]["method"], "PATCH")
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {
                "publication_id": "pub_1",
                "tls": "enforced",
                "tracking_subdomain": "links",
            },
        )

    def test_list_forwards_the_filters(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.domains.list(publication_id="pub_1", region="eu-west-1", status="verified")
        self.assertIn("region=eu-west-1", t.calls[0]["url"])
        self.assertIn("status=verified", t.calls[0]["url"])


if __name__ == "__main__":
    unittest.main()
