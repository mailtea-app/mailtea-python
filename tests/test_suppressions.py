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


class SuppressionsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_list_is_org_scoped_with_filters(self):
        # No publication_id — suppressions are team-scoped.
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.suppressions.list(reason="bounce", q="acme.com", starting_after="cur_1", limit=50)
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/suppressions"
            "?reason=bounce&q=acme.com&starting_after=cur_1&limit=50",
        )

    def test_add_posts_emails_and_reason(self):
        client, t = self._client([{"json": {"added": 2}}])
        result = client.suppressions.add({"emails": ["a@x.com", "b@x.com"], "reason": "complaint"})
        self.assertEqual(result["added"], 2)
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/suppressions")
        self.assertEqual(
            json.loads(call["body"]), {"emails": ["a@x.com", "b@x.com"], "reason": "complaint"}
        )

    def test_remove_deletes_with_json_body(self):
        client, t = self._client([{"json": {"removed": 1}}])
        result = client.suppressions.remove({"emails": ["a@x.com"]})
        self.assertEqual(result["removed"], 1)
        call = t.calls[0]
        self.assertEqual(call["method"], "DELETE")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/suppressions")
        self.assertEqual(json.loads(call["body"]), {"emails": ["a@x.com"]})

    def test_export_returns_raw_csv_text(self):
        # text/csv body — the client hands it back as a raw string, not parsed JSON.
        csv = "email,reason,source,created_at\na@x.com,bounce,api,2026-01-01T00:00:00.000Z\n"
        client, t = self._client([{"raw": csv}])
        result = client.suppressions.export()
        self.assertEqual(result, csv)
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/suppressions/export")
        self.assertIsNone(call["body"])


if __name__ == "__main__":
    unittest.main()
