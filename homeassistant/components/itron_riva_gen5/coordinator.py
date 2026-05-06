import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from . import ItronApi, ItronRivaGen5Power
from .sensor import ItronRivaGen5Consumption, ItronRivaGen5Production

logger = logging.getLogger(__name__)
# The power reading only has the last second, but HA doesn't allow for <5s/update
SCAN_INTERVAL = timedelta(seconds=5)

class IEEE2030_5_Coordinator(DataUpdateCoordinator[None]):
    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, api: ItronApi) -> None:
        super().__init__(
            hass,
            logger,
            name="IEEE 2030.5 Coordinator",
            config_entry=config_entry,
            update_interval=SCAN_INTERVAL,
            always_update=True
        )
        self.config_entry = config_entry
        self.api = api
        self.consumption = ItronRivaGen5Consumption(coordinator=self, context=None, api=self.api)
        self.production = ItronRivaGen5Production(coordinator=self, context=None, api=self.api)
        self.power = ItronRivaGen5Power(coordinator=self, context=None, api=self.api)

    async def _async_setup(self):
        await self.api.wait_for_session()

    async def _async_update_data(self) -> None:
        for device in [self.consumption, self.production, self.power]:
            await device.async_update()