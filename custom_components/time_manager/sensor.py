"""Statussensor des Zeitmanagers."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    manager = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TimeManagerSensor(manager)], True)


class TimeManagerSensor(SensorEntity):
    _attr_icon = "mdi:clock-outline"

    def __init__(self, manager):
        self.manager = manager
        self._attr_unique_id = f"{manager.entry_id}_status"
        self._attr_name = manager.name
        self._remove_listener = None

    @property
    def native_value(self):
        return "on" if self.manager.enabled else "off"

    @property
    def extra_state_attributes(self):
        return self.manager.state_attributes

    async def async_added_to_hass(self):
        self._remove_listener = self.manager.add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self):
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self.manager.entry_id)},
            name=self.manager.name,
            manufacturer="Lokal",
            model="Zeitmanager",
        )
