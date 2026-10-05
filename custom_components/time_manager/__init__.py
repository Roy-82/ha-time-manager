"""Zeitmanager Integration."""

from __future__ import annotations

from pathlib import Path

import voluptuous as vol

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    PLATFORMS,
    SERVICE_ADD_DEVICE,
    SERVICE_UPDATE_DEVICE,
    SERVICE_REMOVE_DEVICE,
    SERVICE_SET_DEVICE_ENABLED,
    SERVICE_ADD_SCHEDULE,
    SERVICE_UPDATE_SCHEDULE,
    SERVICE_REMOVE_SCHEDULE,
    SERVICE_START_TIMER,
    SERVICE_CANCEL_TIMER,
    SERVICE_SET_ENABLED,
)
from .manager import TimeManager

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    hass.data.setdefault(DOMAIN, {})

    frontend_dir = Path(__file__).parent / "frontend"
    await hass.http.async_register_static_paths(
        [StaticPathConfig("/time_manager", str(frontend_dir), False)]
    )

    def _manager(call: ServiceCall) -> TimeManager:
        manager = hass.data[DOMAIN].get(call.data["config_entry_id"])
        if not manager:
            raise ValueError("Zeitmanager nicht gefunden")
        return manager

    async def add_device(call: ServiceCall):
        manager = _manager(call)
        data = dict(call.data)
        data.pop("config_entry_id", None)
        await manager.async_add_device(data)

    async def update_device(call: ServiceCall):
        manager = _manager(call)
        data = dict(call.data)
        device_id = data.pop("device_id")
        data.pop("config_entry_id", None)
        await manager.async_update_device(device_id, data)

    async def remove_device(call: ServiceCall):
        await _manager(call).async_remove_device(call.data["device_id"])

    async def set_device_enabled(call: ServiceCall):
        await _manager(call).async_set_device_enabled(
            call.data["device_id"], call.data["enabled"]
        )

    async def add_schedule(call: ServiceCall):
        manager = _manager(call)
        data = dict(call.data)
        device_id = data.pop("device_id")
        data.pop("config_entry_id", None)
        await manager.async_add_schedule(device_id, data)

    async def update_schedule(call: ServiceCall):
        manager = _manager(call)
        data = dict(call.data)
        device_id = data.pop("device_id")
        schedule_id = data.pop("schedule_id")
        data.pop("config_entry_id", None)
        await manager.async_update_schedule(device_id, schedule_id, data)

    async def remove_schedule(call: ServiceCall):
        await _manager(call).async_remove_schedule(
            call.data["device_id"], call.data["schedule_id"]
        )

    async def start_timer(call: ServiceCall):
        await _manager(call).async_start_timer(
            call.data["device_id"], call.data["duration_min"]
        )

    async def cancel_timer(call: ServiceCall):
        await _manager(call).async_cancel_timer(
            call.data["device_id"], call.data.get("turn_off", False)
        )

    async def set_enabled(call: ServiceCall):
        await _manager(call).async_set_enabled(call.data["enabled"])

    if not hass.services.has_service(DOMAIN, SERVICE_ADD_DEVICE):
        common = {
            vol.Required("config_entry_id"): cv.string,
            vol.Required("name"): cv.string,
            vol.Required("entity_id"): cv.entity_id,
            vol.Optional("enabled", default=True): cv.boolean,
            vol.Optional("climate_mode", default="heat_cool"): cv.string,
            vol.Optional("target_temp"): vol.Any(None, vol.Coerce(float)),
            vol.Optional("cover_on_position", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional("cover_off_position", default=0): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional("timer_presets", default=[30, 60, 90]): [vol.All(vol.Coerce(int), vol.Range(min=1, max=10080))],
        }
        hass.services.async_register(DOMAIN, SERVICE_ADD_DEVICE, add_device, schema=vol.Schema(common))

        update_common = {
            vol.Required("config_entry_id"): cv.string,
            vol.Required("device_id"): cv.string,
            vol.Optional("name"): cv.string,
            vol.Optional("entity_id"): cv.entity_id,
            vol.Optional("enabled"): cv.boolean,
            vol.Optional("climate_mode"): cv.string,
            vol.Optional("target_temp"): vol.Any(None, vol.Coerce(float)),
            vol.Optional("cover_on_position"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional("cover_off_position"): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
            vol.Optional("timer_presets"): [vol.All(vol.Coerce(int), vol.Range(min=1, max=10080))],
        }
        hass.services.async_register(DOMAIN, SERVICE_UPDATE_DEVICE, update_device, schema=vol.Schema(update_common))
        hass.services.async_register(
            DOMAIN, SERVICE_REMOVE_DEVICE, remove_device,
            schema=vol.Schema({vol.Required("config_entry_id"): cv.string, vol.Required("device_id"): cv.string}),
        )
        hass.services.async_register(
            DOMAIN, SERVICE_SET_DEVICE_ENABLED, set_device_enabled,
            schema=vol.Schema({
                vol.Required("config_entry_id"): cv.string,
                vol.Required("device_id"): cv.string,
                vol.Required("enabled"): cv.boolean,
            }),
        )

        schedule_fields = {
            vol.Required("config_entry_id"): cv.string,
            vol.Required("device_id"): cv.string,
            vol.Required("name"): cv.string,
            vol.Optional("enabled", default=True): cv.boolean,
            vol.Required("weekdays"): [vol.All(vol.Coerce(int), vol.Range(min=0, max=6))],
            vol.Required("start_type"): vol.In(["time", "sunrise", "sunset"]),
            vol.Optional("start_time", default="08:00"): cv.string,
            vol.Optional("start_offset_min", default=0): vol.Coerce(int),
            vol.Required("end_type"): vol.In(["time", "sunrise", "sunset"]),
            vol.Optional("end_time", default="10:00"): cv.string,
            vol.Optional("end_offset_min", default=0): vol.Coerce(int),
        }
        hass.services.async_register(DOMAIN, SERVICE_ADD_SCHEDULE, add_schedule, schema=vol.Schema(schedule_fields))

        update_schedule_fields = dict(schedule_fields)
        update_schedule_fields[vol.Required("schedule_id")] = cv.string
        hass.services.async_register(DOMAIN, SERVICE_UPDATE_SCHEDULE, update_schedule, schema=vol.Schema(update_schedule_fields))

        hass.services.async_register(
            DOMAIN, SERVICE_REMOVE_SCHEDULE, remove_schedule,
            schema=vol.Schema({
                vol.Required("config_entry_id"): cv.string,
                vol.Required("device_id"): cv.string,
                vol.Required("schedule_id"): cv.string,
            }),
        )
        hass.services.async_register(
            DOMAIN, SERVICE_START_TIMER, start_timer,
            schema=vol.Schema({
                vol.Required("config_entry_id"): cv.string,
                vol.Required("device_id"): cv.string,
                vol.Required("duration_min"): vol.All(vol.Coerce(int), vol.Range(min=1, max=10080)),
            }),
        )
        hass.services.async_register(
            DOMAIN, SERVICE_CANCEL_TIMER, cancel_timer,
            schema=vol.Schema({
                vol.Required("config_entry_id"): cv.string,
                vol.Required("device_id"): cv.string,
                vol.Optional("turn_off", default=False): cv.boolean,
            }),
        )
        hass.services.async_register(
            DOMAIN, SERVICE_SET_ENABLED, set_enabled,
            schema=vol.Schema({
                vol.Required("config_entry_id"): cv.string,
                vol.Required("enabled"): cv.boolean,
            }),
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    manager = TimeManager(hass, entry)
    await manager.async_load()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = manager
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await manager.async_start()
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    manager = hass.data[DOMAIN].get(entry.entry_id)
    if manager:
        await manager.async_stop()
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
