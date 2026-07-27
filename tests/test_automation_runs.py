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


class AutomationRunsTest(unittest.TestCase):
    def _client(self, responses):
        transport = fake_transport(responses)
        client = Mailtea("mt_pat_test", base_url="https://api.mailtea.app", transport=transport)
        return client, transport

    def test_list_passes_filters_in_query(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automation_runs.list(
            "auto_1", publication_id="pub_1", contact_id="c_1", limit=5, after="cur_1"
        )
        call = t.calls[0]
        self.assertEqual(call["method"], "GET")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs"
            "?publication_id=pub_1&contact_id=c_1&limit=5&after=cur_1",
        )
        self.assertIsNone(call["body"])

    def test_list_joins_a_status_list_into_one_param(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automation_runs.list(
            "auto_1", publication_id="pub_1", status=["executing", "waiting_event"]
        )
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs"
            "?publication_id=pub_1&status=executing%2Cwaiting_event",
        )

    def test_list_leaves_a_status_string_alone(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automation_runs.list("auto_1", publication_id="pub_1", status="completed")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs"
            "?publication_id=pub_1&status=completed",
        )

    def test_list_sends_is_test_as_the_literal_the_server_accepts(self):
        client, t = self._client([{"json": {"object": "list", "data": []}}])
        client.automation_runs.list("auto_1", publication_id="pub_1", is_test=False)
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs"
            "?publication_id=pub_1&is_test=false",
        )

    def test_list_does_not_mutate_the_callers_params(self):
        client, _ = self._client([{"json": {"object": "list", "data": []}}])
        params = {"publication_id": "pub_1", "status": ["scheduled"], "is_test": True}
        client.automation_runs.list("auto_1", params)
        self.assertEqual(
            params, {"publication_id": "pub_1", "status": ["scheduled"], "is_test": True}
        )

    def test_get_passes_publication_id_in_query(self):
        client, t = self._client([{"json": {"object": "automation_run", "id": "arun_1"}}])
        run = client.automation_runs.get("auto_1", "arun_1", {"publication_id": "pub_1"})
        self.assertEqual(run["id"], "arun_1")
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs/arun_1?publication_id=pub_1",
        )

    def test_cancel_posts_with_publication_id_and_no_body(self):
        client, t = self._client(
            [{"json": {"object": "automation_run", "id": "arun_1", "status": "canceled"}}]
        )
        client.automation_runs.cancel("auto_1", "arun_1", {"publication_id": "pub_1"})
        call = t.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(
            call["url"],
            "https://api.mailtea.app/v1/automations/auto_1/runs/arun_1/cancel?publication_id=pub_1",
        )
        self.assertIsNone(call["body"])

    def test_ids_are_url_encoded(self):
        client, t = self._client([{"json": {"object": "automation_run", "id": "arun/1"}}])
        client.automation_runs.get("auto/1", "arun/1", {"publication_id": "pub_1"})
        self.assertEqual(
            t.calls[0]["url"],
            "https://api.mailtea.app/v1/automations/auto%2F1/runs/arun%2F1?publication_id=pub_1",
        )


if __name__ == "__main__":
    unittest.main()
