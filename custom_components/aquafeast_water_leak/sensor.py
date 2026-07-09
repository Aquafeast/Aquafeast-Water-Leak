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

from .const import CONF_MAC, DOMAIN, MANUFACTURER, MODEL


def _measurement_system(data: dict) -> str:
    """Return measurement system from raw data."""
    return "imperial" if str(data.get("data09")) == "1" else "metric"


def _is_imperial(data: dict) -> bool:
    """Return True if device is using imperial units."""
    return _measurement_system(data) == "imperial"


def _parse_optional_number(raw):
    """Parse optional numeric value."""
    if raw in (None, "", "-", "--"):
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _parse_temperature_raw(raw):
    """Parse raw water temperature value."""
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
    """Return friendly mode name."""
    if code is None:
        return None

    mapping = {
        1: "UnProtect",
        2: "UnProtect",
        3: "UnProtect",
        4: "UnProtect",
        5: "UnProtect",
        6: "UnProtect",
        17: "Mode 1",
        18: "Mode 2",
        19: "Mode 3",
        20: "Mode 4",
        21: "Mode 5",
        22: "Mode 6",
    }
    return mapping.get(code)


def _parse_mode(raw) -> int | None:
    """Parse mode code."""
    if raw in (None, "", "-", "--"):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _fault_description(raw) -> str:
    """Return fault description from F0 bitmap."""
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

    async_add_entities(
        [
            AquafeastMeasurementSystemSensor(entry, api, coordinator),
            AquafeastProtectionStateSensor(entry, api, coordinator),
            AquafeastWaterTemperatureSensor(entry, api, coordinator),
            AquafeastWaterFlowRateSensor(entry, api, coordinator),
            AquafeastWaterPressureSensor(entry, api, coordinator),
            AquafeastTotalWaterSensor(entry, api, coordinator),
            AquafeastBatteryLevelSensor(entry, api, coordinator),
            AquafeastPowerSupplyStatusSensor(entry, api, coordinator),
            AquafeastLastModeSensor(entry, api, coordinator),
            AquafeastAiAdaptiveSensor(entry, api, coordinator),
            AquafeastFaultStatusSensor(entry, api, coordinator),
            AquafeastFaultCodeSensor(entry, api, coordinator),
            AquafeastRawStatusSensor(entry, api, coordinator),
        ]
    )


class AquafeastBaseSensor(CoordinatorEntity, SensorEntity):
    """Base Aquafeast sensor."""

    _attr_has_entity_name = True

    def __init__(self, entry, api, coordinator) -> None:
        """Initialize the base sensor."""
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
        """Return coordinator data payload."""
        return self.coordinator.data.get("data", {})


class AquafeastMeasurementSystemSensor(AquafeastBaseSensor):
    """Measurement system sensor."""

    _attr_name = "measurement system"
    _attr_icon = "mdi:ruler"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_measurement_system"

    @property
    def native_value(self) -> str:
        """Return measurement system."""
        return "Imperial" if _is_imperial(self._data) else "Metric"


class AquafeastProtectionStateSensor(AquafeastBaseSensor):
    """Protection state sensor."""

    _attr_name = "protection state"
    _attr_icon = "mdi:shield-check"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_protection_state"

    @property
    def native_value(self) -> str:
        """Return protection state."""
        code = _parse_mode(self._data.get("data02"))

        if code is None:
            return "Unknown"

        if code in (1, 2, 3, 4, 5, 6):
            return "UnProtected"

        if code in (17, 18, 19, 20, 21, 22):
            return "Protected"

        return "Unknown"


class AquafeastWaterTemperatureSensor(AquafeastBaseSensor):
    """Water temperature sensor."""

    _attr_name = "water temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_temperature"

    @property
    def native_unit_of_measurement(self):
        """Return temperature unit."""
        return (
            UnitOfTemperature.FAHRENHEIT
            if _is_imperial(self._data)
            else UnitOfTemperature.CELSIUS
        )

    @property
    def native_value(self):
        """Return water temperature."""
        raw_value = self._data.get("data04")
        return _parse_temperature_raw(raw_value)


class AquafeastWaterFlowRateSensor(AquafeastBaseSensor):
    """Water flow rate sensor."""

    _attr_name = "water flow rate"
    _attr_icon = "mdi:waves-arrow-right"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_flow_rate"

    @property
    def native_unit_of_measurement(self):
        """Return flow unit."""
        return "GPM" if _is_imperial(self._data) else "L/hr"

    @property
    def native_value(self):
        """Return water flow rate."""
        raw_value = self._data.get("data0B")
        value = _parse_optional_number(raw_value)
        if value is None:
            return None

        if _is_imperial(self._data):
            return round(value / 227.1247, 2)

        return round(value / 10, 1)


class AquafeastWaterPressureSensor(AquafeastBaseSensor):
    """Water pressure sensor."""

    _attr_name = "water pressure"
    _attr_icon = "mdi:gauge"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_water_pressure"

    @property
    def native_unit_of_measurement(self):
        """Return pressure unit."""
        return "psi" if _is_imperial(self._data) else "MPa"

    @property
    def native_value(self):
        """Return water pressure."""
        raw_value = self._data.get("data06")
        value = _parse_optional_number(raw_value)
        if value is None:
            return None

        if _is_imperial(self._data):
            return round((value / 100) * 145.0377, 1)

        return round(value / 100, 2)


class AquafeastTotalWaterSensor(AquafeastBaseSensor):
    """Total water sensor."""

    _attr_name = "total water"
    _attr_icon = "mdi:water"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_total_water"

    @property
    def native_unit_of_measurement(self):
        """Return total water unit."""
        return "gal" if _is_imperial(self._data) else "m³"

    @property
    def native_value(self):
        """Return total water."""
        low_raw = self._data.get("data10")
        high_raw = self._data.get("data11")

        low = _parse_optional_number(low_raw)
        high = _parse_optional_number(high_raw)

        if low is None and high is None:
            return None

        low = int(low or 0)
        high = int(high or 0)

        metric_value = high * 100 + (low / 100)

        if _is_imperial(self._data):
            return round(metric_value * 264.172, 1)

        return round(metric_value, 2)


class AquafeastBatteryLevelSensor(AquafeastBaseSensor):
    """Battery level sensor."""

    _attr_name = "battery level"
    _attr_icon = "mdi:battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_battery_level"

    @property
    def native_value(self) -> str:
        """Return battery level."""
        raw_value = self._data.get("data1C")

        mapping = {
            "0": "Critical",
            "1": "Low",
            "2": "Medium",
            "3": "High",
            "4": "Full",
        }

        return mapping.get(str(raw_value), "Unknown")


class AquafeastPowerSupplyStatusSensor(AquafeastBaseSensor):
    """Power supply status sensor."""

    _attr_name = "power supply status"
    _attr_icon = "mdi:power-plug-battery"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_power_supply_status"

    @property
    def native_value(self) -> str:
        """Return power supply status."""
        raw_value = self._data.get("data1D")

        mapping = {
            "0": "Battery only",
            "1": "Charging",
            "2": "External power / full",
        }

        return mapping.get(str(raw_value), "Unknown")


class AquafeastLastModeSensor(AquafeastBaseSensor):
    """Last mode sensor."""

    _attr_name = "last mode"
    _attr_icon = "mdi:history"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_last_mode"

    @property
    def native_value(self) -> str:
        """Return previous mode."""
        code = _parse_mode(self._data.get("data16"))
        return _mode_name(code) or "Unknown"


class AquafeastAiAdaptiveSensor(AquafeastBaseSensor):
    """AI adaptive status sensor."""

    _attr_name = "AI adaptive"
    _attr_icon = "mdi:brain"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ai_adaptive"

    @property
    def native_value(self) -> str:
        """Return AI adaptive status."""
        raw_value = self._data.get("data28")

        mapping = {
            "0": "Off",
            "1": "On",
        }

        return mapping.get(str(raw_value), "Unknown")


class AquafeastFaultStatusSensor(AquafeastBaseSensor):
    """Fault status sensor."""

    _attr_name = "fault status"
    _attr_icon = "mdi:alert-circle-outline"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fault_status"

    @property
    def native_value(self) -> str:
        """Return fault description."""
        return _fault_description(self._data.get("dataF0"))


class AquafeastFaultCodeSensor(AquafeastBaseSensor):
    """Fault code sensor."""

    _attr_name = "fault code"
    _attr_icon = "mdi:numeric"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_fault_code"

    @property
    def native_value(self) -> str:
        """Return raw fault code."""
        raw_value = self._data.get("dataF0")
        return str(raw_value) if raw_value is not None else "Unknown"


class AquafeastRawStatusSensor(AquafeastBaseSensor):
    """Raw status sensor."""

    _attr_name = "raw status"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:code-json"

    def __init__(self, entry, api, coordinator) -> None:
        super().__init__(entry, api, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_raw_status"

    @property
    def native_value(self) -> str:
        """Return raw JSON payload."""
        return json.dumps(self.coordinator.data, ensure_ascii=False, sort_keys=True)
