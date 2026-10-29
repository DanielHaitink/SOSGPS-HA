"""Exercise the real client against controlled responses, without a HA install."""
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location("sosgps_api", Path(__file__).parents[1] / "custom_components/sosgps/api.py")
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)

TOKEN = "sgpha_" + "x" * 43
PAYLOAD = {"api_version": 1, "grant_id": "connection", "devices": []}


class Content:
    def __init__(self, payload):
        self.payload = payload

    async def iter_chunked(self, size):
        yield self.payload


class Response:
    def __init__(self, status=200, payload=None):
        self.status = status
        self.content = Content(json.dumps(PAYLOAD if payload is None else payload).encode())

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


class ApiChecks(unittest.IsolatedAsyncioTestCase):
    def test_requires_https_origin(self):
        for value in ("http://example.com", "https://user:pass@example.com", "https://example.com/api",
                      "https://example.com?token=secret", "https://example.com#fragment", "https://example.com:bad"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                api.validate_url(value)
        self.assertEqual(api.validate_url("https://EXAMPLE.com:443/"), "https://example.com")

    async def test_auth_and_transport(self):
        session = Session(Response())
        result = await api.SosgpsClient(session, "https://example.com", TOKEN).async_get_devices()
        self.assertEqual(result, PAYLOAD)
        url, options = session.calls[0]
        self.assertEqual(url, "https://example.com/api/integrations/home-assistant/v1/devices")
        self.assertTrue(options["ssl"])
        self.assertFalse(options["allow_redirects"])
        self.assertEqual(options["headers"], {"Authorization": "Bearer " + TOKEN})

    async def test_revoked_and_expired_grants(self):
        for status in (401, 403):
            with self.subTest(status=status), self.assertRaises(api.InvalidAuth):
                await api.SosgpsClient(Session(Response(status)), "https://example.com", TOKEN).async_get_devices()

    async def test_refuses_redirect_and_server_errors(self):
        for status in (301, 302, 307, 429, 500):
            session = Session(Response(status))
            with self.subTest(status=status), self.assertRaises(api.CannotConnect):
                await api.SosgpsClient(session, "https://example.com", TOKEN).async_get_devices()
            self.assertEqual(len(session.calls), 1)

    async def test_rejects_malformed_response(self):
        for value in ([], {}, {"api_version": 2, "grant_id": "id", "devices": []},
                      {"api_version": 1, "grant_id": "id", "devices": [{"id": "bad"}]}):
            with self.subTest(value=value), self.assertRaises(api.CannotConnect):
                await api.SosgpsClient(Session(Response(payload=value)), "https://example.com", TOKEN).async_get_devices()

    async def test_bounds_response_size(self):
        response = Response()
        response.content = Content(b"x" * 262145)
        with self.assertRaises(api.CannotConnect):
            await api.SosgpsClient(Session(response), "https://example.com", TOKEN).async_get_devices()
