from __future__ import annotations

from http.server import ThreadingHTTPServer
from threading import Thread
from urllib.request import urlopen

from distribution_os.stdlib_server import api_payload, handler_for

from support import ApplicationTestCase


class DashboardPayloadTests(ApplicationTestCase):
    def test_dashboard_modules_have_live_payloads(self) -> None:
        for endpoint in (
            "overview",
            "assets",
            "verticals",
            "platforms",
            "accounts",
            "jobs",
            "publications",
            "variants",
            "analytics",
            "experiments",
            "human-queue",
            "rules",
            "health",
            "logs",
            "settings",
        ):
            self.assertIsNotNone(api_payload(self.app, endpoint), endpoint)

    def test_unknown_api_payload_fails_closed(self) -> None:
        with self.assertRaises(KeyError):
            api_payload(self.app, "unknown")

    def test_actual_http_dashboard_and_api(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(self.app))
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            base = f"http://127.0.0.1:{server.server_port}"
            with urlopen(base + "/", timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"Distribution OS", response.read())
            with urlopen(base + "/api/platforms", timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"chrome_web_store", response.read())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
