"""Shared entity state and dynamic discovery."""
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class SosgpsEntity(CoordinatorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, device_id, key):
        super().__init__(coordinator)
        self.device_id = device_id
        self._attr_unique_id = f"{entry.unique_id}_{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{entry.unique_id}_{device_id}")},
            name=self.device.get("name", device_id),
            manufacturer="SOSGPS",
        )

    @property
    def device(self):
        return (self.coordinator.data or {}).get(self.device_id, {})

    @property
    def available(self):
        return super().available and bool(self.device)


def setup_entities(entry, async_add_entities, factories):
    coordinator = entry.runtime_data
    known = set()

    @callback
    def discover():
        new_ids = set(coordinator.data or {}) - known
        if new_ids:
            async_add_entities([factory(coordinator, entry, device_id)
                                for device_id in sorted(new_ids) for factory in factories])
            known.update(new_ids)

    entry.async_on_unload(coordinator.async_add_listener(discover))
    discover()
