"""Data coordinator for Aquafeast Water Leak."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AquafeastApi
from .const import (
    CAP_AI_ADAPTIVE,
    CAP_FILTER,
    CONF_DEVICE_MODEL,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    KEY_AI_ADAPTIVE,
    KEY_DATA,
    KEY_DEVICE_MODEL,
    KEY_FLUSH_DURATION,
    KEY_FLUSH_PERIOD,
    KEY_FLUSH_STATUS,
    KEY_NEXT_FLUSH_HOURS,
    MODEL_LEAK_PROTECTOR_FILTER,
)

_LOGGER = logging.getLogger(__name__)


class AquafeastDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to manage fetching Aquafeast data."""

    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        """Initialize the coordinator."""
        self.entry_data = entry_data
        self.api = AquafeastApi(
            hass,
            entry_data[CONF_MAC],
            entry_data[CONF_DEVICE_MODEL],
        )
        self.model_code: int | None = None
        self.capabilities: set[str] = set()

        scan_interval = entry_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _state_payload(self, payload: dict | None = None) -> dict[str, Any]:
        """Return the nested data payload."""
        source = payload if payload is not None else self.data
        if not isinstance(source, dict):
            return {}

        nested = source.get(KEY_DATA, {})
        if isinstance(nested, dict):
            return nested

        return {}

    @staticmethod
    def _as_int(value: Any) -> int | None:
        """Convert raw API value to int when possible."""
        if value in (None, "", "-"):
            return None
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get raw value from nested device data."""
        return self._state_payload().get(key, default)

    def get_int(self, key: str) -> int | None:
        """Get integer value from nested device data."""
        return self._as_int(self.get_value(key))

    def get_scaled(self, key: str, divisor: float) -> float | None:
        """Get scaled numeric value."""
        raw = self.get_int(key)
        if raw is None:
            return None
        return raw / divisor

    def detect_model_code(self, payload: dict | None = None) -> int | None:
        """Detect device model code."""
        data = self._state_payload(payload)
        model = self._as_int(data.get(KEY_DEVICE_MODEL))
        if model is not None:
            return model

        filter_keys = (
            KEY_FLUSH_PERIOD,
            KEY_FLUSH_DURATION,
            KEY_NEXT_FLUSH_HOURS,
            KEY_FLUSH_STATUS,
        )
        if any(data.get(key) not in (None, "", "-") for key in filter_keys):
            return MODEL_LEAK_PROTECTOR_FILTER

        return None

    def detect_capabilities(self, payload: dict | None = None) -> set[str]:
        """Detect supported capabilities from payload."""
        data = self._state_payload(payload)
        caps: set[str] = set()

        model = self.detect_model_code(payload)
        if model == MODEL_LEAK_PROTECTOR_FILTER:
            caps.add(CAP_FILTER)

        filter_keys = (
            KEY_FLUSH_PERIOD,
            KEY_FLUSH_DURATION,
            KEY_NEXT_FLUSH_HOURS,
            KEY_FLUSH_STATUS,
        )
        if any(data.get(key) not in (None, "", "-") for key in filter_keys):
            caps.add(CAP_FILTER)

        if data.get(KEY_AI_ADAPTIVE) not in (None, "", "-"):
            caps.add(CAP_AI_ADAPTIVE)

        return caps

    def has_capability(self, capability: str) -> bool:
        """Return True if device supports capability."""
        return capability in self.capabilities

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            data = await self.api.async_get_state()

            if data.get("resCode") not in (None, "0", 0):
                raise UpdateFailed(f"API error: {data.get('resMsg')}")

            self.model_code = self.detect_model_code(data)
            self.capabilities = self.detect_capabilities(data)

            return data

        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
