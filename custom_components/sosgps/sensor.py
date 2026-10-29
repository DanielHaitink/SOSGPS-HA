"""Battery and last-seen sensors."""
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.entity import EntityCategory

from .entity import SosgpsEntity, setup_entities


async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, [SosgpsBattery, SosgpsLastSeen])


class SosgpsBattery(SosgpsEntity, SensorEntity):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, device_id):
        super().__init__(coordinator, entry, device_id, "battery")

    @property
    def native_value(self):
        return self.device.get("battery")


class SosgpsLastSeen(SosgpsEntity, SensorEntity):
    _attr_name = "Last seen"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry, device_id):
        super().__init__(coordinator, entry, device_id, "last_seen")

    @property
    def native_value(self):
        value = self.device.get("last_seen")
        return datetime.fromtimestamp(value, tz=timezone.utc) if value else None
