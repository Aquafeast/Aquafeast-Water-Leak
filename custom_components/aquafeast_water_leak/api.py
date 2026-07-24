"""API client for Aquafeast Water Leak."""

from __future__ import annotations

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONTROL_URL, GET_STATE_URL, SET_HOUR_URL, SET_MODE_URL


class AquafeastApi:
    """Simple API client."""

    def __init__(self, hass, mac_address: str, device_model: str) -> None:
        self.hass = hass
        self.mac_address = mac_address.strip().replace(":", "").replace("-", "").upper()
        self.device_model = device_model

    async def async_get_state(self) -> dict:
        """Get current device state."""
        params = {
            "device": self.mac_address,
            "deviceModel": self.device_model,
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(GET_STATE_URL, params=params, timeout=timeout) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def async_send_command(self, key: str, value: str):
        """Send generic command to device."""
        params = {
            "strMac": self.mac_address,
            "key": key,
            "value": value,
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(CONTROL_URL, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}

    async def async_set_valve(self, open_valve: bool):
        """Set valve state."""
        return await self.async_send_command("01", "1" if open_valve else "0")

    async def async_set_warning_minimum_flow(self, flow_lph: float):
        """Set warning minimum flow in L/hr."""
        value = int(round(flow_lph * 10))
        return await self.async_send_command("22", str(value))

    async def async_set_flush_period(self, days: int):
        """Set flush period in days."""
        return await self.async_send_command("17", str(days))

    async def async_set_flush_duration(self, seconds: int):
        """Set flush duration in seconds."""
        return await self.async_send_command("18", str(seconds))

    async def async_manual_flush(self):
        """Run immediate flush."""
        return await self.async_send_command("1A", "1")

    async def async_set_mode(
        self, mode: int, flow_set: int = 0, hour_set: float | None = None
    ):
        """Set operation mode."""
        params = {
            "strMac": self.mac_address,
            "mode": str(mode),
            "flowSet": str(flow_set),
        }

        if hour_set is not None:
            params["hourSet"] = str(hour_set)

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(SET_MODE_URL, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}

    async def async_set_clock(self, hour: int, minute: int, second: int):
        """Set device clock."""
        params = {
            "strMac": self.mac_address,
            "hour": str(hour),
            "minute": str(minute),
            "second": str(second),
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(SET_HOUR_URL, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}
