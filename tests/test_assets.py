"""The ``assets`` resource — a publication's image library.

The wire format is base64 in JSON (chosen over multipart so every SDK has one
code path), and the point of ``upload`` is that a caller hands it raw bytes and
never encodes by hand. If that regressed, uploads would silently carry the repr
of a bytes object instead of an image.
"""

import base64
import json
import unittest

from mailtea import Mailtea
from mailtea._transport import HttpResponse


PUB = "pub_123"
PNG = b"\x89PNG"


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


class AssetsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_upload_base64_encodes_raw_bytes(self):
        client, t = self._client(
            [{"json": {"object": "asset", "id": "asset_1", "url": "https://cdn.test/a.png"}}]
        )
        asset = client.assets.upload(
            publication_id=PUB, content=PNG, content_type="image/png", filename="hero.png"
        )
        self.assertEqual(asset["url"], "https://cdn.test/a.png")
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/assets")
        body = json.loads(call["body"])
        self.assertEqual(body["content"], base64.b64encode(PNG).decode())
        self.assertEqual(body["filename"], "hero.png")

    def test_upload_passes_an_already_encoded_string_through(self):
        client, t = self._client([{"json": {"object": "asset", "id": "asset_2"}}])
        encoded = base64.b64encode(PNG).decode()
        client.assets.upload(publication_id=PUB, content=encoded, content_type="image/png")
        self.assertEqual(json.loads(t.calls[0]["body"])["content"], encoded)

    def test_list_sends_filters_as_query_params(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.assets.list(publication_id=PUB, search="hero", limit=10)
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertIn("/v1/assets?", call["url"])
        self.assertIn("publication_id=" + PUB, call["url"])
        self.assertIn("search=hero", call["url"])

    def test_delete_targets_the_id_and_keeps_publication_id(self):
        client, t = self._client([{"json": {"object": "asset", "id": "asset_1", "deleted": True}}])
        res = client.assets.delete("asset_1", publication_id=PUB)
        self.assertTrue(res["deleted"])
        call = t.calls[0]
        self.assertEqual(call["method"], "DELETE")
        self.assertIn("/v1/assets/asset_1?", call["url"])


if __name__ == "__main__":
    unittest.main()
