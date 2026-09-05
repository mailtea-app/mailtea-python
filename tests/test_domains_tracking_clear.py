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


class DomainsTrackingClearTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_update_sends_an_explicit_null_to_clear(self):
        # The removal has to reach the wire AS null. The query helper drops
        # None values; the body helper must not, or "remove it" would become
        # "leave it alone" and the caller would get a 200 saying nothing
        # happened.
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.update("dom_1", publication_id="pub_1", tracking_subdomain=None)
        body = json.loads(t.calls[0]["body"])
        self.assertIn("tracking_subdomain", body)
        self.assertIsNone(body["tracking_subdomain"])

    def test_update_still_sends_a_named_subdomain(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.update("dom_1", publication_id="pub_1", tracking_subdomain="links")
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {"publication_id": "pub_1", "tracking_subdomain": "links"},
        )

    def test_omitting_the_field_sends_no_key(self):
        # Three states, not two: absent leaves the subdomain alone, null
        # removes it. A body that always carried the key would clear it on
        # every unrelated update.
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.update("dom_1", publication_id="pub_1", tls="enforced")
        self.assertNotIn("tracking_subdomain", json.loads(t.calls[0]["body"]))

    def test_the_publication_still_reaches_the_query(self):
        # The clear must not disturb the scoping the PATCH is routed by.
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.update("dom_1", publication_id="pub_1", tracking_subdomain=None)
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/dom_1?publication_id=pub_1",
        )


if __name__ == "__main__":
    unittest.main()
