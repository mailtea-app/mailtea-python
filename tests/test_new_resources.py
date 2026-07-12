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


class NewResourcesTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    # --- domains ---
    def test_domains_create_posts_body(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1"}}])
        client.domains.create({"publication_id": "pub_1", "name": "mail.acme.com", "purpose": "email"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/domains")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "mail.acme.com", "purpose": "email"},
        )

    def test_domains_verify_posts_with_publication_id_and_no_body(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1", "status": "verified"}}])
        client.domains.verify("dom_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/domains/dom_1/verify?publication_id=pub_1"
        )
        self.assertIsNone(call["body"])

    def test_domains_delete(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_1", "deleted": True}}])
        client.domains.delete("dom_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/domains/dom_1?publication_id=pub_1"
        )

    def test_domains_tracking_create(self):
        client, t = self._client([{"json": {"object": "tracking_domain", "id": "trk_1"}}])
        client.domains.tracking.create("dom_1", {"publication_id": "pub_1", "subdomain": "links"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/domains/dom_1/tracking-domains?publication_id=pub_1",
        )
        # publication_id in the query; only subdomain in the body
        self.assertEqual(json.loads(call["body"]), {"subdomain": "links"})

    def test_domains_tracking_verify_and_delete_nested_paths(self):
        client, t = self._client([{"json": {"object": "tracking_domain", "id": "trk_1", "status": "verified"}}])
        client.domains.tracking.verify("dom_1", "trk_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "POST")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/dom_1/tracking-domains/trk_1/verify?publication_id=pub_1",
        )

        client2, t2 = self._client([{"json": {"object": "tracking_domain", "id": "trk_1", "deleted": True}}])
        client2.domains.tracking.delete("dom_1", "trk_1", {"publication_id": "pub_1"})
        self.assertEqual(t2.calls[0]["method"], "DELETE")
        self.assertEqual(
            t2.calls[0]["url"],
            "https://api.mailtea.app/v1/domains/dom_1/tracking-domains/trk_1?publication_id=pub_1",
        )

    # --- webhooks (mounted at /v1/webhooks/endpoints) ---
    def test_webhooks_create_targets_endpoints_path(self):
        client, t = self._client([{"json": {"object": "webhook", "id": "whk_1", "signing_secret": "s"}}])
        client.webhooks.create(
            {"publication_id": "pub_1", "endpoint": "https://x.test/h", "events": ["email.delivered"]}
        )
        call = t.calls[0]
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/webhooks/endpoints")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "endpoint": "https://x.test/h", "events": ["email.delivered"]},
        )

    def test_webhooks_update_targets_endpoints_id(self):
        client, t = self._client([{"json": {"object": "webhook", "id": "whk_1"}}])
        client.webhooks.update("whk_1", {"publication_id": "pub_1", "status": "disabled"})
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/webhooks/endpoints/whk_1?publication_id=pub_1",
        )

    # --- contact properties (team-scoped, no publication_id) ---
    def test_contact_properties_create_no_publication_id(self):
        client, t = self._client([{"json": {"object": "contact_property", "id": "cprop_1"}}])
        client.contact_properties.create({"key": "plan", "type": "string", "fallback_value": "free"})
        call = t.calls[0]
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/contact-properties")
        self.assertEqual(
            json.loads(call["body"]), {"key": "plan", "type": "string", "fallback_value": "free"}
        )

    def test_contact_properties_list_and_delete(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.contact_properties.list()
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/contact-properties")

        client2, t2 = self._client([{"json": {"object": "contact_property", "id": "cprop_1", "deleted": True}}])
        client2.contact_properties.delete("cprop_1")
        self.assertEqual(t2.calls[0]["method"], "DELETE")
        self.assertEqual(t2.calls[0]["url"], "https://api.mailtea.app/v1/contact-properties/cprop_1")

    # --- api keys ---
    def test_api_keys_create_returns_token(self):
        client, t = self._client([{"json": {"id": "tok_1", "token": "mt_pat_secret"}}])
        result = client.api_keys.create({"name": "CI", "permission": "sending_access"})
        self.assertEqual(result["token"], "mt_pat_secret")
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/api-keys")
        self.assertEqual(json.loads(t.calls[0]["body"]), {"name": "CI", "permission": "sending_access"})

    def test_api_keys_revoke_tolerates_empty_body(self):
        # DELETE /v1/api-keys/:id returns 200 with an empty body.
        client, t = self._client([{"status": 200, "raw": ""}])
        result = client.api_keys.revoke("tok_1")
        self.assertIsNone(result)
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/api-keys/tok_1")


if __name__ == "__main__":
    unittest.main()
