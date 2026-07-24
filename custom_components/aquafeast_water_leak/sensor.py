"""Sensor platform for Aquafeast Water Leak."""

from __future__ import annotations

import json

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CAP_FILTER,
    CONF_MAC,
    DOMAIN,
    KEY_BATTERY_LEVEL,
    KEY_FAULT,
    KEY_FLOW,
    KEY_MODE,
    KEY_NEXT_FLUSH_HOURS,
    KEY_POWER_STATUS,
    KEY_PREVIOUS_MODE,
    KEY_TEMPERATURE,
    KEY_TOTAL_WATER_HIGH,
    KEY_TOTAL_WATER_LOW,
    KEY_UNIT_SYSTEM,
    MANUFACTURER,
    MODEL,
)

MODE_LABELS = {
    0x01: "Unprotect Mode 1",
    0x02: "Unprotect Mode 2",
    0x03: "Unprotect Mode 3",
    0x04: "Unprotect Mode 4",
    0x05: "Unprotect Mode 5",
    0x06: "Unprotect Mode 6",
    0x11: "Protect Mode 1",
    0x12: "Protect Mode 2",
    0x13: "Protect Mode 3",
    0x14: "Protect Mode 4",
    0x15: "Protect Mode 5",
    0x16: "Protect Mode 6",
}


def _is_imperial(coordinator) -> bool:
    return str(coordinator.get_value(KEY_UNIT_SYSTEM)) == "1"


def _parse_temperature_raw(raw) -> float | None:
    if raw in (None, "", "-", "--"):
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None

    whole = value // 256
    fraction = value % 256
    return round(whole + (fraction / 100), 1)


def _mode_name(code: int | None) -> str | None:
    if code is None:
        return None
    return MODE_LABELS.get(code)


def _fault_description(raw) -> str:
    if raw in (None, "", "-", "--"):
        return "Unknown"

    try:
        value = int(raw)
    except (TypeError, ValueError):
        return "Unknown"

    if value == 0:
        return "Normal"

    faults: list[str] = []
    bit_labels = {
        0: "Power fault / low battery",
        1: "Empty pipe fault",
        2: "Reverse flow fault",
        3: "Overrange fault",
        4: "Water temperature fault",
        5: "EE alarm",
        6: "Water valve fault",
        12: "Leak warning",
        13: "Leak warning",
        14: "Leak warning",
        15: "Leak detected",
    }

    for bit, label in bit_labels.items():
        if value & (1 << bit):
            faults.append(label)

    if not faults:
        return f"Fault code {value}"

    return ", ".join(faults)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Aquafeast sensors."""
    stored = hass.data[DOMAIN][entry.entry_id]
    api = stored["api"]
    coordinator = stored["coordinator"]

    entities: list[SensorEntity] = [
        AquafeastMeasurementSystemSensor(entry, api, coordinator),
        AquafeastProtectionStateSensor(entry, api, coordinator),
        AquafeastWaterTemperatureSensor(entry, api, coordinator),
        AquafeastWaterFlowRateSensor(entry, api, coordinator),
        AquafeastTotalWaterSensor(entry, api, coordinator),
        AquafeastLastModeSensor(entry, api, coordinator),
        AquafeastFaultStatusSensor(entry, api, coordinator),
        AquafeastFaultCodeSensor(entry, api, coordinator),
        AquafeastRawStatusSensor(entry, api, coordinator),
        AquafeastBatteryLevelSensor(entry, api, coordinator),
        AquafeastPowerSupplyStatusSensor(entry, api, coordinator),
    ]

    if coordinator.has_capability(CAP_FILTER):
        entities.append(AquafeastNextFlushHoursSensor(entry, api, coordinator))

    async_add_entities(entities)


class AquafeastBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor."""

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


class AquafeastMeasurementSystemSensor(AquafeastBaseSensor):
    _attr_name = "measurement system"
    _attr_icon = "mdi:ruler"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_measurement_system"

    @property
    def native_value(self) -> str:
        return "Imperial" if _is_imperial(self.coordinator) else "Metric"


class AquafeastProtectionStateSensor(AquafeastBaseSensor):
    _attr_name = "protection state"
    _attr_icon = "mdi:shield-check"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_protection_state"

    @property
    def native_value(self) -> str:
        code = self.coordinator.get_int(KEY_MODE)
        if code is None:
            return "Unknown"
        if 0x01 <= code <= 0x06:
            return "Unprotected"
        if 0x11 <= code <= 0x16:
            return "Protected"
        return "Unknown"


class AquafeastWaterTemperatureSensor(AquafeastBaseSensor):
    _attr_name = "water temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_temperature"

    @property
    def native_unit_of_measurement(self):
        return (
            UnitOfTemperature.FAHRENHEIT
            if _is_imperial(self.coordinator)
            else UnitOfTemperature.CELSIUS
        )

    @property
    def native_value(self):
        return _parse_temperature_raw(self.coordinator.get_value(KEY_TEMPERATURE))


class AquafeastWaterFlowRateSensor(AquafeastBaseSensor):
    _attr_name = "water flow rate"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_flow_rate"

    @property
    def native_unit_of_measurement(self):
        return "GPM" if _is_imperial(self.coordinator) else "L/hr"

    @property
    def native_value(self):
        raw = self.coordinator.get_int(KEY_FLOW)
        if raw is None:
            return None
        if _is_imperial(self.coordinator):
            return round((raw / 10) / 227.1247, 2)
        return round(raw / 10, 1)


class AquafeastTotalWaterSensor(AquafeastBaseSensor):
    _attr_name = "total water"
    _attr_icon = "mdi:water"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_total_water"

    @property
    def native_unit_of_measurement(self):
        return "gal" if _is_imperial(self.coordinator) else "m³"

    @property
    def native_value(self):
        low = self.coordinator.get_int(KEY_TOTAL_WATER_LOW)
        high = self.coordinator.get_int(KEY_TOTAL_WATER_HIGH)

        if low is None and high is None:
            return None

        low = low or 0
        high = high or 0

        metric_value = high * 100 + (low / 100)

        if _is_imperial(self.coordinator):
            return round(metric_value * 264.172, 1)

        return round(metric_value, 2)


class AquafeastBatteryLevelSensor(AquafeastBaseSensor):
    _attr_name = "battery level"
    _attr_icon = "mdi:battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_level"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.get_value(KEY_BATTERY_LEVEL) not in (
            None,
            "",
            "-",
            "--",
        )

    @property
    def native_value(self) -> str:
        raw_value = self.coordinator.get_value(KEY_BATTERY_LEVEL)
        mapping = {
            "0": "Critical",
            "1": "Low",
            "2": "Medium",
            "3": "High",
            "4": "Full",
        }
        return mapping.get(str(raw_value), "Unknown")


class AquafeastPowerSupplyStatusSensor(AquafeastBaseSensor):
    _attr_name = "power supply status"
    _attr_icon = "mdi:power-plug-battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_power_supply_status"

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.get_value(KEY_POWER_STATUS) not in (
            None,
            "",
            "-",
            "--",
        )

    @property
    def native_value(self) -> str:
        raw_value = self.coordinator.get_value(KEY_POWER_STATUS)
        mapping = {
            "0": "Battery only",
            "1": "Charging",
            "2": "External power / full",
        }
        return mapping.get(str(raw_value), "Unknown")


class AquafeastLastModeSensor(AquafeastBaseSensor):
    _attr_name = "last mode"
    _attr_icon = "mdi:history"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_mode"

    @property
    def native_value(self) -> str:
        code = self.coordinator.get_int(KEY_PREVIOUS_MODE)
        return _mode_name(code) or "Unknown"


class AquafeastNextFlushHoursSensor(AquafeastBaseSensor):
    _attr_name = "next flush in"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_next_flush_in"

    @property
    def available(self) -> bool:
        return (
            super().available
            and self.coordinator.has_capability(CAP_FILTER)
            and self.coordinator.get_value(KEY_NEXT_FLUSH_HOURS) not in (None, "", "-", "--")
        )

    @property
    def native_unit_of_measurement(self):
        return "h"

    @property
    def native_value(self):
        return self.coordinator.get_int(KEY_NEXT_FLUSH_HOURS)


class AquafeastFaultStatusSensor(AquafeastBaseSensor):
    _attr_name = "fault status"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fault_status"

    @property
    def native_value(self) -> str:
        return _fault_description(self.coordinator.get_value(KEY_FAULT))


class AquafeastFaultCodeSensor(AquafeastBaseSensor):
    _attr_name = "fault code"
    _attr_icon = "mdi:numeric"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fault_code"

    @property
    def native_value(self) -> str:
        raw_value = self.coordinator.get_value(KEY_FAULT)
        return str(raw_value) if raw_value is not None else "Unknown"


class AquafeastRawStatusSensor(AquafeastBaseSensor):
    _attr_name = "raw status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_raw_status"

    @property
    def native_value(self) -> str:
        return json.dumps(self.coordinator.data, ensure_ascii=False, sort_keys=True)
