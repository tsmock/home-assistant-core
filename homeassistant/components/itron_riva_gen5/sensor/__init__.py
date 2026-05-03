"""The sensor package for itron_riva_gen5 providing sensors for the Itron Riva Gen 5 power meters."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from .. import CONF_KEY, CONF_CERTIFICATE
from .certs import ITRON_CERT
from .itron_riva_gen5 import (
    ItronApi,
    ItronRivaGen5,
    ItronRivaGen5Consumption,
    ItronRivaGen5Power,
    ItronRivaGen5Production,
)

__all__ = [
    "ITRON_CERT",
    "ItronApi",
    "ItronRivaGen5",
    "ItronRivaGen5Consumption",
    "ItronRivaGen5Power",
    "ItronRivaGen5Production",
]

LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddConfigEntryEntitiesCallback) -> None:
    """Set up Xcel Energy from a config entry."""

    api: ItronApi = entry.runtime_data
    consumption = ItronRivaGen5Consumption(api)
    power: ItronRivaGen5Power = ItronRivaGen5Power(api)
    production = ItronRivaGen5Production(api)

    async_add_entities([consumption, power, production])
