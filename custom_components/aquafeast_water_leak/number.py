"""Number platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAP_FILTER,
    CONF_MAC,
    DOMAIN,
    KEY_FLUSH_DURATION,
    KEY_FLUSH_PERIOD,
    KEY_MODE,
    KEY_MODE4_HOURS,
    KEY_MODE4_WARNING_FLOW,
    KEY_MODE5_HOURS,
    KEY_MODE5_WARNING_FLOW,
    KEY_MODE6_HOURS,
    KEY_MODE6_WARNING_FLOW,
    KEY_WARNING_MIN_FLOW,
    MANUFACTURER,
    MODEL,
)


def _mode_code(coordinator) -> int | None:
    """Return current mode code."""
    return coordinator.get_int(KEY_MODE)


def _base_mode(coordinator) -> int | None:
    """Normalize mode 0x11..0x16 to base 1..6."""
    mode = _mode_code(coordinator)
    if mode is None:
        return None
    if 0x11 <= mode <= 0x16:
        return mode - 0x10
    return mode


def _is_professional_mode(coordinator) -> bool:
    """Return True for mode 4/5/6."""
    return _base_mode(coordinator) in (4, 5, 6)


def _warning_time_key(coordinator) -> str | None:
    """Return active warning time key."""
    return {
        4: KEY_MODE4_HOURS,
        5: KEY_MODE5_HOURS,
        6: KEY_MODE6_HOURS,
    }.get(_base_mode(coordinator))


def _warning_flow_key(coordinator) -> str | None:
    """Return active warning flow key."""
    return {
        4: KEY_MODE4_WARNING_FLOW,
        5: KEY_MODE5_WARNING_FLOW,
        6: KEY_MODE6_WARNING_FLOW,
    }.get(_base_mode(coordinator))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast numbers."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    entities: list[NumberEntity] = [
        AquafeastWarningTimeNumber(entry, api, coordinator),
        AquafeastWarningWaterNumber(entry, api, coordinator),
        AquafeastWarningMinimumFlowNumber(entry, api, coordinator),
    ]

    if coordinator.has_capability(CAP_FILTER):
        entities.extend(
            [
                AquafeastFlushPeriodNumber(entry, api, coordinator),
                AquafeastFlushDurationNumber(entry, api, coordinator),
            ]
        )

    async_add_entities(entities)


class AquafeastBaseNumber(CoordinatorEntity, NumberEntity):
    """Base number entity."""

    _attr_has_entity_name = True

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize base number."""
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
            serial_number=entry.data.get(CONF_MAC),
        )


class AquafeastWarningTimeNumber(AquafeastBaseNumber):
    """Warning time number for mode 4/5/6."""

    _attr_name = "warning time"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize warning time."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warning_time"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and _is_professional_mode(self.coordinator)

    @property
    def native_unit_of_measurement(self):
        """Return unit."""
        return "h"

    @property
    def native_min_value(self) -> float:
        """Return min."""
        return 0.1

    @property
    def native_max_value(self) -> float:
        """Return max."""
        return 24.0

    @property
    def native_step(self) -> float:
        """Return step."""
        return 0.1

    @property
    def native_value(self) -> float | None:
        """Return warning time in hours."""
        key = _warning_time_key(self.coordinator)
        if key is None:
            return None

        raw = self.coordinator.get_int(key)
        if raw is None:
            return None

        return round(raw / 3600, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning time."""
        mode = _mode_code(self.coordinator)
        flow_key = _warning_flow_key(self.coordinator)

        if mode is None or flow_key is None:
            return

        current_flow = self.coordinator.get_int(flow_key) or 0
        hour_set = int(round(value * 3600))

        await self._api.async_set_mode(mode, flow_set=current_flow, hour_set=hour_set)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastWarningWaterNumber(AquafeastBaseNumber):
    """Warning water number for mode 4/5/6."""

    _attr_name = "warning water"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize warning water."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warning_water"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and _is_professional_mode(self.coordinator)

    @property
    def native_unit_of_measurement(self):
        """Return unit."""
        return "m³"

    @property
    def native_min_value(self) -> float:
        """Return min."""
        return 0.1

    @property
    def native_max_value(self) -> float:
        """Return max."""
        return 5.0

    @property
    def native_step(self) -> float:
        """Return step."""
        return 0.1

    @property
    def native_value(self) -> float | None:
        """Return warning water in m³."""
        key = _warning_flow_key(self.coordinator)
        if key is None:
            return None

        raw = self.coordinator.get_int(key)
        if raw is None:
            return None

        return round(raw / 10, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning water."""
        mode = _mode_code(self.coordinator)
        time_key = _warning_time_key(self.coordinator)

        if mode is None or time_key is None:
            return

        current_hour = self.coordinator.get_int(time_key) or 0
        flow_set = int(round(value * 10))

        await self._api.async_set_mode(mode, flow_set=flow_set, hour_set=current_hour)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastWarningMinimumFlowNumber(AquafeastBaseNumber):
    """Warning minimum flow number."""

    _attr_name = "warning minimum flow"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize warning minimum flow."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warning_minimum_flow"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and self.coordinator.get_value(KEY_WARNING_MIN_FLOW) not in (
            None,
            "",
            "-",
            "--",
        )

    @property
    def native_unit_of_measurement(self):
        """Return unit."""
        return "L/hr"

    @property
    def native_min_value(self) -> float:
        """Return min."""
        return 1.0

    @property
    def native_max_value(self) -> float:
        """Return max."""
        return 20.0

    @property
    def native_step(self) -> float:
        """Return step."""
        return 0.5

    @property
    def native_value(self) -> float | None:
        """Return warning minimum flow."""
        return self.coordinator.get_scaled(KEY_WARNING_MIN_FLOW, 10)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning minimum flow."""
        await self._api.async_set_warning_minimum_flow(value)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastFlushPeriodNumber(AquafeastBaseNumber):
    """Flush impurity period."""

    _attr_name = "flush impurity period"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize flush period."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_flush_impurity_period"

    @property
    def available(self) -> bool:
        """Return availability."""
        return (
            super().available
            and self.coordinator.has_capability(CAP_FILTER)
            and self.coordinator.get_value(KEY_FLUSH_PERIOD) not in (None, "", "-", "--")
        )

    @property
    def native_unit_of_measurement(self):
        """Return unit."""
        return "d"

    @property
    def native_min_value(self) -> float:
        """Return min."""
        return 0

    @property
    def native_max_value(self) -> float:
        """Return max."""
        return 90

    @property
    def native_step(self) -> float:
        """Return step."""
        return 1

    @property
    def native_value(self) -> float | None:
        """Return flush period."""
        value = self.coordinator.get_int(KEY_FLUSH_PERIOD)
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set flush period."""
        await self._api.async_set_flush_period(int(value))
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastFlushDurationNumber(AquafeastBaseNumber):
    """Flush duration."""

    _attr_name = "flush duration"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize flush duration."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_flush_duration"

    @property
    def available(self) -> bool:
        """Return availability."""
        return (
            super().available
            and self.coordinator.has_capability(CAP_FILTER)
            and self.coordinator.get_value(KEY_FLUSH_DURATION) not in (None, "", "-", "--")
        )

    @property
    def native_unit_of_measurement(self):
        """Return unit."""
        return "s"

    @property
    def native_min_value(self) -> float:
        """Return min."""
        return 5

    @property
    def native_max_value(self) -> float:
        """Return max."""
        return 120

    @property
    def native_step(self) -> float:
        """Return step."""
        return 1

    @property
    def native_value(self) -> float | None:
        """Return flush duration."""
        value = self.coordinator.get_int(KEY_FLUSH_DURATION)
        return None if value is None else float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set flush duration."""
        await self._api.async_set_flush_duration(int(value))
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
