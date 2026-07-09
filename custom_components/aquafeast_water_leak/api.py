"""API client for Aquafeast Water Leak."""

from __future__ import annotations

import aiohttp

from homeassistant.helpers.aiohttp_client import async_get_clientsession


class AquafeastApi:
    """Simple API client."""

    def __init__(self, hass, mac_address: str, device_model: str) -> None:
        self.hass = hass
        self.mac_address = (
            mac_address.strip().replace(":", "").replace("-", "").upper()
        )
        self.device_model = device_model

    async def async_get_state(self) -> dict:
        """Get current device state."""
        url = "https://interface.briskworld.com/devSta/getState/app"
        params = {
            "device": self.mac_address,
            "deviceModel": self.device_model,
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            return await response.json(content_type=None)

    async def async_send_command(self, key: str, value: str):
        """Send generic command to device."""
        url = "https://interface.briskworld.com/device/control/app"
        params = {
            "strMac": self.mac_address,
            "key": key,
            "value": value,
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}

    async def async_set_warning_minimum_flow(self, flow_lph: float):
        """Set warning minimum flow in L/hr."""
        value = int(round(flow_lph * 10))
        return await self.async_send_command("22", str(value))

    async def async_set_mode(self, mode: int, flow_set: int = 0, hour_set: float | None = None):
        """Set operation mode."""
        url = "https://interface.briskworld.com/device/setMode/app"
        params = {
            "strMac": self.mac_address,
            "mode": str(mode),
            "flowSet": str(flow_set),
        }

        if hour_set is not None:
            params["hourSet"] = str(hour_set)

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}


    async def async_set_clock(self, hour: int, minute: int, second: int):
        """Set device clock."""
        url = "https://interface.briskworld.com/device/setHour/app"
        params = {
            "strMac": self.mac_address,
            "hour": str(hour),
            "minute": str(minute),
            "second": str(second),
        }

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=15)

        async with session.get(url, params=params, timeout=timeout) as response:
            response.raise_for_status()
            text = await response.text()
            try:
                return await response.json(content_type=None)
            except Exception:
                return {"raw": text}
