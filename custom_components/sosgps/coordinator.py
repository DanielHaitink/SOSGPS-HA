"""One coordinated request for every authorized tracker."""
import logging
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import CannotConnect, InvalidAuth
from .const import DOMAIN, UPDATE_INTERVAL


class SosgpsCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, client):
        super().__init__(hass, logging.getLogger(__name__),
                         name=DOMAIN, update_interval=UPDATE_INTERVAL, config_entry=entry)
        self.client = client

    async def _async_update_data(self):
        try:
            payload = await self.client.async_get_devices()
        except InvalidAuth as error:
            self.data = {}
            raise ConfigEntryAuthFailed("Renew the SOSGPS connection token") from error
        except CannotConnect as error:
            self.data = {}
            raise UpdateFailed("SOSGPS is unavailable") from error
        return {device["id"]: device for device in payload["devices"]}
