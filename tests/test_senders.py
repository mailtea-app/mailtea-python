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


class SendersTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_create_posts_body(self):
        client, t = self._client([{"json": {"object": "sender", "id": "snd_1"}}])
        client.senders.create(
            {"publication_id": "pub_1", "name": "Acme", "email": "hi@acme.com", "is_default": True}
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/senders")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "Acme", "email": "hi@acme.com", "is_default": True},
        )

    def test_list_passes_publication_id_limit_and_after_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.senders.list(publication_id="pub_1", limit=10, after="cur_1")
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/senders?publication_id=pub_1&limit=10&after=cur_1",
        )

    def test_get_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "sender", "id": "snd_1"}}])
        client.senders.get("snd_1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/senders/snd_1?publication_id=pub_1"
        )

    def test_update_sends_publication_id_in_body_not_query(self):
        # Senders update reads publication_id from the body (email is immutable).
        client, t = self._client([{"json": {"object": "sender", "id": "snd_1"}}])
        client.senders.update("snd_1", {"publication_id": "pub_1", "name": "Renamed"})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/senders/snd_1")
        self.assertEqual(
            json.loads(call["body"]), {"publication_id": "pub_1", "name": "Renamed"}
        )

    def test_delete_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "sender", "id": "snd_1", "deleted": True}}])
        client.senders.delete("snd_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/senders/snd_1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
