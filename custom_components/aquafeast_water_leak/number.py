"""Number platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, MANUFACTURER, MODEL


def _is_imperial(data: dict) -> bool:
    return str(data.get("data09")) == "1"


def _mode_code(data: dict) -> int | None:
    raw = data.get("data02")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _is_unprotect(data: dict) -> bool:
    return _mode_code(data) == 2


def _is_professional_mode(data: dict) -> bool:
    return _mode_code(data) in (20, 21, 22)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast numbers."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    async_add_entities(
        [
            AquafeastWarningTimeNumber(entry, api, coordinator),
            AquafeastWarningWaterNumber(entry, api, coordinator),
            AquafeastWarningMinimumFlowNumber(entry, api, coordinator),
        ]
    )


class AquafeastBaseNumber(CoordinatorEntity, NumberEntity):
    """Base Aquafeast number entity."""

    _attr_has_entity_name = True

    def __init__(self, entry, api, coordinator) -> None:
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

    @property
    def _data(self) -> dict:
        return self.coordinator.data.get("data", {})

    @property
    def _current_mode(self) -> int | None:
        return _mode_code(self._data)


class AquafeastWarningTimeNumber(AquafeastBaseNumber):
    """Warning time number entity for professional modes."""

    _attr_name = "warning time"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warning_time"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and _is_professional_mode(self._data)

    @property
    def native_unit_of_measurement(self):
        return "h"

    @property
    def native_min_value(self) -> float:
        return 1.0

    @property
    def native_max_value(self) -> float:
        return 3.0

    @property
    def native_step(self) -> float:
        return 0.1

    @property
    def native_value(self) -> float | None:
        """Return warning time in hours."""
        raw_value = self._data.get("data0E")

        if raw_value in (None, "", "-"):
            return None

        try:
            raw = float(raw_value)
        except (TypeError, ValueError):
            return None

        return round(raw / 3600, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning time in hours."""
        mode = self._current_mode
        if mode not in (20, 21, 22):
            return

        current_flow_raw = self._data.get("data0D", "0")
        try:
            flow_set = int(float(current_flow_raw))
        except (TypeError, ValueError):
            flow_set = 0

        hour_set = int(round(value * 3600))

        await self._api.async_set_mode(mode, flow_set=flow_set, hour_set=hour_set)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastWarningWaterNumber(AquafeastBaseNumber):
    """Warning water number entity for professional modes."""

    _attr_name = "warning water"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_warning_water"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and _is_professional_mode(self._data)

    @property
    def native_unit_of_measurement(self):
        return "gal" if _is_imperial(self._data) else "m³"

    @property
    def native_min_value(self) -> float:
        return 50.0 if _is_imperial(self._data) else 0.1

    @property
    def native_max_value(self) -> float:
        return 1500.0 if _is_imperial(self._data) else 5.0

    @property
    def native_step(self) -> float:
        return 50.0 if _is_imperial(self._data) else 0.1

    @property
    def native_value(self) -> float | None:
        """Return warning water."""
        raw_value = self._data.get("data0D")

        if raw_value in (None, "", "-"):
            return None

        try:
            raw = float(raw_value)
        except (TypeError, ValueError):
            return None

        if _is_imperial(self._data):
            return round(raw / 8, 0)

        return round(raw / 1000, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning water."""
        mode = self._current_mode
        if mode not in (20, 21, 22):
            return

        current_hour_raw = self._data.get("data0E", "0")
        try:
            hour_set = int(float(current_hour_raw))
        except (TypeError, ValueError):
            hour_set = 0

        if _is_imperial(self._data):
            flow_set = int(round(value * 8))
        else:
            flow_set = int(round(value * 1000))

        await self._api.async_set_mode(mode, flow_set=flow_set, hour_set=hour_set)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastWarningMinimumFlowNumber(AquafeastBaseNumber):
    """Warning minimum flow number entity."""

    _attr_name = "warning minimum flow"
    _attr_mode = "slider"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_warning_minimum_flow"

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and not _is_unprotect(self._data)

    @property
    def native_unit_of_measurement(self):
        return "GPM" if _is_imperial(self._data) else "L/hr"

    @property
    def native_min_value(self) -> float:
        return 0.01 if _is_imperial(self._data) else 1.0

    @property
    def native_max_value(self) -> float:
        return 0.20 if _is_imperial(self._data) else 20.0

    @property
    def native_step(self) -> float:
        return 0.01 if _is_imperial(self._data) else 0.5

    @property
    def native_value(self) -> float | None:
        """Return current warning minimum flow."""
        raw_value = self._data.get("data22")

        if raw_value in (None, "", "-"):
            return None

        try:
            raw = float(raw_value)
        except (TypeError, ValueError):
            return None

        if _is_imperial(self._data):
            return round(raw / 1000, 2)

        return round(raw / 10, 1)

    async def async_set_native_value(self, value: float) -> None:
        """Set warning minimum flow."""
        await self._api.async_set_warning_minimum_flow(value)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
