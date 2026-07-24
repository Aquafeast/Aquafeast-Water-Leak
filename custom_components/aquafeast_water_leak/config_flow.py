"""Config flow for Aquafeast Water Leak."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DEVICE_TYPE,
    CONF_MAC,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEVICE_TYPE_FILTER,
    DEVICE_TYPE_LEAKAGE_PROTECTOR,
    DOMAIN,
)

DEVICE_TYPE_TITLES = {
    DEVICE_TYPE_LEAKAGE_PROTECTOR: "Leakage protector",
    DEVICE_TYPE_FILTER: "Leakage protector + pre-filter",
}

DEVICE_TYPE_SELECTOR = SelectSelector(
    SelectSelectorConfig(
        options=[
            SelectOptionDict(
                value=DEVICE_TYPE_LEAKAGE_PROTECTOR,
                label="Leakage protector",
            ),
            SelectOptionDict(
                value=DEVICE_TYPE_FILTER,
                label="Leakage protector + pre-filter",
            ),
        ],
        mode=SelectSelectorMode.DROPDOWN,
    )
)


class AquafeastWaterLeakConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Aquafeast Water Leak."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            mac = user_input[CONF_MAC].replace(":", "").replace("-", "").lower()

            await self.async_set_unique_id(mac)
            self._abort_if_unique_id_configured()

            device_type = user_input[CONF_DEVICE_TYPE]
            title = f"{DEVICE_TYPE_TITLES[device_type]} {user_input[CONF_MAC]}"

            return self.async_create_entry(
                title=title,
                data=user_input,
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_MAC): str,
                vol.Required(
                    CONF_DEVICE_TYPE,
                    default=DEVICE_TYPE_LEAKAGE_PROTECTOR,
                ): DEVICE_TYPE_SELECTOR,
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
