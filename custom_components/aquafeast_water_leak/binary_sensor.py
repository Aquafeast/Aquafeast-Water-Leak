"""Binary sensor platform for Aquafeast Water Leak."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            AquafeastProtectionBinarySensor(coordinator, entry),
        ]
    )


class AquafeastProtectionBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of Aquafeast protection state."""

    _attr_has_entity_name = True
    _attr_name = "protection enabled"
    _attr_icon = "mdi:shield-check"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_protection_enabled"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
            serial_number=entry.data.get(CONF_MAC),
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if protection is enabled."""
        data = self.coordinator.data.get("data", {})
        value = data.get("data01")

        if value is None:
            return None

        return str(value) == "1"
