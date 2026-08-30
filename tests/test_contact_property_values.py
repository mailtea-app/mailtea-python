"""Bead mailtea-kg2r: contact property VALUES were unsettable outside the
dashboard, so a script could define ``first_name`` and never fill it in — every
email using ``{{contact.first_name}}`` came out blank."""

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


class ContactPropertyValuesTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_set_property_values_puts_to_the_properties_subresource(self):
        client, transport = self._client([{"status": 200, "json": {"contact_id": "con_1"}}])
        client.contacts.set_property_values(
            "con_1",
            publication_id="pub_1",
            values=[{"key": "first_name", "value": "Ada"}],
        )
        call = transport.calls[0]
        self.assertEqual(call["method"], "PUT")
        self.assertTrue(call["url"].endswith("/v1/contacts/con_1/properties"), call["url"])
        self.assertEqual(json.loads(call["body"])["values"][0]["key"], "first_name")

    def test_an_email_address_is_url_encoded(self):
        # Contacts are addressable by email, and an unencoded @ would split the path.
        client, transport = self._client([{"status": 200, "json": {}}])
        client.contacts.set_property_values(
            "ada@example.com", publication_id="pub_1", values=[]
        )
        self.assertIn("ada%40example.com/properties", transport.calls[0]["url"])

    def test_an_empty_value_is_sent_verbatim_because_it_CLEARS(self):
        # Empty is not "absent": it is how a value is cleared, which is what
        # makes the property's fallback_value apply again.
        client, transport = self._client([{"status": 200, "json": {}}])
        client.contacts.set_property_values(
            "con_1", publication_id="pub_1", values=[{"key": "first_name", "value": ""}]
        )
        self.assertEqual(json.loads(transport.calls[0]["body"])["values"][0]["value"], "")

    def test_list_property_values_gets_with_the_publication_in_the_query(self):
        client, transport = self._client([{"status": 200, "json": {"properties": []}}])
        client.contacts.list_property_values("con_1", publication_id="pub_1")
        call = transport.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertIn("/v1/contacts/con_1/properties?", call["url"])
        self.assertIn("publication_id=pub_1", call["url"])


if __name__ == "__main__":
    unittest.main()
