"""Locks the interface the public docs promise: keyword arguments with
``from_`` mapping, attribute access on responses, ``contacts.upsert``, and
``posts.create``/``posts.send``. Each test mirrors a real docs snippet."""

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
        return HttpResponse(
            spec.get("status", 200),
            {"x-request-id": "req_1"},
            json.dumps(spec.get("json", {})),
        )

    transport.calls = calls
    return transport


class DocsInterfaceTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    # --- emails.send: kwargs form with from_ (client-libraries.mdx) ---
    def test_emails_send_kwargs_maps_from_underscore(self):
        client, t = self._client([{"json": {"id": "txemail_1"}}])
        email = client.emails.send(
            from_="you@yourdomain.com",
            to="recipient@example.com",
            subject="Hello from Mailtea",
            html="<p>Your first email, sent via the API.</p>",
        )
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {
                "from": "you@yourdomain.com",
                "to": "recipient@example.com",
                "subject": "Hello from Mailtea",
                "html": "<p>Your first email, sent via the API.</p>",
            },
        )
        self.assertEqual(email.id, "txemail_1")  # attribute access
        self.assertEqual(email["id"], "txemail_1")  # dict access

    # --- emails.send: positional dict form still works (quickstart.mdx) ---
    def test_emails_send_dict_and_kwargs_merge(self):
        client, t = self._client([{"json": {"id": "txemail_1"}}])
        client.emails.send({"from": "a@b.co", "subject": "Hi"}, to="c@d.co")
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {"from": "a@b.co", "subject": "Hi", "to": "c@d.co"},
        )

    # --- emails.get: attribute access on status (bounces-and-suppressions.mdx) ---
    def test_emails_get_attribute_status(self):
        client, _ = self._client([{"json": {"id": "txemail_1", "last_event": "bounced"}}])
        email = client.emails.get("txemail_1")
        self.assertEqual(email.status, "bounced")
        self.assertEqual(email["status"], "bounced")

    def test_response_wraps_nested_values(self):
        client, _ = self._client(
            [{"json": {"data": [{"id": "c_1", "status": "active"}], "has_more": False}}]
        )
        page = client.contacts.list(publication_id="pub_1")
        self.assertEqual(page.data[0].status, "active")
        with self.assertRaises(AttributeError):
            page.missing_key

    # --- contacts.upsert (contacts.mdx) ---
    def test_contacts_upsert_kwargs(self):
        client, t = self._client([{"json": {"object": "contact", "id": "c_1"}}])
        client.contacts.upsert(
            publication_id="pub_123",
            email="ada@example.com",
            status="active",
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/contacts")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_123", "email": "ada@example.com", "status": "active"},
        )

    # --- contacts.list kwargs (contacts.mdx) ---
    def test_contacts_list_kwargs_build_query(self):
        client, t = self._client([{"json": {"data": []}}])
        client.contacts.list(publication_id="pub_123", limit=20, status="active")
        url = t.calls[0]["url"]
        self.assertIn("publication_id=pub_123", url)
        self.assertIn("limit=20", url)
        self.assertIn("status=active", url)

    # --- posts.create (campaigns.mdx) ---
    def test_posts_create_kwargs(self):
        client, t = self._client([{"json": {"id": "post_456"}}])
        post = client.posts.create(
            publication_id="pub_123",
            subject="This week in product",
            html="<h1>Hello readers</h1><p>Here is what shipped this week.</p>",
            send=False,
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/posts")
        self.assertEqual(json.loads(call["body"])["send"], False)
        self.assertEqual(post.id, "post_456")

    # --- posts.send, immediate and scheduled (campaigns.mdx) ---
    def test_posts_send_immediate_has_no_body(self):
        client, t = self._client([{"json": {"object": "post", "id": "post_456"}}])
        client.posts.send("post_456")
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/posts/post_456/send")
        self.assertIsNone(call["body"])

    def test_posts_send_scheduled(self):
        client, t = self._client([{"json": {"object": "post", "id": "post_456"}}])
        client.posts.send("post_456", scheduled_at="2026-06-01T15:00:00Z")
        self.assertEqual(
            json.loads(t.calls[0]["body"]), {"scheduled_at": "2026-06-01T15:00:00Z"}
        )

    # --- posts.send_test keeps the positional-dict form (client-libraries.mdx) ---
    def test_posts_send_test_dict_body(self):
        client, t = self._client([{"json": {"sent_to": ["you@example.com"], "failed_to": []}}])
        result = client.posts.send_test(
            "iss_abc123def456",
            {"recipients": ["you@example.com"], "from": "Acme <hello@acme.com>"},
        )
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/posts/iss_abc123def456/test"
        )
        self.assertEqual(result["sent_to"], ["you@example.com"])

    # --- domains.verify without publication_id (domains.mdx) ---
    def test_domains_verify_without_params(self):
        client, t = self._client([{"json": {"object": "domain", "id": "dom_456"}}])
        client.domains.verify("dom_456")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/domains/dom_456/verify"
        )

    # --- webhooks.create kwargs (tracking-analytics.mdx) ---
    def test_webhooks_create_kwargs(self):
        client, t = self._client([{"json": {"id": "wh_1", "signing_secret": "whsec_x"}}])
        client.webhooks.create(
            publication_id="pub_123",
            endpoint="https://example.com/webhooks/mailtea",
            events=["email.delivered", "email.opened"],
        )
        body = json.loads(t.calls[0]["body"])
        self.assertEqual(body["endpoint"], "https://example.com/webhooks/mailtea")
        self.assertEqual(body["events"], ["email.delivered", "email.opened"])

    # --- api_keys.create keeps the positional-dict form (api-keys.mdx) ---
    def test_api_keys_create_dict_body(self):
        client, t = self._client([{"json": {"id": "key_1", "token": "mt_pat_x"}}])
        result = client.api_keys.create(
            {"name": "Production sender", "permission": "sending_access"}
        )
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {"name": "Production sender", "permission": "sending_access"},
        )
        self.assertEqual(result["token"], "mt_pat_x")

    def test_responses_stay_json_serializable_dicts(self):
        client, _ = self._client([{"json": {"id": "txemail_1", "tags": [{"name": "env"}]}}])
        email = client.emails.get("txemail_1")
        self.assertIsInstance(email, dict)
        json.dumps(email)  # Resource must serialize like a plain dict


if __name__ == "__main__":
    unittest.main()
