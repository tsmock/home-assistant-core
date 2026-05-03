"""Config flow for the Xcel Energy integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from .const import CONF_CERTIFICATE, CONF_KEY, DOMAIN
from .exceptions import CannotConnect, InvalidAuth
from .sensor.itron_riva_gen5 import ITRON_CERT, ItronApi, ItronRivaGen5Consumption

_LOGGER = logging.getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    cv.url_no_path(data[CONF_HOST]) # For whatever reason, I can't do this in vol.Schema above. I'm probably misunderstanding something.
    vol.Any(vol.PathExists(data[CONF_CERTIFICATE]), vol.All(vol.Contains("-----BEGIN CERTIFICATE-----", data[CONF_CERTIFICATE]), vol.Contains("-----END CERTIFICATE-----", data[CONF_CERTIFICATE])))
    vol.Any(vol.PathExists(data[CONF_KEY]), vol.All(vol.Contains("-----BEGIN PRIVATE KEY-----", data[CONF_KEY]), vol.Contains("-----END PRIVATE KEY-----", data[CONF_KEY])))
    cv.string_with_no_html(data[CONF_KEY])
    cv.string_with_no_html(data[CONF_CERTIFICATE])
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
    return {"title": "Itron Riva Gen 5", "data": {CONF_HOST: data[CONF_HOST], CONF_CERTIFICATE: data[CONF_CERTIFICATE], CONF_KEY: data[CONF_KEY]}}


class XcelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Xcel Energy."""

    VERSION = 1

    def __init__(self):
        self.ip_address: str | None = None

    async def async_step_dhcp(
        self, discovery_info: DhcpServiceInfo
    ) -> ConfigFlowResult:
        # TODO: Filter out devices that aren't listening on 8081?
        _LOGGER.warning(f"DHCP discovery: {discovery_info.macaddress}")
        await self.async_set_unique_id(discovery_info.macaddress)
        self._abort_if_unique_id_configured(updates={CONF_HOST: discovery_info.ip})
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if not entry.unique_id and entry.data[CONF_HOST] == discovery_info.ip:
                self.hass.config_entries.async_update_entry(entry, unique_id=discovery_info.macaddress)
            return self.async_abort(reason="already_configured")
        self.ip_address = discovery_info.ip
        return await self.async_step_confirm_discovery()

    async def async_step_confirm_discovery(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        user_input = user_input or {}
        userDataSchema = vol.Schema(
            {
                vol.Required(
                    CONF_CERTIFICATE,
                    description="PEM certificate for communicating with xcel meter",
                    default=user_input.get(CONF_CERTIFICATE, None),
                ): cv.string,  # I'd prefer cv.string_with_no_html, but that doesn't seem to work.
                vol.Required(
                    CONF_KEY, description="Key for communicating with xcel meter",
                    default=user_input.get(CONF_KEY, None),
                ): cv.string,  # I'd prefer cv.string_with_no_html, but that doesn't seem to work.
            }
        )
        return self.async_show_form(
            step_id="confirm_discovery",
            data_schema=userDataSchema,
        )
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        _LOGGER.error(f"user_input: {user_input}")
        if user_input is not None:
            self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.exception("Unexpected exception", exc_info=e)
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        user_input = user_input or {}
        userDataSchema = vol.Schema(
            {
                vol.Required(CONF_HOST, default=user_input.get(CONF_HOST, self.ip_address)): cv.string,  # really cv.url_no_path, but it doesn't seem to work
                vol.Required(
                    CONF_CERTIFICATE,
                    description="PEM certificate for communicating with xcel meter",
                    default=user_input.get(CONF_CERTIFICATE, None),
                ): cv.string,  # I'd prefer cv.string_with_no_html, but that doesn't seem to work.
                vol.Required(
                    CONF_KEY, description="Key for communicating with xcel meter",
                    default=user_input.get(CONF_KEY, None),
                ): cv.string,  # I'd prefer cv.string_with_no_html, but that doesn't seem to work.
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=userDataSchema, errors=errors
        )
