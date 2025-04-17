"""Config flow for the Xcel Energy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_CERTIFICATE, CONF_KEY, DOMAIN
from .exceptions import CannotConnect, InvalidAuth
from .itron_riva_gen5 import ITRON_CERT, ItronApi, ItronRivaGen5Consumption

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(
            CONF_CERTIFICATE,
            description="PEM certificate for communicating with xcel meter",
        ): str,
        vol.Required(
            CONF_KEY, description="Key for communicating with xcel meter"
        ): str,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data[CONF_USERNAME], data[CONF_PASSWORD]
    # )

    api: ItronApi = ItronApi(
        hass=hass,
        host=data[CONF_HOST],
        certificate=data[CONF_CERTIFICATE],
        key=data[CONF_KEY],
        cadata=ITRON_CERT,
    )
    await api.wait_for_session()
    consumption = ItronRivaGen5Consumption(api)

    # consumption will almost never be 0. AFAIK, it is an always incrementing number.
    consumption.async_update()
    if not consumption.native_value:
        raise InvalidAuth

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"title": "Xcel Energy"}


class XcelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xcel Energy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        _LOGGER.error(user_input)
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
