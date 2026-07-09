"""Data coordinator for Aquafeast Water Leak."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import AquafeastApi
from .const import (
    CONF_DEVICE_MODEL,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class AquafeastDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching Aquafeast data."""

    def __init__(self, hass: HomeAssistant, entry_data: dict) -> None:
        """Initialize the coordinator."""
        self.api = AquafeastApi(
            hass,
            entry_data[CONF_MAC],
            entry_data[CONF_DEVICE_MODEL],
        )

        scan_interval = entry_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            data = await self.api.async_get_state()

            if data.get("resCode") not in (None, "0", 0):
                raise UpdateFailed(f"API error: {data.get('resMsg')}")

            return data

        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
