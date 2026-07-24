"""Config flow for Aquafeast Water Leak."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import (
    CONF_DEVICE_MODEL,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_DEVICE_MODEL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FILTER_DEVICE_MODEL,
)

DEVICE_MODEL_OPTIONS = {
    DEFAULT_DEVICE_MODEL: "Leakage protector",
    FILTER_DEVICE_MODEL: "Leakage protector + pre-filter",
}


class AquafeastWaterLeakConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquafeast Water Leak."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(
                user_input[CONF_MAC].replace(":", "").replace("-", "").lower()
            )
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Aquafeast {user_input[CONF_MAC]}",
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MAC): str,
                vol.Optional(
                    CONF_DEVICE_MODEL,
                    default=DEFAULT_DEVICE_MODEL,
                ): vol.In(list(DEVICE_MODEL_OPTIONS.keys())),
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=DEFAULT_SCAN_INTERVAL,
                ): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
