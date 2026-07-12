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


if __name__ == "__main__":
    unittest.main()
