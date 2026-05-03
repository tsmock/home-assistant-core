"""The sensor package for itron_riva_gen5 providing sensors for the Itron Riva Gen 5 power meters."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from itron_riva_gen5 import CONF_CERTIFICATE, CONF_KEY
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

async def async_setup_entry(hass: HomeAssistant, data: ConfigEntry) -> bool:
    api: ItronApi = ItronApi(
        hass=hass,
        host=data[CONF_HOST],
        certificate=data[CONF_CERTIFICATE],
        key=data[CONF_KEY],
        cadata=ITRON_CERT,
    )
    await api.wait_for_session()
    consumption = ItronRivaGen5Consumption(api)
    power = ItronRivaGen5Power(api)
    production = ItronRivaGen5Production(api)
