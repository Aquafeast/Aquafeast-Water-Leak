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
        raw_value = self._data.get("data02")

        if raw_value is None:
            return "Unknown"

        try:
            code = int(raw_value)
        except (TypeError, ValueError):
            return "Unknown"

        if code == 2:
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
        raw_value = self._data.get("data1C")
        return _parse_optional_number(raw_value)


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
        raw_value = self._data.get("data1A")
        return _parse_optional_number(raw_value)


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
        raw_value = self._data.get("data1D")
        return _parse_optional_number(raw_value)


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
