"""Optional checks against real Home Assistant; run in its supported Python."""
import importlib.util
import tempfile
import unittest

HAS_HA = importlib.util.find_spec("homeassistant") is not None


@unittest.skipUnless(HAS_HA, "Home Assistant runtime not installed")
class RuntimeChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        from homeassistant.core import HomeAssistant
        from homeassistant.config_entries import ConfigEntry
        self.directory = tempfile.TemporaryDirectory()
        self.hass = HomeAssistant(self.directory.name)
        self.entry = ConfigEntry(version=1, minor_version=1, domain="sosgps",
                                title="SOSGPS", data={}, options={}, source="user",
                                unique_id="connection", discovery_keys={}, subentries_data=[])

    async def asyncTearDown(self):
        await self.hass.async_stop()
        self.directory.cleanup()

    async def test_zone_accuracy_and_permission_loss(self):
        from custom_components.sosgps.coordinator import SosgpsCoordinator
        from custom_components.sosgps.device_tracker import SosgpsTracker
        from custom_components.sosgps.sensor import SosgpsBattery, SosgpsLastSeen
        from custom_components.sosgps.binary_sensor import SosgpsOnline
        from homeassistant.components.zone import async_active_zone, DATA_ZONE_ENTITY_IDS

        class Client:
            async def async_get_devices(self):
                return {"devices": [{"id": "tracker", "name": "Demo", "battery": 80,
                        "online": True, "last_seen": 1790000000, "location": {
                        "latitude": 52.1, "longitude": 5.1, "accuracy": None,
                        "gps_valid": True, "updated_at": 1790000000}}]}

        coordinator = SosgpsCoordinator(self.hass, self.entry, Client())
        coordinator.data = await coordinator._async_update_data()
        tracker = SosgpsTracker(coordinator, self.entry, "tracker")
        tracker.hass = self.hass
        self.hass.states.async_set("zone.home", "0", {"latitude": 52.1, "longitude": 5.1, "radius": 100, "friendly_name": "Home"})
        self.hass.data[DATA_ZONE_ENTITY_IDS] = ["zone.home"]
        self.assertEqual(tracker.location_accuracy, 0)
        self.assertEqual(async_active_zone(self.hass, tracker.latitude, tracker.longitude, tracker.location_accuracy).entity_id, "zone.home")
        self.assertEqual(SosgpsBattery(coordinator, self.entry, "tracker").native_value, 80)
        self.assertTrue(SosgpsOnline(coordinator, self.entry, "tracker").is_on)
        self.assertIsNotNone(SosgpsLastSeen(coordinator, self.entry, "tracker").native_value)
        original = coordinator.data
        coordinator.data = {}
        self.assertFalse(tracker.available)
        self.assertIsNone(tracker.latitude)
        self.assertIsNone(tracker.longitude)
        coordinator.data = original
        self.assertTrue(tracker.available)
        self.assertEqual(tracker.latitude, 52.1)
        await coordinator.async_shutdown()

    async def test_coordinator_clears_values_on_errors(self):
        from custom_components.sosgps.coordinator import SosgpsCoordinator
        from custom_components.sosgps.api import CannotConnect, InvalidAuth
        from homeassistant.helpers.update_coordinator import UpdateFailed
        from homeassistant.exceptions import ConfigEntryAuthFailed

        class Client:
            error = CannotConnect()
            async def async_get_devices(self):
                raise self.error

        client = Client()
        coordinator = SosgpsCoordinator(self.hass, self.entry, client)
        coordinator.data = {"tracker": {"location": {"latitude": 52.1}}}
        with self.assertRaises(UpdateFailed):
            await coordinator._async_update_data()
        self.assertEqual(coordinator.data, {})
        client.error = InvalidAuth()
        coordinator.data = {"tracker": {}}
        with self.assertRaises(ConfigEntryAuthFailed):
            await coordinator._async_update_data()
        self.assertEqual(coordinator.data, {})
        await coordinator.async_shutdown()

    async def test_config_flow_validates_before_creating_entry(self):
        from unittest.mock import AsyncMock, patch
        from homeassistant.config_entries import ConfigEntries
        from homeassistant.const import CONF_ACCESS_TOKEN
        from custom_components.sosgps.config_flow import SosgpsConfigFlow
        from custom_components.sosgps.const import CONF_SERVER_URL
        from custom_components.sosgps.api import InvalidAuth

        self.hass.config_entries = ConfigEntries(self.hass, {})
        flow = SosgpsConfigFlow()
        flow.hass = self.hass
        flow.handler = "sosgps"
        flow.context = {"source": "user"}
        form = await flow.async_step_user()
        self.assertEqual(form["step_id"], "user")
        values = {CONF_SERVER_URL: "http://example.com", CONF_ACCESS_TOKEN: "sgpha_" + "x" * 43}
        result = await flow.async_step_user(values)
        self.assertEqual(result["errors"]["base"], "invalid_input")
        values[CONF_SERVER_URL] = "https://EXAMPLE.com/"
        with patch("custom_components.sosgps.config_flow.async_get_clientsession", return_value=object()), patch(
            "custom_components.sosgps.api.SosgpsClient.async_get_devices", new=AsyncMock(side_effect=InvalidAuth())
        ):
            result = await flow.async_step_user(values)
            self.assertEqual(result["errors"]["base"], "invalid_auth")
        with patch("custom_components.sosgps.config_flow.async_get_clientsession", return_value=object()), patch(
            "custom_components.sosgps.api.SosgpsClient.async_get_devices", new=AsyncMock(return_value={"grant_id": "connection", "devices": []})
        ):
            result = await flow.async_step_user(values)
        self.assertEqual(result["type"], "create_entry")
        self.assertEqual(result["data"][CONF_SERVER_URL], "https://example.com")
