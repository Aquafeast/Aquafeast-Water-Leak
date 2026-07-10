"""Binary sensor platform for Aquafeast Water Leak."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MAC, DOMAIN, MANUFACTURER, MODEL


def _fault_value(data: dict) -> int:
    raw = data.get("dataF0", 0)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def _is_fault_bit_set(data: dict, bit: int) -> bool:
    value = _fault_value(data)
    return bool(value & (1 << bit))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities(
        [
            AquafeastLeakWarningBinarySensor(coordinator, entry),
            AquafeastLeakDetectedBinarySensor(coordinator, entry),
            AquafeastEmptyPipeFaultBinarySensor(coordinator, entry),
            AquafeastWaterValveFaultBinarySensor(coordinator, entry),
        ]
    )


class AquafeastBaseFaultBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base fault binary sensor."""

    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
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


class AquafeastLeakWarningBinarySensor(AquafeastBaseFaultBinarySensor):
    """Leak warning binary sensor."""

    _attr_name = "leak warning"
    _attr_icon = "mdi:water-alert-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_leak_warning"

    @property
    def is_on(self) -> bool:
        return (
            _is_fault_bit_set(self._data, 12)
            or _is_fault_bit_set(self._data, 13)
            or _is_fault_bit_set(self._data, 14)
        )


class AquafeastLeakDetectedBinarySensor(AquafeastBaseFaultBinarySensor):
    """Leak detected binary sensor."""

    _attr_name = "leak detected"
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_leak_detected"

    @property
    def is_on(self) -> bool:
        return _is_fault_bit_set(self._data, 15)


class AquafeastEmptyPipeFaultBinarySensor(AquafeastBaseFaultBinarySensor):
    """Empty pipe fault binary sensor."""

    _attr_name = "empty pipe fault"
    _attr_icon = "mdi:pipe-disconnected"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_empty_pipe_fault"

    @property
    def is_on(self) -> bool:
        return _is_fault_bit_set(self._data, 1)


class AquafeastWaterValveFaultBinarySensor(AquafeastBaseFaultBinarySensor):
    """Water valve fault binary sensor."""

    _attr_name = "water valve fault"
    _attr_icon = "mdi:valve"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_water_valve_fault"

    @property
    def is_on(self) -> bool:
        return _is_fault_bit_set(self._data, 6)
