"""The Xcel Energy integration."""

from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import CONF_CERTIFICATE, CONF_KEY
from .sensor.itron_riva_gen5 import ITRON_CERT, ItronApi, ItronRivaGen5Power
from .coordinator import IEEE2030_5_Coordinator

_LOGGER = logging.getLogger(__name__)
# For your initial PR, limit it to 1 platform.
_PLATFORMS: list[Platform] = [Platform.SENSOR]

type XcelConfigEntry = ConfigEntry[ItronApi]


# TODO Update entry annotation
async def async_setup_entry(hass: HomeAssistant, entry: XcelConfigEntry) -> bool:
    """Set up Xcel Energy from a config entry."""

    # 1. Create API instance
    host: str = entry.data[CONF_HOST]
    client_key: str = entry.data[CONF_KEY]
    client_cert: str = entry.data[CONF_CERTIFICATE]
    api: ItronApi = ItronApi(
        hass=hass, host=host, key=client_key, certificate=client_cert, cadata=ITRON_CERT
    )
    await api.wait_for_session()

    # 2. Validate the API connection (and authentication)
    result: str = api.fetch("/upt/1/mr/1/r")
    _LOGGER.info("Power is currently: %s", result)

    # 3. Store an API object for your platforms to access
    entry.runtime_data = IEEE2030_5_Coordinator(hass=hass, config_entry=entry, api=api)

    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)

    return True


# TODO Update entry annotation
async def async_unload_entry(hass: HomeAssistant, entry: XcelConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, _PLATFORMS)
