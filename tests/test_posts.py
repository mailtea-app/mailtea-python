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


class PostsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_send_test_posts_to_test_endpoint(self):
        client, t = self._client(
            [{"json": {"object": "test_send", "id": "iss_1", "sent_to": ["you@x.com"]}}]
        )
        result = client.posts.send_test(
            "iss_1", {"recipients": ["you@x.com"], "from": "Acme <a@b.com>"}
        )
        self.assertEqual(result["sent_to"], ["you@x.com"])
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/posts/iss_1/test")
        self.assertEqual(
            json.loads(call["body"]),
            {"recipients": ["you@x.com"], "from": "Acme <a@b.com>"},
        )

    def test_send_test_url_encodes_id(self):
        client, t = self._client([{"json": {"object": "test_send", "id": "iss/1"}}])
        client.posts.send_test("iss/1", {"recipients": ["you@x.com"], "from": "a@b.com"})
        self.assertEqual(t.calls[0]["url"], "https://api.mailtea.app/v1/posts/iss%2F1/test")

    def test_list_passes_query_filters(self):
        client, t = self._client([{"json": {"data": [], "total": 0}}])
        client.posts.list(publication_id="pub_1", limit=10, offset=20, status="draft", kind="newsletter")
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/posts"
            "?publication_id=pub_1&limit=10&offset=20&status=draft&kind=newsletter",
        )

    def test_get_retrieves_post(self):
        client, t = self._client([{"json": {"object": "post", "id": "iss_1"}}])
        client.posts.get("iss_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/posts/iss_1?publication_id=pub_1"
        )

    def test_update_patches_draft_body(self):
        client, t = self._client([{"json": {"object": "post", "id": "iss_1"}}])
        client.posts.update("iss_1", {"subject": "New subject", "html": "<p>Hi</p>"})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/posts/iss_1")
        self.assertEqual(
            json.loads(call["body"]), {"subject": "New subject", "html": "<p>Hi</p>"}
        )

    def test_delete_removes_draft(self):
        client, t = self._client([{"json": {"object": "post", "id": "iss_1", "deleted": True}}])
        client.posts.delete("iss_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "DELETE")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/posts/iss_1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
