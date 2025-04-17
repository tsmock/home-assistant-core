"""The Xcel Energy integration."""

from __future__ import annotations

import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CERTIFICATE, CONF_KEY
from .itron_riva_gen5 import ITRON_CERT, ItronApi, ItronRivaGen5Power

# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]

type XcelConfigEntry = ConfigEntry[MyApi]  # noqa: F821


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: XcelConfigEntry) -> bool:
    """Set up Xcel Energy from a config entry."""

    # TODO 1. Create API instance
    # TODO 2. Validate the API connection (and authentication)
    # TODO 3. Store an API object for your platforms to access
    # entry.runtime_data = MyAPI(...)

    host: str = entry.data[CONF_HOST]
    client_key: str = entry.data[CONF_KEY]
    client_cert: str = entry.data[CONF_CERTIFICATE]
    api: ItronApi = ItronApi(
        host=host, key=client_key, certificate=client_cert, cadata=ITRON_CERT
    )
    await api.wait_for_session()
    power: ItronRivaGen5Power = ItronRivaGen5Power(api)

    if await hass.async_add_executor_job(power.async_update):
        raise ConfigEntryNotReady
    entry.runtime_data = power

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: XcelConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
