"""Data coordinator for Aquafeast Water Leak."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AquafeastApi
from .const import (
    API_DEVICE_MODEL,
    CAP_FILTER,
    CONF_DEVICE_TYPE,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_FILTER,
    DOMAIN,
    KEY_DATA,
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
            API_DEVICE_MODEL,
        )
        self.capabilities: set[str] = self._detect_capabilities()

        scan_interval = entry_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    def _detect_capabilities(self) -> set[str]:
        """Detect capabilities from configured device type only."""
        caps: set[str] = set()

        if self.entry_data.get(CONF_DEVICE_TYPE) == DEVICE_TYPE_FILTER:
            caps.add(CAP_FILTER)

        return caps

    def _state_payload(self, payload: dict | None = None) -> dict[str, Any]:
        """Return nested device payload."""
        source = payload if payload is not None else self.data
        if not isinstance(source, dict):
            return {}

        nested = source.get(KEY_DATA, {})
        if isinstance(nested, dict):
            return nested

        return {}

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get raw value from nested payload."""
        return self._state_payload().get(key, default)

    def get_int(self, key: str) -> int | None:
        """Get integer value from nested payload."""
        value = self.get_value(key)
        if value in (None, "", "-", "--"):
            return None
        try:
            return int(str(value))
        except (TypeError, ValueError):
            return None

    def get_scaled(self, key: str, divisor: float) -> float | None:
        """Get scaled numeric value."""
        raw = self.get_int(key)
        if raw is None:
            return None
        return raw / divisor

    def has_capability(self, capability: str) -> bool:
        """Return True if device supports a capability."""
        return capability in self.capabilities

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            data = await self.api.async_get_state()

            if data.get("resCode") not in (None, "0", 0):
                raise UpdateFailed(f"API error: {data.get('resMsg')}")

            self.capabilities = self._detect_capabilities()
            return data

        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
