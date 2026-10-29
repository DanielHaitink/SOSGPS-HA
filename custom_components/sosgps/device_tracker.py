"""GPS location entities."""
from homeassistant.components.device_tracker import SourceType, TrackerEntity

from .entity import SosgpsEntity, setup_entities


async def async_setup_entry(hass, entry, async_add_entities):
    setup_entities(entry, async_add_entities, [SosgpsTracker])


class SosgpsTracker(SosgpsEntity, TrackerEntity):
    _attr_name = None
    _attr_source_type = SourceType.GPS

    def __init__(self, coordinator, entry, device_id):
        super().__init__(coordinator, entry, device_id, "location")

    @property
    def location(self):
        return self.device.get("location") or {}

    @property
    def available(self):
        return super().available and bool(self.location)

    @property
    def latitude(self):
        return self.location.get("latitude")

    @property
    def longitude(self):
        return self.location.get("longitude")

    @property
    def location_accuracy(self):
        return self.location.get("accuracy") or 0

    @property
    def extra_state_attributes(self):
        location = self.location
        return {"gps_valid": location.get("gps_valid"), "position_updated_at": location.get("updated_at")}
