"""Integrate the Itron sensors into Home Assistant."""

from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import CONF_CERTIFICATE, CONF_KEY
from .sensor import (
    ITRON_CERT,
    ItronApi,
    ItronRivaGen5Consumption,
    ItronRivaGen5Power,
    ItronRivaGen5Production,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    host: str = config[CONF_HOST]
    client_key: str = config[CONF_KEY]
    client_cert: str = config[CONF_CERTIFICATE]
    api: ItronApi = ItronApi(
        hass=hass, host=host, key=client_key, certificate=client_cert, cadata=ITRON_CERT
    )
    power: ItronRivaGen5Power = ItronRivaGen5Power(api)
    consumption: ItronRivaGen5Consumption = ItronRivaGen5Consumption(api)
    production: ItronRivaGen5Production = ItronRivaGen5Production(api)

    async_add_entities([power, consumption, production], False)
