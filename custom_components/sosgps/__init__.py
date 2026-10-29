"""Read-only SOSGPS tracker integration."""
from homeassistant.const import CONF_ACCESS_TOKEN, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SosgpsClient
from .const import CONF_SERVER_URL
from .coordinator import SosgpsCoordinator

PLATFORMS = [Platform.DEVICE_TRACKER, Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass, entry):
    client = SosgpsClient(async_get_clientsession(hass), entry.data[CONF_SERVER_URL], entry.data[CONF_ACCESS_TOKEN])
    coordinator = SosgpsCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
