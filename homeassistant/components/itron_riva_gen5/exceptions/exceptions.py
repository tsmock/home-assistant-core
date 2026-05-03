"""Common exceptions for the itron_riva_gen5 integration."""

from homeassistant.exceptions import HomeAssistantError


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
