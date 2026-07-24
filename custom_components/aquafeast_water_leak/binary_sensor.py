"""Binary sensor platform for Aquafeast Water Leak."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAP_FILTER,
    CONF_MAC,
    DOMAIN,
    KEY_FAULT,
    KEY_FLUSH_STATUS,
    MANUFACTURER,
    MODEL,
)


def _fault_value(coordinator) -> int:
    """Return raw fault value."""
    raw = coordinator.get_int(KEY_FAULT)
    return raw if raw is not None else 0


def _is_fault_bit_set(coordinator, bit: int) -> bool:
    """Return True if bit is set in fault mask."""
    value = _fault_value(coordinator)
    return bool(value & (1 << bit))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    entities: list[BinarySensorEntity] = [
        AquafeastLeakWarningBinarySensor(coordinator, entry),
        AquafeastLeakDetectedBinarySensor(coordinator, entry),
        AquafeastEmptyPipeFaultBinarySensor(coordinator, entry),
        AquafeastWaterValveFaultBinarySensor(coordinator, entry),
    ]

    if coordinator.has_capability(CAP_FILTER):
        entities.append(AquafeastFlushRunningBinarySensor(coordinator, entry))

    async_add_entities(entities)


class AquafeastBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Base binary sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=entry.title,
            serial_number=entry.data.get(CONF_MAC),
        )


class AquafeastBaseFaultBinarySensor(AquafeastBaseBinarySensor):
    """Base fault binary sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.PROBLEM


class AquafeastLeakWarningBinarySensor(AquafeastBaseFaultBinarySensor):
    """Leak warning binary sensor."""

    _attr_name = "leak warning"
    _attr_icon = "mdi:water-alert-outline"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize leak warning binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_leak_warning"

    @property
    def is_on(self) -> bool:
        """Return true if leak warning is active."""
        return (
            _is_fault_bit_set(self.coordinator, 12)
            or _is_fault_bit_set(self.coordinator, 13)
            or _is_fault_bit_set(self.coordinator, 14)
        )


class AquafeastLeakDetectedBinarySensor(AquafeastBaseFaultBinarySensor):
    """Leak detected binary sensor."""

    _attr_name = "leak detected"
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize leak detected binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_leak_detected"

    @property
    def is_on(self) -> bool:
        """Return true if leak is detected."""
        return _is_fault_bit_set(self.coordinator, 15)


class AquafeastEmptyPipeFaultBinarySensor(AquafeastBaseFaultBinarySensor):
    """Empty pipe fault binary sensor."""

    _attr_name = "empty pipe fault"
    _attr_icon = "mdi:pipe-disconnected"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize empty pipe fault binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_empty_pipe_fault"

    @property
    def is_on(self) -> bool:
        """Return true if empty pipe fault is active."""
        return _is_fault_bit_set(self.coordinator, 1)


class AquafeastWaterValveFaultBinarySensor(AquafeastBaseFaultBinarySensor):
    """Water valve fault binary sensor."""

    _attr_name = "water valve fault"
    _attr_icon = "mdi:valve"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize water valve fault binary sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_water_valve_fault"

    @property
    def is_on(self) -> bool:
        """Return true if water valve fault is active."""
        return _is_fault_bit_set(self.coordinator, 6)


class AquafeastFlushRunningBinarySensor(AquafeastBaseBinarySensor):
    """Flush running sensor for filter model."""

    _attr_name = "flush impurity running"
    _attr_icon = "mdi:water-sync"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize flush running sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_flush_impurity_running"

    @property
    def available(self) -> bool:
        """Return availability."""
        return super().available and self.coordinator.has_capability(CAP_FILTER)

    @property
    def is_on(self) -> bool:
        """Return true if flushing is currently running."""
        value = self.coordinator.get_value(KEY_FLUSH_STATUS)
        return str(value) == "1"
