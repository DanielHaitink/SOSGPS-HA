"""Small read-only SOSGPS API client. Never log credentials or response bodies."""
from __future__ import annotations

import asyncio
import math
from urllib.parse import urlsplit

import aiohttp


class InvalidAuth(Exception):
    """The grant is invalid, revoked or expired."""


class CannotConnect(Exception):
    """The service cannot provide a valid response."""


def validate_url(value: str) -> str:
    """Only accept an HTTPS origin without embedded credentials or query data."""
    if not isinstance(value, str):
        raise ValueError("HTTPS server URL required")
    value = value.strip().rstrip("/")
    try:
        parsed = urlsplit(value)
        port = parsed.port
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.path or parsed.query or parsed.fragment
                or "\\" in value or any(ord(char) < 33 for char in value)):
            raise ValueError("HTTPS server origin required")
    except (ValueError, TypeError) as error:
        raise ValueError("HTTPS server origin required") from error
    # Canonicalize to prevent duplicate entries for the same server.
    hostname = parsed.hostname.lower()
    if ":" in hostname:
        hostname = f"[{hostname}]"
    return f"https://{hostname}" + (f":{port}" if port and port != 443 else "")


def validate_token(value: str) -> str:
    if not isinstance(value, str) or len(value.strip()) != 49 or not value.strip().startswith("sgpha_"):
        raise ValueError("SOSGPS access token required")
    return value.strip()


def _number(value, minimum, maximum):
    return (type(value) in (int, float) and math.isfinite(value)
            and minimum <= value <= maximum)


def validate_payload(data):
    if (not isinstance(data, dict) or data.get("api_version") != 1
            or not isinstance(data.get("grant_id"), str) or not data["grant_id"]
            or not isinstance(data.get("devices"), list) or len(data["devices"]) > 100):
        raise CannotConnect("Unsupported SOSGPS response")
    ids = set()
    for device in data["devices"]:
        if (not isinstance(device, dict) or not isinstance(device.get("id"), str)
                or not device["id"] or device["id"] in ids
                or not isinstance(device.get("name"), str)
                or type(device.get("online")) is not bool):
            raise CannotConnect("Invalid tracker response")
        ids.add(device["id"])
        for key, minimum, maximum in (("battery", 0, 100), ("last_seen", 0, 4102444800)):
            if device.get(key) is not None and not _number(device[key], minimum, maximum):
                raise CannotConnect("Invalid tracker value")
        location = device.get("location")
        if location is not None:
            if (not isinstance(location, dict)
                    or not _number(location.get("latitude"), -90, 90)
                    or not _number(location.get("longitude"), -180, 180)
                    or type(location.get("gps_valid")) is not bool
                    or location.get("accuracy") is not None and not _number(location["accuracy"], 0, 1000000)
                    or location.get("updated_at") is not None and not _number(location["updated_at"], 0, 4102444800)):
                raise CannotConnect("Invalid location response")
    return data


class SosgpsClient:
    def __init__(self, session: aiohttp.ClientSession, server_url: str, token: str):
        self.session = session
        self.server_url = validate_url(server_url)
        self._token = validate_token(token)

    async def async_get_devices(self):
        try:
            async with self.session.get(
                self.server_url + "/api/integrations/home-assistant/v1/devices",
                headers={"Authorization": "Bearer " + self._token},
                timeout=aiohttp.ClientTimeout(total=15),
                allow_redirects=False,
                ssl=True,
            ) as response:
                if response.status in (401, 403):
                    raise InvalidAuth("SOSGPS access must be renewed")
                if response.status != 200:
                    raise CannotConnect("SOSGPS request failed")
                # Bound memory even for a misconfigured server.
                payload = bytearray()
                async for chunk in response.content.iter_chunked(16384):
                    payload.extend(chunk)
                    if len(payload) > 262144:
                        raise CannotConnect("SOSGPS response too large")
                import json
                return validate_payload(json.loads(payload))
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError, UnicodeError) as error:
            raise CannotConnect("Cannot read SOSGPS") from error
