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


class SegmentsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_create_posts_body(self):
        client, t = self._client([{"json": {"object": "segment", "id": "seg_1"}}])
        client.segments.create({"publication_id": "pub_1", "name": "VIPs", "status_filter": "active"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/segments")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "VIPs", "status_filter": "active"},
        )

    def test_list_builds_query(self):
        client, t = self._client([{"json": {"object": "list", "data": [], "has_more": False}}])
        client.segments.list({"publication_id": "pub_1", "limit": 10})
        url = t.calls[0]["url"]
        self.assertIn("/v1/segments?", url)
        self.assertIn("publication_id=pub_1", url)
        self.assertIn("limit=10", url)

    def test_get_url_encodes_id(self):
        client, t = self._client([{"json": {"object": "segment", "id": "seg/1"}}])
        client.segments.get("seg/1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/segments/seg%2F1?publication_id=pub_1"
        )

    def test_update_puts_publication_id_in_query_and_forwards_null_to_clear(self):
        client, t = self._client([{"json": {"object": "segment", "id": "seg_1"}}])
        client.segments.update("seg_1", {"publication_id": "pub_1", "status_filter": None})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/segments/seg_1?publication_id=pub_1"
        )
        # null is forwarded in the body to clear the nullable filter
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "status_filter": None},
        )

    def test_create_sends_inactive_days(self):
        client, t = self._client([{"json": {"object": "segment", "id": "seg_1", "inactive_days": 90}}])
        result = client.segments.create(publication_id="pub_1", name="Silent 90", inactive_days=90)
        self.assertEqual(
            json.loads(t.calls[0]["body"]),
            {"publication_id": "pub_1", "name": "Silent 90", "inactive_days": 90},
        )
        self.assertEqual(result["inactive_days"], 90)

    def test_update_sets_inactive_days_and_none_clears_it(self):
        client, t = self._client(
            [{"json": {"object": "segment", "id": "seg_1"}}, {"json": {"object": "segment", "id": "seg_1"}}]
        )
        client.segments.update("seg_1", publication_id="pub_1", inactive_days=30)
        client.segments.update("seg_1", {"publication_id": "pub_1", "inactive_days": None})
        self.assertEqual(
            json.loads(t.calls[0]["body"]), {"publication_id": "pub_1", "inactive_days": 30}
        )
        self.assertEqual(
            json.loads(t.calls[1]["body"]), {"publication_id": "pub_1", "inactive_days": None}
        )

    def test_docstring_names_inactive_days(self):
        from mailtea.segments import Segments

        doc = Segments.__doc__ or ""
        self.assertIn("inactive_days", doc)
        self.assertIn("never engaged", doc)
        self.assertIn("not backfilled", doc)
        self.assertNotIn("migration", doc)

    def test_delete_docstring_says_a_segment_in_use_is_refused(self):
        from mailtea.segments import Segments

        doc = Segments.delete.__doc__ or ""
        self.assertIn("segment_in_use", doc)
        self.assertIn("409", doc)

    def test_delete(self):
        client, t = self._client([{"json": {"object": "segment", "id": "seg_1", "deleted": True}}])
        client.segments.delete("seg_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/segments/seg_1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
