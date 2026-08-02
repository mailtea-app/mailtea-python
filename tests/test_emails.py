import json
import os
import unittest

from mailtea import Mailtea, MailteaError
from mailtea._transport import HttpResponse


def fake_transport(responses):
    """Build an injectable transport that returns canned responses and records calls."""
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


class EmailsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_send_posts_payload(self):
        client, t = self._client([{"json": {"id": "email_1"}}])
        result = client.emails.send(
            {"from": "a@b.com", "to": "r@x.com", "subject": "Hi", "html": "<p>hi</p>"}
        )
        self.assertEqual(result, {"id": "email_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/emails")
        self.assertEqual(call["headers"]["Authorization"], "Bearer mt_pat_test")
        self.assertEqual(
            json.loads(call["body"]),
            {"from": "a@b.com", "to": "r@x.com", "subject": "Hi", "html": "<p>hi</p>"},
        )

    def test_batch_sends_bare_array(self):
        client, t = self._client([{"json": {"data": [{"id": "e1"}, {"id": "e2"}]}}])
        client.emails.batch(
            [
                {"from": "a@b.com", "to": "x@a.com", "subject": "1", "html": "<p>1</p>"},
                {"from": "a@b.com", "to": "y@a.com", "subject": "2", "html": "<p>2</p>"},
            ]
        )
        body = json.loads(t.calls[0]["body"])
        self.assertIsInstance(body, list)
        self.assertEqual(len(body), 2)
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/emails/batch")

    def test_get_aliases_last_event_to_status(self):
        client, t = self._client([{"json": {"id": "e1", "last_event": "delivered"}}])
        email = client.emails.get("e1")
        self.assertEqual(email["status"], "delivered")
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/emails/e1")
        self.assertEqual(t.calls[0]["method"], "GET")

    def test_list_builds_query_and_drops_none(self):
        client, t = self._client([{"json": {"object": "list", "data": [], "total": 0}}])
        client.emails.list({"status": "sent", "limit": 10, "search": "invoice", "offset": None})
        url = t.calls[0]["url"]
        self.assertIn("/v1/emails?", url)
        self.assertIn("status=sent", url)
        self.assertIn("limit=10", url)
        self.assertIn("search=invoice", url)
        self.assertNotIn("offset", url)

    def test_reschedule_patches_scheduled_at(self):
        client, t = self._client([{"json": {"object": "email", "id": "e1"}}])
        client.emails.reschedule("e1", "2030-06-01T12:00:00.000Z")
        self.assertEqual(t.calls[0]["method"], "PATCH")
        self.assertEqual(json.loads(t.calls[0]["body"]), {"scheduled_at": "2030-06-01T12:00:00.000Z"})

    def test_cancel_posts_to_cancel(self):
        client, t = self._client([{"json": {"object": "email", "id": "e1"}}])
        client.emails.cancel("e1")
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/emails/e1/cancel")
        self.assertEqual(t.calls[0]["method"], "POST")

    def test_api_error_maps_to_mailtea_error(self):
        client, _ = self._client([{"status": 401, "json": {"error": "Unauthorized"}}])
        with self.assertRaises(MailteaError) as ctx:
            client.emails.get("e1")
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(ctx.exception.message, "Unauthorized")
        self.assertEqual(ctx.exception.request_id, "req_1")
        self.assertIsNone(ctx.exception.code)

    def test_api_error_code_is_surfaced(self):
        client, _ = self._client(
            [
                {
                    "status": 402,
                    "json": {
                        "error": "Your plan covers transactional email only.",
                        "code": "marketing_plan_required",
                    },
                }
            ]
        )
        with self.assertRaises(MailteaError) as ctx:
            client.emails.get("e1")
        self.assertEqual(ctx.exception.status, 402)
        # Branching on the code has to survive a copy change to the message.
        self.assertEqual(ctx.exception.code, "marketing_plan_required")

    def test_missing_api_key_raises(self):
        saved = os.environ.pop("MAILTEA_API_KEY", None)
        try:
            with self.assertRaises(MailteaError) as ctx:
                Mailtea()
            self.assertEqual(ctx.exception.code, "missing_api_key")
        finally:
            if saved is not None:
                os.environ["MAILTEA_API_KEY"] = saved


if __name__ == "__main__":
    unittest.main()
