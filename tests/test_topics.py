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


class TagsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_create_posts_body_with_required_default_subscription(self):
        client, t = self._client([{"json": {"object": "topic", "id": "tag_1"}}])
        client.topics.create(
            {"publication_id": "pub_1", "name": "Weekly", "default_subscription": "opt_in"}
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/topics")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "Weekly", "default_subscription": "opt_in"},
        )

    def test_list_builds_query(self):
        client, t = self._client([{"json": {"object": "list", "data": [], "has_more": False}}])
        client.topics.list({"publication_id": "pub_1"})
        url = t.calls[0]["url"]
        self.assertIn("/v1/topics?", url)
        self.assertIn("publication_id=pub_1", url)

    def test_get_url_encodes_id(self):
        client, t = self._client([{"json": {"object": "topic", "id": "topic/1"}}])
        client.topics.get("topic/1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/topics/topic%2F1?publication_id=pub_1"
        )

    def test_update_puts_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "topic", "id": "tag_1"}}])
        client.topics.update("tag_1", {"publication_id": "pub_1", "name": "Renamed"})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/topics/tag_1?publication_id=pub_1"
        )
        self.assertEqual(
            json.loads(call["body"]), {"publication_id": "pub_1", "name": "Renamed"}
        )

    def test_delete(self):
        client, t = self._client([{"json": {"object": "topic", "id": "tag_1", "deleted": True}}])
        client.topics.delete("tag_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/topics/tag_1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
