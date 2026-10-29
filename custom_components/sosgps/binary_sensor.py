"""Tracker connectivity (distinct from integration availability)."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

from .entity import SosgpsEntity, setup_entities


async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, [SosgpsOnline])


class SosgpsOnline(SosgpsEntity, BinarySensorEntity):
    _attr_name = "Online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, device_id):
        super().__init__(coordinator, entry, device_id, "online")

    @property
    def is_on(self):
        return self.device.get("online")
