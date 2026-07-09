"""Select platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, MANUFACTURER, MODEL

MODE_MAP = {
    "UnProtect": 1,
    "Mode 1": 17,
    "Mode 2": 18,
    "Mode 3": 19,
    "Mode 4": 20,
    "Mode 5": 21,
    "Mode 6": 22,
}

MODE_STATUS_MAP = {
    2: "UnProtect",
    17: "Mode 1",
    18: "Mode 2",
    19: "Mode 3",
    20: "Mode 4",
    21: "Mode 5",
    22: "Mode 6",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast selects."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    async_add_entities(
        [
            AquafeastOperationModeSelect(entry, api, coordinator),
        ]
    )


class AquafeastOperationModeSelect(CoordinatorEntity, SelectEntity):
    """Operation mode select entity."""

    _attr_has_entity_name = True
    _attr_name = "operation mode"
    _attr_options = list(MODE_MAP.keys())

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self._attr_unique_id = f"{entry.entry_id}_operation_mode"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
            serial_number=entry.data.get(CONF_MAC),
        )

    @property
    def current_option(self) -> str | None:
        """Return current operation mode."""
        data = self.coordinator.data.get("data", {})
        raw_value = data.get("data02")

        if raw_value is None:
            return None

        try:
            code = int(raw_value)
        except (TypeError, ValueError):
            return None

        return MODE_STATUS_MAP.get(code)

    async def async_select_option(self, option: str) -> None:
        """Set operation mode."""
        mode_code = MODE_MAP.get(option)
        if mode_code is None:
            return

        await self._api.async_set_mode(mode_code, flow_set=0)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
