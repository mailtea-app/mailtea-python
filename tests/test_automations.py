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


STEPS = [
    {"key": "trigger", "type": "trigger", "config": {"trigger_type": "contact.subscribed"}},
    {"key": "wait", "type": "delay", "config": {"duration": 1, "unit": "days"}},
]


class AutomationsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_validate_posts_graph_in_body(self):
        client, t = self._client(
            [{"json": {"object": "automation_validation", "valid": True, "issues": []}}]
        )
        result = client.automations.validate(publication_id="pub_1", steps=STEPS)
        self.assertTrue(result["valid"])
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/automations/validate")
        self.assertEqual(
            json.loads(call["body"]), {"publication_id": "pub_1", "steps": STEPS}
        )

    def test_create_posts_publication_id_in_body_without_query(self):
        client, t = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
        client.automations.create(publication_id="pub_1", name="Welcome", steps=STEPS)
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://api.mailtea.app/v1/automations")
        self.assertEqual(
            json.loads(call["body"]),
            {"publication_id": "pub_1", "name": "Welcome", "steps": STEPS},
        )

    def test_create_carries_validate_only_and_connections(self):
        client, t = self._client(
            [{"json": {"object": "automation_validation", "valid": False, "issues": []}}]
        )
        connections = [{"from": "trigger", "to": "wait", "branch": "next"}]
        client.automations.create(
            {"publication_id": "pub_1", "name": "Welcome", "steps": STEPS},
            connections=connections,
            validate_only=True,
        )
        body = json.loads(t.calls[0]["body"])
        self.assertEqual(body["connections"], connections)
        self.assertIs(body["validate_only"], True)

    def test_list_passes_filters_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automations.list(publication_id="pub_1", status="active", limit=5, after="cur_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations"
            "?publication_id=pub_1&status=active&limit=5&after=cur_1",
        )

    def test_get_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
        client.automations.get("auto_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/automations/auto_1?publication_id=pub_1"
        )

    def test_update_puts_publication_id_in_query_and_drops_it_from_body(self):
        client, t = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
        client.automations.update("auto_1", {"publication_id": "pub_1", "name": "Renamed"})
        call = t.calls[0]
        self.assertEqual(call["method"], "PATCH")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1?publication_id=pub_1"
        )
        self.assertEqual(json.loads(call["body"]), {"name": "Renamed"})

    def test_update_does_not_mutate_the_callers_params(self):
        client, _ = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
        params = {"publication_id": "pub_1", "name": "Renamed"}
        client.automations.update("auto_1", params)
        self.assertEqual(params, {"publication_id": "pub_1", "name": "Renamed"})

    def test_delete_passes_publication_id_in_query(self):
        client, t = self._client(
            [{"json": {"object": "automation", "id": "auto_1", "deleted": True}}]
        )
        client.automations.delete("auto_1", {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "DELETE")
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/automations/auto_1?publication_id=pub_1"
        )

    def test_activate_posts_with_publication_id_and_no_body(self):
        client, t = self._client(
            [{"json": {"object": "automation", "id": "auto_1", "status": "active"}}]
        )
        client.automations.activate("auto_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1/activate?publication_id=pub_1"
        )
        self.assertIsNone(call["body"])

    def test_pause_without_cancel_runs_sends_no_body(self):
        client, t = self._client(
            [{"json": {"object": "automation", "id": "auto_1", "canceled_runs": 0}}]
        )
        client.automations.pause("auto_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1/pause?publication_id=pub_1"
        )
        self.assertIsNone(call["body"])

    def test_pause_with_cancel_runs_splits_query_and_body(self):
        client, t = self._client(
            [{"json": {"object": "automation", "id": "auto_1", "canceled_runs": 3}}]
        )
        client.automations.pause("auto_1", publication_id="pub_1", cancel_runs=True)
        call = t.calls[0]
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1/pause?publication_id=pub_1"
        )
        self.assertEqual(json.loads(call["body"]), {"cancel_runs": True})

    def test_archive_with_cancel_runs_false_sends_the_flag(self):
        client, t = self._client(
            [{"json": {"object": "automation", "id": "auto_1", "canceled_runs": 0}}]
        )
        client.automations.archive("auto_1", publication_id="pub_1", cancel_runs=False)
        call = t.calls[0]
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1/archive?publication_id=pub_1"
        )
        self.assertEqual(json.loads(call["body"]), {"cancel_runs": False})

    def test_archive_without_cancel_runs_sends_no_body(self):
        client, t = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
        client.automations.archive("auto_1", {"publication_id": "pub_1"})
        self.assertIsNone(t.calls[0]["body"])

    def test_cancel_runs_none_is_omitted_rather_than_sent_as_null(self):
        for verb in ("pause", "archive"):
            client, t = self._client([{"json": {"object": "automation", "id": "auto_1"}}])
            getattr(client.automations, verb)(
                "auto_1", publication_id="pub_1", cancel_runs=None
            )
            self.assertIsNone(t.calls[0]["body"], verb)

    def test_versions_lists_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automations.versions("auto_1", publication_id="pub_1", limit=10)
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/versions?publication_id=pub_1&limit=10",
        )

    def test_version_retrieves_one_stored_graph(self):
        client, t = self._client([{"json": {"object": "automation_version", "version": 3}}])
        client.automations.version("auto_1", 3, {"publication_id": "pub_1"})
        self.assertEqual(t.calls[0]["method"], "GET")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/versions/3?publication_id=pub_1",
        )

    def test_metrics_passes_version_and_window_in_query(self):
        client, t = self._client([{"json": {"object": "automation_metrics", "steps": []}}])
        client.automations.metrics(
            "auto_1", publication_id="pub_1", version=2, since="2026-07-01T00:00:00Z"
        )
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/metrics"
            "?publication_id=pub_1&version=2&since=2026-07-01T00%3A00%3A00Z",
        )

    def test_test_puts_publication_id_in_query_and_drops_it_from_body(self):
        client, t = self._client(
            [{"status": 202, "json": {"object": "automation_run", "id": "arun_1", "is_test": True}}]
        )
        client.automations.test(
            "auto_1",
            {"publication_id": "pub_1", "email": "ada@example.com"},
            event_properties={"plan": "pro"},
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"], "https://api.mailtea.app/v1/automations/auto_1/test?publication_id=pub_1"
        )
        self.assertEqual(
            json.loads(call["body"]),
            {"email": "ada@example.com", "event_properties": {"plan": "pro"}},
        )

    def test_id_is_url_encoded(self):
        client, t = self._client([{"json": {"object": "automation", "id": "auto/1"}}])
        client.automations.get("auto/1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"], "https://api.mailtea.app/v1/automations/auto%2F1?publication_id=pub_1"
        )


if __name__ == "__main__":
    unittest.main()
