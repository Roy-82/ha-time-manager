"""Zeit- und Sonnenlogik des Zeitmanagers."""

from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta
import logging
import time
import uuid
from typing import Any, Callable

from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.helpers.sun import get_astral_event_date
from homeassistant.util import dt as dt_util

from .const import (
    CONF_LANGUAGE,
    CONF_SCAN_INTERVAL,
    DEFAULT_LANGUAGE,
    DEFAULT_SCAN_INTERVAL,
    STORAGE_KEY_PREFIX,
    STORAGE_VERSION,
    SUPPORTED_DOMAINS,
)

_LOGGER = logging.getLogger(__name__)


class TimeManager:
    """Verwaltet Geräte, Zeitpläne und Timer."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        self.hass = hass
        self.entry = entry
        self.entry_id = entry.entry_id
        self.name = entry.title

        data = dict(entry.data)
        data.update(entry.options)
        self.language = str(data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE))
        self.scan_interval = max(5, int(data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)))

        self.store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY_PREFIX}.{self.entry_id}")
        self.enabled = True
        self.devices: list[dict[str, Any]] = []
        self._listeners: set[Callable[[], None]] = set()
        self._unsub_timer = None
        self._lock = asyncio.Lock()

    async def async_load(self) -> None:
        stored = await self.store.async_load() or {}
        self.enabled = bool(stored.get("enabled", True))
        self.devices = [self._normalize_device(x) for x in stored.get("devices", [])]

    async def async_start(self) -> None:
        self._unsub_timer = async_track_time_interval(
            self.hass, self._async_tick, timedelta(seconds=self.scan_interval)
        )
        await self.async_evaluate()

    async def async_stop(self) -> None:
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    def add_listener(self, callback: Callable[[], None]) -> Callable[[], None]:
        self._listeners.add(callback)

        def _remove() -> None:
            self._listeners.discard(callback)

        return _remove

    def _notify(self) -> None:
        for callback in list(self._listeners):
            try:
                callback()
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Fehler beim Aktualisieren einer Zeitmanager-Entität")

    async def _save(self) -> None:
        await self.store.async_save({"enabled": self.enabled, "devices": self.devices})

    def _normalize_schedule(self, raw: dict[str, Any]) -> dict[str, Any]:
        weekdays = raw.get("weekdays", list(range(7)))
        weekdays = [int(x) for x in weekdays if 0 <= int(x) <= 6]
        if not weekdays:
            weekdays = list(range(7))

        return {
            "id": str(raw.get("id") or uuid.uuid4().hex),
            "name": str(raw.get("name") or "Zeitplan"),
            "enabled": bool(raw.get("enabled", True)),
            "weekdays": weekdays,
            "start_type": str(raw.get("start_type") or "time"),
            "start_time": str(raw.get("start_time") or "08:00"),
            "start_offset_min": int(raw.get("start_offset_min") or 0),
            "end_type": str(raw.get("end_type") or "time"),
            "end_time": str(raw.get("end_time") or "10:00"),
            "end_offset_min": int(raw.get("end_offset_min") or 0),
        }

    def _normalize_device(self, raw: dict[str, Any]) -> dict[str, Any]:
        entity_id = str(raw.get("entity_id") or "")
        domain = entity_id.split(".", 1)[0] if "." in entity_id else ""
        presets: list[int] = []
        for value in raw.get("timer_presets") or [30, 60, 90]:
            try:
                presets.append(max(1, min(10080, int(value))))
            except (TypeError, ValueError):
                continue
        defaults = [30, 60, 90]
        presets = presets[:3]
        while len(presets) < 3:
            presets.append(defaults[len(presets)])
        return {
            "id": str(raw.get("id") or uuid.uuid4().hex),
            "name": str(raw.get("name") or entity_id or "Gerät"),
            "entity_id": entity_id,
            "enabled": bool(raw.get("enabled", True)),
            "domain": domain,
            "climate_mode": str(raw.get("climate_mode") or "heat_cool"),
            "target_temp": (
                None if raw.get("target_temp") in (None, "") else float(raw.get("target_temp"))
            ),
            "cover_on_position": max(0, min(100, int(raw.get("cover_on_position", 100)))),
            "cover_off_position": max(0, min(100, int(raw.get("cover_off_position", 0)))),
            "timer_presets": presets,
            "timer_until": float(raw.get("timer_until") or 0),
            "timer_started": float(raw.get("timer_started") or 0),
            "schedules": [self._normalize_schedule(x) for x in raw.get("schedules", [])],
            "last_error": str(raw.get("last_error") or ""),
            "last_action": str(raw.get("last_action") or ""),
            "last_action_ts": float(raw.get("last_action_ts") or 0),
        }

    def _find_device(self, device_id: str) -> dict[str, Any] | None:
        return next((d for d in self.devices if d["id"] == device_id), None)

    def _find_schedule(self, device: dict[str, Any], schedule_id: str) -> dict[str, Any] | None:
        return next((s for s in device["schedules"] if s["id"] == schedule_id), None)

    async def async_set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        await self._save()
        self._notify()
        await self.async_evaluate()

    async def async_add_device(self, data: dict[str, Any]) -> dict[str, Any]:
        entity_id = str(data["entity_id"])
        domain = entity_id.split(".", 1)[0]
        if domain not in SUPPORTED_DOMAINS:
            raise ValueError(f"Nicht unterstützte Domain: {domain}")

        initial_schedule = data.get("initial_schedule")
        schedules = []
        if isinstance(initial_schedule, dict):
            schedules.append(self._normalize_schedule(initial_schedule))

        device = self._normalize_device(
            {
                "id": uuid.uuid4().hex,
                "name": data.get("name") or entity_id,
                "entity_id": entity_id,
                "enabled": data.get("enabled", True),
                "climate_mode": data.get("climate_mode", "heat_cool"),
                "target_temp": data.get("target_temp"),
                "cover_on_position": data.get("cover_on_position", 100),
                "cover_off_position": data.get("cover_off_position", 0),
                "timer_presets": data.get("timer_presets", [30, 60, 90]),
                "schedules": schedules,
            }
        )
        self.devices.append(device)
        await self._save()
        self._notify()
        return device

    async def async_update_device(self, device_id: str, data: dict[str, Any]) -> None:
        device = self._find_device(device_id)
        if not device:
            raise ValueError(f"Unbekanntes Gerät: {device_id}")

        for key in (
            "name",
            "entity_id",
            "enabled",
            "climate_mode",
            "target_temp",
            "cover_on_position",
            "cover_off_position",
            "timer_presets",
        ):
            if key in data:
                device[key] = data[key]

        normalized = self._normalize_device(device)
        device.clear()
        device.update(normalized)
        await self._save()
        self._notify()
        await self.async_evaluate()

    async def async_remove_device(self, device_id: str) -> None:
        device = self._find_device(device_id)
        if not device:
            return
        self.devices.remove(device)
        await self._save()
        self._notify()

    async def async_set_device_enabled(self, device_id: str, enabled: bool) -> None:
        device = self._find_device(device_id)
        if not device:
            raise ValueError(f"Unbekanntes Gerät: {device_id}")
        device["enabled"] = bool(enabled)
        await self._save()
        self._notify()
        await self.async_evaluate()

    async def async_add_schedule(self, device_id: str, data: dict[str, Any]) -> dict[str, Any]:
        device = self._find_device(device_id)
        if not device:
            raise ValueError(f"Unbekanntes Gerät: {device_id}")
        schedule = self._normalize_schedule({"id": uuid.uuid4().hex, **data})
        device["schedules"].append(schedule)
        await self._save()
        self._notify()
        await self.async_evaluate()
        return schedule

    async def async_update_schedule(
        self, device_id: str, schedule_id: str, data: dict[str, Any]
    ) -> None:
        device = self._find_device(device_id)
        if not device:
            raise ValueError(f"Unbekanntes Gerät: {device_id}")
        schedule = self._find_schedule(device, schedule_id)
        if not schedule:
            raise ValueError(f"Unbekannter Zeitplan: {schedule_id}")

        for key in (
            "name",
            "enabled",
            "weekdays",
            "start_type",
            "start_time",
            "start_offset_min",
            "end_type",
            "end_time",
            "end_offset_min",
        ):
            if key in data:
                schedule[key] = data[key]

        normalized = self._normalize_schedule(schedule)
        schedule.clear()
        schedule.update(normalized)
        await self._save()
        self._notify()
        await self.async_evaluate()

    async def async_remove_schedule(self, device_id: str, schedule_id: str) -> None:
        device = self._find_device(device_id)
        if not device:
            return
        schedule = self._find_schedule(device, schedule_id)
        if not schedule:
            return
        device["schedules"].remove(schedule)
        await self._save()
        self._notify()
        await self.async_evaluate()

    async def async_start_timer(self, device_id: str, duration_min: int) -> None:
        device = self._find_device(device_id)
        if not device:
            raise ValueError(f"Unbekanntes Gerät: {device_id}")
        duration_min = max(1, int(duration_min))
        now = time.time()
        device["timer_started"] = now
        device["timer_until"] = now + duration_min * 60
        await self._save()
        await self._turn_on(device)
        self._notify()

    async def async_cancel_timer(self, device_id: str, turn_off: bool = False) -> None:
        device = self._find_device(device_id)
        if not device:
            return
        device["timer_started"] = 0
        device["timer_until"] = 0
        await self._save()
        if turn_off:
            await self._turn_off(device)
        self._notify()

    def _resolve_event(self, event_type: str, time_value: str, offset_min: int, day: date) -> datetime:
        if event_type == "time":
            try:
                hour, minute = [int(x) for x in time_value.split(":", 1)]
            except Exception:
                hour, minute = 0, 0
            local = datetime(day.year, day.month, day.day, hour, minute, tzinfo=dt_util.DEFAULT_TIME_ZONE)
            return local + timedelta(minutes=offset_min)

        event = "sunrise" if event_type == "sunrise" else "sunset"
        event_dt = get_astral_event_date(self.hass, event, day)
        if event_dt is None:
            local = datetime(day.year, day.month, day.day, 12, 0, tzinfo=dt_util.DEFAULT_TIME_ZONE)
            return local + timedelta(minutes=offset_min)
        return dt_util.as_local(event_dt) + timedelta(minutes=offset_min)

    def _schedule_window(self, schedule: dict[str, Any], anchor: date) -> tuple[datetime, datetime]:
        start = self._resolve_event(
            schedule["start_type"],
            schedule["start_time"],
            schedule["start_offset_min"],
            anchor,
        )
        end = self._resolve_event(
            schedule["end_type"],
            schedule["end_time"],
            schedule["end_offset_min"],
            anchor,
        )
        if end <= start:
            next_day = anchor + timedelta(days=1)
            end = self._resolve_event(
                schedule["end_type"],
                schedule["end_time"],
                schedule["end_offset_min"],
                next_day,
            )
        return start, end

    def _is_schedule_active(self, schedule: dict[str, Any], now: datetime) -> bool:
        if not schedule.get("enabled", True):
            return False
        for anchor in (now.date(), now.date() - timedelta(days=1)):
            if anchor.weekday() not in schedule["weekdays"]:
                continue
            start, end = self._schedule_window(schedule, anchor)
            if start <= now < end:
                return True
        return False

    def _is_on(self, entity_id: str) -> bool:
        state = self.hass.states.get(entity_id)
        if state is None:
            return False
        value = str(state.state).lower()
        if entity_id.startswith("cover."):
            position = state.attributes.get("current_position")
            if position is not None:
                try:
                    return int(position) > 0
                except (TypeError, ValueError):
                    pass
        return value not in {"off", "closed", "idle", "unknown", "unavailable"}

    async def _turn_on(self, device: dict[str, Any]) -> None:
        entity_id = device["entity_id"]
        domain = device["domain"]
        try:
            if domain == "climate":
                mode = device.get("climate_mode") or "heat_cool"
                await self.hass.services.async_call(
                    "climate", "set_hvac_mode",
                    {"entity_id": entity_id, "hvac_mode": mode},
                    blocking=True,
                )
                if device.get("target_temp") is not None:
                    await self.hass.services.async_call(
                        "climate", "set_temperature",
                        {"entity_id": entity_id, "temperature": device["target_temp"]},
                        blocking=True,
                    )
            elif domain == "cover":
                await self.hass.services.async_call(
                    "cover", "set_cover_position",
                    {"entity_id": entity_id, "position": device["cover_on_position"]},
                    blocking=True,
                )
            else:
                await self.hass.services.async_call(
                    domain, "turn_on", {"entity_id": entity_id}, blocking=True
                )
            device["last_error"] = ""
            device["last_action"] = "on"
            device["last_action_ts"] = time.time()
        except Exception as err:  # noqa: BLE001
            device["last_error"] = str(err)
            _LOGGER.exception("Fehler beim Einschalten von %s", entity_id)

    async def _turn_off(self, device: dict[str, Any]) -> None:
        entity_id = device["entity_id"]
        domain = device["domain"]
        try:
            if domain == "climate":
                await self.hass.services.async_call(
                    "climate", "set_hvac_mode",
                    {"entity_id": entity_id, "hvac_mode": "off"},
                    blocking=True,
                )
            elif domain == "cover":
                await self.hass.services.async_call(
                    "cover", "set_cover_position",
                    {"entity_id": entity_id, "position": device["cover_off_position"]},
                    blocking=True,
                )
            else:
                await self.hass.services.async_call(
                    domain, "turn_off", {"entity_id": entity_id}, blocking=True
                )
            device["last_error"] = ""
            device["last_action"] = "off"
            device["last_action_ts"] = time.time()
        except Exception as err:  # noqa: BLE001
            device["last_error"] = str(err)
            _LOGGER.exception("Fehler beim Ausschalten von %s", entity_id)

    def _next_action_for(self, device: dict[str, Any], now: datetime) -> dict[str, Any] | None:
        timer_until = float(device.get("timer_until") or 0)
        if timer_until > time.time():
            return {"action": "off", "at": datetime.fromtimestamp(timer_until, tz=dt_util.DEFAULT_TIME_ZONE).isoformat(), "source": "timer"}

        candidates: list[tuple[datetime, str]] = []
        for schedule in device["schedules"]:
            if not schedule.get("enabled", True):
                continue
            for delta in range(0, 8):
                anchor = now.date() + timedelta(days=delta)
                if anchor.weekday() not in schedule["weekdays"]:
                    continue
                start, end = self._schedule_window(schedule, anchor)
                if start > now:
                    candidates.append((start, "on"))
                if end > now:
                    candidates.append((end, "off"))
        if not candidates:
            return None
        when, action = min(candidates, key=lambda x: x[0])
        return {"action": action, "at": when.isoformat(), "source": "schedule"}

    @property
    def state_attributes(self) -> dict[str, Any]:
        now = dt_util.now()
        result = []
        for device in self.devices:
            item = dict(device)
            item["is_on"] = self._is_on(device["entity_id"])
            item["timer_remaining_s"] = max(0, int((device.get("timer_until") or 0) - time.time()))
            item["next_action"] = self._next_action_for(device, now)
            result.append(item)
        return {
            "entry_id": self.entry_id,
            "enabled": self.enabled,
            "language": self.language,
            "scan_interval": self.scan_interval,
            "devices": result,
            "supported_domains": SUPPORTED_DOMAINS,
            "version": "0.2.1",
        }

    async def _async_tick(self, _now) -> None:
        await self.async_evaluate()

    async def async_evaluate(self) -> None:
        async with self._lock:
            changed = False
            now = dt_util.now()
            now_ts = time.time()

            for device in self.devices:
                if not self.enabled or not device.get("enabled", True):
                    continue

                timer_until = float(device.get("timer_until") or 0)
                if timer_until and timer_until <= now_ts:
                    device["timer_until"] = 0
                    device["timer_started"] = 0
                    await self._turn_off(device)
                    changed = True
                    continue

                timer_active = timer_until > now_ts
                schedule_active = any(
                    self._is_schedule_active(schedule, now)
                    for schedule in device["schedules"]
                )
                desired_on = timer_active or schedule_active
                current_on = self._is_on(device["entity_id"])

                if desired_on and not current_on:
                    await self._turn_on(device)
                    changed = True
                elif not desired_on and current_on and device["schedules"]:
                    await self._turn_off(device)
                    changed = True

            if changed:
                await self._save()
            self._notify()
