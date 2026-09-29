import base64
import os
import unittest

os.environ["SKIP_BACKGROUND_TASKS"] = "1"

from fastapi.testclient import TestClient

from app import _authorized, _is_public_get, app


class AccessControlTest(unittest.TestCase):
    def test_only_health_and_read_only_feeds_are_public(self):
        self.assertTrue(_is_public_get("GET", "/api/health"))
        self.assertTrue(_is_public_get("GET", "/api/rss/all"))
        self.assertTrue(_is_public_get("GET", "/api/rss/MzExample=="))
        self.assertTrue(_is_public_get("GET", "/api/rss/MzExample==/history"))
        self.assertTrue(_is_public_get("GET", "/api/rss/category/1"))
        self.assertFalse(_is_public_get("GET", "/api/rss/subscriptions"))
        self.assertFalse(_is_public_get("GET", "/api/rss/status"))
        self.assertFalse(_is_public_get("POST", "/api/rss/MzExample=="))
        self.assertFalse(_is_public_get("GET", "/login.html"))

    def test_basic_auth_uses_the_fixed_admin_account(self):
        token = base64.b64encode(b"admin:secret")
        self.assertTrue(_authorized({b"authorization": b"Basic " + token}, "secret"))
        self.assertFalse(_authorized({b"authorization": b"Basic " + token}, "wrong"))
        self.assertTrue(_authorized({}, ""))

    def test_http_gate(self):
        previous = os.environ.get("ADMIN_PASSWORD")
        os.environ["ADMIN_PASSWORD"] = "secret"
        try:
            client = TestClient(app)
            self.assertEqual(client.get("/api/health").status_code, 200)
            self.assertEqual(client.get("/login.html").status_code, 401)
            self.assertEqual(client.get("/api/rss/subscriptions").status_code, 401)
            self.assertEqual(client.get("/login.html", auth=("admin", "secret")).status_code, 200)
        finally:
            if previous is None:
                os.environ.pop("ADMIN_PASSWORD", None)
            else:
                os.environ["ADMIN_PASSWORD"] = previous


if __name__ == "__main__":
    unittest.main()
