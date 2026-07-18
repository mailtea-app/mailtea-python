"""URL/body building for the inbound (received) email resource and
``emails.analytics``. Mirrors the Node SDK (``packages/sdk/src/inbound.ts``,
``emails.ts``): inbound is nested under ``emails`` (``mailtea.emails.inbound``)."""

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


class InboundTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_inbound_list_builds_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.emails.inbound.list(publication_id="pub_123", limit=20)
        url = t.calls[0]["url"]
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertIn("https://api.mailtea.app/v1/emails/inbound?", url)
        self.assertIn("publication_id=pub_123", url)
        self.assertIn("limit=20", url)

    def test_inbound_list_drops_none_cursor(self):
        client, t = self._client([{"json": {"data": []}}])
        client.emails.inbound.list(publication_id="pub_1", cursor=None)
        self.assertNotIn("cursor", t.calls[0]["url"])

    def test_inbound_get(self):
        client, t = self._client([{"json": {"object": "email", "id": "rxemail_1"}}])
        email = client.emails.inbound.get("rxemail_1")
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/emails/inbound/rxemail_1")
        self.assertEqual(email.id, "rxemail_1")

    def test_inbound_attachments_list(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.emails.inbound.attachments.list("rxemail_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/emails/inbound/rxemail_1/attachments",
        )

    def test_inbound_attachment_get(self):
        client, t = self._client([{"json": {"object": "attachment", "id": "rxatt_9"}}])
        client.emails.inbound.attachments.get("rxemail_1", "rxatt_9")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/emails/inbound/rxemail_1/attachments/rxatt_9",
        )

    def test_inbound_reply_posts_body(self):
        client, t = self._client([{"json": {"id": "txemail_2", "status": "queued"}}])
        result = client.emails.inbound.reply(
            "rxemail_1",
            html="<p>Thanks!</p>",
            idempotency_key="key_1",
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/emails/inbound/rxemail_1/reply")
        self.assertEqual(
            json.loads(call["body"]),
            {"html": "<p>Thanks!</p>", "idempotency_key": "key_1"},
        )
        self.assertEqual(result["id"], "txemail_2")

    def test_inbound_reply_dict_and_kwargs_merge(self):
        client, t = self._client([{"json": {"id": "txemail_3", "status": "queued"}}])
        client.emails.inbound.reply(
            "rxemail_1",
            {"from": {"email": "hi@acme.com", "name": "Acme"}},
            text="hello",
        )
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {"from": {"email": "hi@acme.com", "name": "Acme"}, "text": "hello"},
        )


class AnalyticsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_analytics_builds_query(self):
        client, t = self._client([{"json": {"object": "analytics", "total": 10}}])
        result = client.emails.analytics(
            from_date="2026-01-01T00:00:00Z", to_date="2026-02-01T00:00:00Z"
        )
        url = t.calls[0]["url"]
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertIn("https://api.mailtea.app/v1/emails/analytics?", url)
        self.assertIn("from_date=2026-01-01", url)
        self.assertIn("to_date=2026-02-01", url)
        self.assertEqual(result["total"], 10)

    def test_analytics_no_params(self):
        client, t = self._client([{"json": {"object": "analytics", "total": 0}}])
        client.emails.analytics()
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/emails/analytics")


if __name__ == "__main__":
    unittest.main()
