"""Select platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, KEY_MODE, MANUFACTURER, MODEL


MODE_MAP = {
    "Unprotect Mode 1": 0x01,
    "Unprotect Mode 2": 0x02,
    "Unprotect Mode 3": 0x03,
    "Unprotect Mode 4": 0x04,
    "Unprotect Mode 5": 0x05,
    "Unprotect Mode 6": 0x06,
    "Protect Mode 1": 0x11,
    "Protect Mode 2": 0x12,
    "Protect Mode 3": 0x13,
    "Protect Mode 4": 0x14,
    "Protect Mode 5": 0x15,
    "Protect Mode 6": 0x16,
}

MODE_STATUS_MAP = {value: key for key, value in MODE_MAP.items()}


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
        [AquafeastOperationModeSelect(entry, api, coordinator)]
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
        code = self.coordinator.get_int(KEY_MODE)
        if code is None:
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
