"""Data coordinator for Aquafeast Water Leak."""

from __future__ import annotations

from datetime import timedelta
import asyncio
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
        self.reset_armed = False
        self._reset_arm_task: asyncio.Task | None = None

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

    async def async_set_reset_armed(self, armed: bool, timeout: int = 15) -> None:
        """Enable or disable reset arm state."""
        self.reset_armed = armed

        if self._reset_arm_task:
            self._reset_arm_task.cancel()
            self._reset_arm_task = None

        if armed:
            self._reset_arm_task = self.hass.async_create_task(
                self._async_auto_disarm_reset(timeout)
            )

        self.async_update_listeners()

    async def _async_auto_disarm_reset(self, timeout: int) -> None:
        """Auto-disarm reset after timeout."""
        try:
            await asyncio.sleep(timeout)
            self.reset_armed = False
            self._reset_arm_task = None
            self.async_update_listeners()
        except asyncio.CancelledError:
            pass

    async def async_consume_reset_arm(self) -> bool:
        """Consume armed reset state."""
        if not self.reset_armed:
            return False

        await self.async_set_reset_armed(False)
        return True

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
