"""Button platform for Aquafeast Water Leak."""

from __future__ import annotations

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import CAP_FILTER, CONF_MAC, DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast buttons."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    entities: list[ButtonEntity] = [
        AquafeastSyncClockButton(entry, api, coordinator),
        AquafeastResetDeviceButton(entry, api, coordinator),
    ]

    if coordinator.has_capability(CAP_FILTER):
        entities.append(AquafeastManualFlushButton(entry, api, coordinator))

    async_add_entities(entities)


class AquafeastBaseButton(CoordinatorEntity, ButtonEntity):
    """Base button entity."""

    _attr_has_entity_name = True

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the base button."""
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


class AquafeastSyncClockButton(AquafeastBaseButton):
    """Sync device clock button."""

    _attr_name = "sync clock"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize sync clock button."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_sync_clock"

    async def async_press(self) -> None:
        """Sync device clock with Home Assistant time."""
        now = dt_util.now()
        await self._api.async_set_clock(now.hour, now.minute, now.second)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastManualFlushButton(AquafeastBaseButton):
    """Run immediate/manual flush."""

    _attr_name = "manual flush impurity"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:water-sync"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize manual flush button."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_manual_flush_impurity"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and self.coordinator.has_capability(CAP_FILTER)

    async def async_press(self) -> None:
        """Start immediate flush."""
        await self._api.async_manual_flush()
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()


class AquafeastResetDeviceButton(AquafeastBaseButton):
    """Reset device button."""

    _attr_name = "reset device"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:restart"

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize reset device button."""
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_reset_device"

    async def async_press(self) -> None:
        """Reset device."""
        await self._api.async_reset_device(0)
        await asyncio.sleep(2)
        await self.coordinator.async_request_refresh()
