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


class TemplatesTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_render_posts_spec_and_variables(self):
        client, t = self._client([{"json": {"html": "<p>Hi</p>", "text": "Hi"}}])
        spec = {"root": "r", "elements": {"r": {"type": "container"}}}
        result = client.templates.render({"spec": spec, "variables": {"name": "Ada"}})
        self.assertEqual(result["html"], "<p>Hi</p>")
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/templates/render")
        self.assertEqual(json.loads(call["body"]), {"spec": spec, "variables": {"name": "Ada"}})

    def test_create_posts_body_with_from_alias(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_1"}}])
        client.templates.create(
            publication_id="pub_1", name="Welcome", html="<p>Hi</p>", from_="a@b.com"
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/templates")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "Welcome", "html": "<p>Hi</p>", "from": "a@b.com"},
        )

    def test_list_passes_publication_id_limit_and_after_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.templates.list(publication_id="pub_1", limit=5, after="cur_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/templates?publication_id=pub_1&limit=5&after=cur_1",
        )

    def test_get_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_1"}}])
        client.templates.get("tpl_1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/templates/tpl_1?publication_id=pub_1"
        )

    def test_update_puts_publication_id_in_query_and_sends_body(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_1"}}])
        client.templates.update("tpl_1", {"publication_id": "pub_1", "name": "Renamed"})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/templates/tpl_1?publication_id=pub_1"
        )
        self.assertEqual(
            json.loads(call["body"]), {"publication_id": "pub_1", "name": "Renamed"}
        )

    def test_publish_posts_with_publication_id_and_no_body(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_1", "status": "published"}}])
        client.templates.publish("tpl_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/templates/tpl_1/publish?publication_id=pub_1"
        )
        self.assertIsNone(call["body"])

    def test_duplicate_posts_with_publication_id(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_2"}}])
        client.templates.duplicate("tpl_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "POST")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/templates/tpl_1/duplicate?publication_id=pub_1",
        )

    def test_delete_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "template", "id": "tpl_1", "deleted": True}}])
        client.templates.delete("tpl_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/templates/tpl_1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
