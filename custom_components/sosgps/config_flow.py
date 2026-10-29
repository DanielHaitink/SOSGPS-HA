"""UI setup and token renewal; tracker scope is managed by SOSGPS."""
import hashlib

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import CannotConnect, InvalidAuth, SosgpsClient, validate_url, validate_token
from .const import CONF_SERVER_URL, DOMAIN


class SosgpsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _validate(self, user_input):
        server = validate_url(user_input[CONF_SERVER_URL])
        token = validate_token(user_input[CONF_ACCESS_TOKEN])
        payload = await SosgpsClient(async_get_clientsession(self.hass), server, token).async_get_devices()
        return {CONF_SERVER_URL: server, CONF_ACCESS_TOKEN: token}, payload

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                data, payload = await self._validate(user_input)
            except ValueError:
                errors["base"] = "invalid_input"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                unique = hashlib.sha256((data[CONF_SERVER_URL] + "/" + payload["grant_id"]).encode()).hexdigest()
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="SOSGPS", data=data)
        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_SERVER_URL): str,
            vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)

    async def async_step_reauth(self, entry_data):
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        errors = {}
        entry = self._get_reauth_entry()
        if user_input is not None:
            try:
                data, _ = await self._validate({**entry.data, **user_input})
            except ValueError:
                errors["base"] = "invalid_input"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            else:
                # Preserve the entry ID/unique ID so existing automations survive renewal.
                return self.async_update_reload_and_abort(entry, data_updates=data)
        return self.async_show_form(step_id="reauth_confirm", data_schema=vol.Schema({
            vol.Required(CONF_ACCESS_TOKEN): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)),
        }), errors=errors)
