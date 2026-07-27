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


class EventsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_send_posts_whole_payload_in_body(self):
        client, t = self._client(
            [
                {
                    "status": 202,
                    "json": {
                        "object": "event",
                        "id": "evt_1",
                        "enrolled_automations": 1,
                        "resumed_runs": 0,
                    },
                }
            ]
        )
        result = client.events.send(
            publication_id="pub_1",
            name="order.completed",
            email="ada@example.com",
            create_contact=True,
            properties={"total": 42},
            idempotency_key="ord_9",
        )
        self.assertEqual(result["enrolled_automations"], 1)
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/events")
        self.assertEqual(
            json.loads(call["body"]),
            {
                "publication_id": "pub_1",
                "name": "order.completed",
                "email": "ada@example.com",
                "create_contact": True,
                "properties": {"total": 42},
                "idempotency_key": "ord_9",
            },
        )

    def test_send_replay_reports_zero_enrollments(self):
        client, _ = self._client(
            [
                {
                    "status": 202,
                    "json": {
                        "object": "event",
                        "id": "evt_1",
                        "replayed": True,
                        "enrolled_automations": 0,
                        "resumed_runs": 0,
                    },
                }
            ]
        )
        result = client.events.send(publication_id="pub_1", name="order.completed", contact_id="c_1")
        self.assertIs(result["replayed"], True)
        self.assertEqual(result["enrolled_automations"], 0)

    def test_list_passes_filters_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.events.list(publication_id="pub_1", name="order.completed", contact_id="c_1", limit=5)
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/events"
            "?publication_id=pub_1&name=order.completed&contact_id=c_1&limit=5",
        )
        self.assertIsNone(call["body"])


class EventDefinitionsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_create_posts_publication_id_in_body_without_query(self):
        client, t = self._client([{"json": {"object": "event_definition", "id": "evd_1"}}])
        client.event_definitions.create(
            publication_id="pub_1",
            name="order.completed",
            description="Fires when checkout succeeds",
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/event-definitions")
        self.assertEqual(
            json.loads(call["body"]),
            {
                "publication_id": "pub_1",
                "name": "order.completed",
                "description": "Fires when checkout succeeds",
            },
        )

    def test_list_passes_filters_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.event_definitions.list(publication_id="pub_1", limit=5, after="cur_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/event-definitions?publication_id=pub_1&limit=5&after=cur_1",
        )

    def test_get_passes_publication_id_in_query(self):
        client, t = self._client(
            [{"json": {"object": "event_definition", "id": "evd_1", "inferred_properties": []}}]
        )
        client.event_definitions.get("evd_1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/event-definitions/evd_1?publication_id=pub_1",
        )

    def test_update_puts_publication_id_in_query_only(self):
        client, t = self._client([{"json": {"object": "event_definition", "id": "evd_1"}}])
        client.event_definitions.update(
            "evd_1", {"publication_id": "pub_1", "description": "Checkout success"}
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/event-definitions/evd_1?publication_id=pub_1",
        )
        self.assertEqual(json.loads(call["body"]), {"description": "Checkout success"})

    def test_update_does_not_mutate_the_callers_params(self):
        client, _ = self._client([{"json": {"object": "event_definition", "id": "evd_1"}}])
        params = {"publication_id": "pub_1", "description": "Checkout success"}
        client.event_definitions.update("evd_1", params)
        self.assertEqual(
            params, {"publication_id": "pub_1", "description": "Checkout success"}
        )

    def test_update_can_clear_schema_json(self):
        client, t = self._client([{"json": {"object": "event_definition", "id": "evd_1"}}])
        client.event_definitions.update("evd_1", publication_id="pub_1", schema_json=None)
        self.assertEqual(json.loads(t.calls[0]["body"]), {"schema_json": None})

    def test_delete_passes_publication_id_in_query(self):
        client, t = self._client(
            [{"json": {"object": "event_definition", "id": "evd_1", "deleted": True}}]
        )
        client.event_definitions.delete("evd_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/event-definitions/evd_1?publication_id=pub_1",
        )


if __name__ == "__main__":
    unittest.main()
