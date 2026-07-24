"""Switch platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAP_AI_ADAPTIVE,
    CONF_MAC,
    DOMAIN,
    KEY_AI_ADAPTIVE,
    KEY_VALVE,
    MANUFACTURER,
    MODEL,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast switches."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    entities: list[SwitchEntity] = [
        AquafeastValveSwitch(entry, api, coordinator),
    ]

    if coordinator.has_capability(CAP_AI_ADAPTIVE):
        entities.append(AquafeastAiAdaptiveSwitch(entry, api, coordinator))

    async_add_entities(entities)


class AquafeastBaseSwitch(CoordinatorEntity, SwitchEntity):
    """Base switch entity."""

    _attr_has_entity_name = True

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the switch."""
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


class AquafeastValveSwitch(AquafeastBaseSwitch):
    """Valve switch with real state feedback."""

    _attr_name = "water valve"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the valve switch."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_valve"

    @property
    def is_on(self) -> bool | None:
        """Return valve state."""
        value = self.coordinator.get_value(KEY_VALVE)
        if value is None:
            return None
        return str(value) == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Open valve."""
        await self._api.async_set_valve(True)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Close valve."""
        await self._api.async_set_valve(False)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastAiAdaptiveSwitch(AquafeastBaseSwitch):
    """AI adaptive mode switch."""

    _attr_name = "ai adaptive"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the AI adaptive switch."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ai_adaptive"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and self.coordinator.has_capability(CAP_AI_ADAPTIVE)

    @property
    def is_on(self) -> bool | None:
        """Return AI adaptive state."""
        value = self.coordinator.get_value(KEY_AI_ADAPTIVE)
        if value is None:
            return None
        return str(value) == "1"

    async def async_turn_on(self, **kwargs) -> None:
        """Enable AI adaptive."""
        await self._api.async_set_ai_adaptive(True)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Disable AI adaptive."""
        await self._api.async_set_ai_adaptive(False)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
